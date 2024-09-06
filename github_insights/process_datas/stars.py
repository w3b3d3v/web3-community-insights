import requests
import pandas as pd
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = 'https://api.github.com/graphql'

headers = {
    'Authorization': f'bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}

db_path = os.getenv('DB_PATH', 'github_insights/process_datas/github_data.db')

def fetch_data(query):
    """Função para buscar dados da API do GitHub."""
    response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"HTTP error occurred: {response.status_code} - {response.text}")

def process_data(data):
    if not data or 'data' not in data or not data['data']:
        raise ValueError("Unexpected data structure: {}".format(data))
    
    organization_data = data['data'].get('organization', {})
    if not organization_data:
        raise ValueError("Organization data not found in the response: {}".format(data))
    
    user_activity = {}
    repositories = organization_data.get('repositories', {}).get('nodes', [])

    for repo in repositories:
        stargazers = repo.get('stargazers', {}).get('nodes', [])

        for user in stargazers:
            user_login = user.get('login', 'Unknown')
            if user_login in user_activity:
                user_activity[user_login] += 1
            else:
                user_activity[user_login] = 1
    
    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'repositories_stared_count'])
    df_users_stars = df_users.sort_values(by='repositories_stared_count', ascending=False)

    return df_users_stars

def get_users_with_pagination():
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) {
          nodes {
            stargazers(first: 100) {
              nodes {
                login
              }
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """
    
    user_activity = {}
    has_next_page = True
    end_cursor = None

    while has_next_page:
        paginated_query = query
        if end_cursor:
            paginated_query = paginated_query.replace('repositories(first: 100)', f'repositories(first: 100, after: "{end_cursor}")')
        
        data = fetch_data(paginated_query)
        organization_data = data['data'].get('organization', {})
        repositories = organization_data.get('repositories', {}).get('nodes', [])
        page_info = organization_data.get('repositories', {}).get('pageInfo', {})
        
        has_next_page = page_info.get('hasNextPage', False)
        end_cursor = page_info.get('endCursor', None)

        for repo in repositories:
            stargazers = repo.get('stargazers', {}).get('nodes', [])

            for user in stargazers:
                user_login = user.get('login', 'Unknown')
                if user_login in user_activity:
                    user_activity[user_login] += 1
                else:
                    user_activity[user_login] = 1

    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'repositories_stared_count'])
    df_users_stars = df_users.sort_values(by='repositories_stared_count', ascending=False)

    return df_users_stars

def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Stars_from_user (
        user TEXT PRIMARY KEY,
        repositories_stared_count INTEGER
    )
    ''')

    conn.close()

def store_data(df_users_stars):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with conn:
        for _, row in df_users_stars.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Stars_from_user (user, repositories_stared_count)
            VALUES (?, ?)
            ''', (row['user'], row['repositories_stared_count']))

    conn.close()

def main():
    df_users_stars = get_users_with_pagination()

    create_tables()

    store_data(df_users_stars)

    pd.set_option('display.max_rows', None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Stars_from_user')
    users = cursor.fetchall()

    conn.close()

if __name__ == "__main__":
    main()
