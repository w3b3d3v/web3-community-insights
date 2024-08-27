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
    """Função para processar os dados obtidos da API."""
    if not data or 'data' not in data or not data['data']:
        raise ValueError("Unexpected data structure: {}".format(data))
    
    organization_data = data['data'].get('organization', {})
    if not organization_data:
        raise ValueError("Organization data not found in the response: {}".format(data))
    
    repositories = organization_data.get('repositories', {}).get('nodes', [])

    repo_data = []
    user_activity = {}

    for repo in repositories:
        repo_name = repo.get('name', 'Unknown')
        stars_count = repo.get('stargazerCount', 0)
        stargazers = repo.get('stargazers', {}).get('nodes', [])

        repo_data.append({
            'repo_name': repo_name,
            'stars_count': stars_count
        })

        for user in stargazers:
            user_login = user.get('login', 'Unknown')
            if user_login in user_activity:
                user_activity[user_login] += 1
            else:
                user_activity[user_login] = 1

    df_repos = pd.DataFrame(repo_data)
    df_repo_stars = df_repos.sort_values(by='stars_count', ascending=False)
    
    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'repositories_stared_count'])
    df_users_stars = df_users.sort_values(by='repositories_stared_count', ascending=False)

    return df_repo_stars, df_users_stars

def get_repositories_with_pagination():
    """Função para obter dados de repositórios com paginação e coleta de estrelas."""
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) {
          nodes {
            name
            stargazerCount
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
    
    all_repos = []
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
            repo_name = repo.get('name', 'Unknown')
            stars_count = repo.get('stargazerCount', 0)
            stargazers = repo.get('stargazers', {}).get('nodes', [])

            all_repos.append({
                'repo_name': repo_name,
                'stars_count': stars_count
            })

            for user in stargazers:
                user_login = user.get('login', 'Unknown')
                if user_login in user_activity:
                    user_activity[user_login] += 1
                else:
                    user_activity[user_login] = 1

    df_repos = pd.DataFrame(all_repos)
    df_repo_stars = df_repos.sort_values(by='stars_count', ascending=False)
    
    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'repositories_stared_count'])
    df_users_stars = df_users.sort_values(by='repositories_stared_count', ascending=False)

    return df_repo_stars, df_users_stars

def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Stars_from_repo (
        repo_name TEXT PRIMARY KEY,
        stars_count INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Stars_from_user (
        user TEXT PRIMARY KEY,
        repositories_stared_count INTEGER
    )
    ''')

    conn.close()

def store_data(df_repo_stars, df_users_stars):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with conn:
        for _, row in df_repo_stars.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Stars_from_repo (repo_name, stars_count)
            VALUES (?, ?)
            ''', (row['repo_name'], row['stars_count']))

        for _, row in df_users_stars.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Stars_from_user (user, repositories_stared_count)
            VALUES (?, ?)
            ''', (row['user'], row['repositories_stared_count']))

    conn.close()
    return store_data

def main():
    df_repo_stars, df_users_stars = get_repositories_with_pagination()

    create_tables()

    store_data(df_repo_stars, df_users_stars)

    pd.set_option('display.max_rows', None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Stars_from_repo')
    repos = cursor.fetchall()


    cursor.execute('SELECT * FROM Stars_from_user')
    users = cursor.fetchall()


    conn.close()

if __name__ == "__main__":
    main()
