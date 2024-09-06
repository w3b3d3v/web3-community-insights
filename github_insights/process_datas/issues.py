import requests
import pandas as pd
from dotenv import load_dotenv
import os
import time
import sqlite3

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = 'https://api.github.com/graphql'

headers = {
    'Authorization': f'bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}

db_path = os.getenv('DB_PATH', 'github_insights/process_datas/github_data.db')

def fetch_data(query, retries=3, delay=5):
    """Função para buscar dados da API do GitHub com repetição em caso de erro."""
    for attempt in range(retries):
        response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Attempt {attempt + 1} failed with status {response.status_code}. Retrying in {delay} seconds...")
            time.sleep(delay)
    
    raise Exception(f"HTTP error occurred: {response.status_code} - {response.text}")

def process_data(data):
    if not data or 'data' not in data or not data['data']:
        raise ValueError("Unexpected data structure: {}".format(data))
    
    organization_data = data['data'].get('organization', {})
    if not organization_data:
        raise ValueError("Organization data not found in the response: {}".format(data))
    
    repositories = organization_data.get('repositories', {}).get('nodes', [])
    user_issue_activity = {}

    for repo in repositories:
        issue_nodes = repo.get('issues', {}).get('nodes', [])

        for issue in issue_nodes:
            user = issue.get('author', {}).get('login', 'Unknown')
            if user in user_issue_activity:
                user_issue_activity[user] += 1
            else:
                user_issue_activity[user] = 1

    df_users = pd.DataFrame(user_issue_activity.items(), columns=['user', 'issues_count'])
    df_users_issues = df_users.sort_values(by='issues_count', ascending=False)

    return df_users_issues

def get_repositories_with_pagination():
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) {  
          nodes {
            name
            issues(first: 100) {
              totalCount
              nodes {
                author {
                  login
                }
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
    
    user_issue_activity = {}
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
            issue_nodes = repo.get('issues', {}).get('nodes', [])

            for issue in issue_nodes:
                user = issue.get('author', {}).get('login', 'Unknown')
                if user in user_issue_activity:
                    user_issue_activity[user] += 1
                else:
                    user_issue_activity[user] = 1

    df_users = pd.DataFrame(user_issue_activity.items(), columns=['user', 'issues_count'])
    df_users_issues = df_users.sort_values(by='issues_count', ascending=False)

    return df_users_issues

def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Issues_from_user (
        user TEXT PRIMARY KEY,
        issues_count INTEGER
    )
    ''')

    conn.close()

def store_data(df_users_issues):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with conn:
        for _, row in df_users_issues.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Issues_from_user (user, issues_count)
            VALUES (?, ?)
            ''', (row['user'], row['issues_count']))

    conn.close()

def main():
    df_users_issues = get_repositories_with_pagination()

    create_tables()

    store_data(df_users_issues)

    pd.set_option('display.max_rows', None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Issues_from_user')
    users = cursor.fetchall()

    conn.close()

if __name__ == "__main__":
    main()
