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
    """Função para processar os dados obtidos da API."""
    if not data or 'data' not in data or not data['data']:
        raise ValueError("Unexpected data structure: {}".format(data))
    
    organization_data = data['data'].get('organization', {})
    if not organization_data:
        raise ValueError("Organization data not found in the response: {}".format(data))
    
    repositories = organization_data.get('repositories', {}).get('nodes', [])

    repo_data = []
    user_fork_activity = {}

    for repo in repositories:
        repo_name = repo.get('name', 'Unknown')
        forks_count = repo.get('forks', {}).get('totalCount', 0)
        fork_nodes = repo.get('forks', {}).get('nodes', [])

        repo_data.append({
            'repo_name': repo_name,
            'forks_count': forks_count
        })

        for fork in fork_nodes:
            user = fork.get('owner', {}).get('login', 'Unknown')
            if user in user_fork_activity:
                user_fork_activity[user] += 1
            else:
                user_fork_activity[user] = 1

    df_repos = pd.DataFrame(repo_data)
    df_repo_forks = df_repos.sort_values(by='forks_count', ascending=False)
    
    df_users = pd.DataFrame(user_fork_activity.items(), columns=['user', 'forks_count'])
    df_users_forks = df_users.sort_values(by='forks_count', ascending=False)

    return df_repo_forks, df_users_forks

def get_repositories_with_pagination():
    """Função para obter dados de repositórios com paginação e coleta de forks."""
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) { 
          nodes {
            name
            forks(first: 100) {
              totalCount
              nodes {
                owner {
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
    
    all_repos = []
    user_fork_activity = {}
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
            forks_count = repo.get('forks', {}).get('totalCount', 0)
            fork_nodes = repo.get('forks', {}).get('nodes', [])

            all_repos.append({
                'repo_name': repo_name,
                'forks_count': forks_count
            })

            for fork in fork_nodes:
                user = fork.get('owner', {}).get('login', 'Unknown')
                if user in user_fork_activity:
                    user_fork_activity[user] += 1
                else:
                    user_fork_activity[user] = 1

    df_repos = pd.DataFrame(all_repos)
    df_repo_forks = df_repos.sort_values(by='forks_count', ascending=False)
    
    df_users = pd.DataFrame(user_fork_activity.items(), columns=['user', 'forks_count'])
    df_users_forks = df_users.sort_values(by='forks_count', ascending=False)

    return df_repo_forks, df_users_forks

def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Forks_from_repo (
        repo_name TEXT PRIMARY KEY,
        forks_count INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Forks_from_user (
        user TEXT PRIMARY KEY,
        forks_count INTEGER
    )
    ''')

    conn.close()

def store_data(df_repo_forks, df_users_forks):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with conn:
        for _, row in df_repo_forks.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Forks_from_repo (repo_name, forks_count)
            VALUES (?, ?)
            ''', (row['repo_name'], row['forks_count']))

        for _, row in df_users_forks.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Forks_from_user (user, forks_count)
            VALUES (?, ?)
            ''', (row['user'], row['forks_count']))

    conn.close()

def main():
    df_repo_forks, df_users_forks = get_repositories_with_pagination()

    create_tables()

    store_data(df_repo_forks, df_users_forks)

    pd.set_option('display.max_rows', None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Forks_from_repo')
    repos = cursor.fetchall()



    cursor.execute('SELECT * FROM Forks_from_user')
    users = cursor.fetchall()



    conn.close()

if __name__ == "__main__":
    main()
