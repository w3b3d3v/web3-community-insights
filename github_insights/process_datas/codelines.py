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

# Configuração do caminho do banco de dados SQLite
db_path = os.getenv('DB_PATH', 'github_insights/process_datas/github_data.db')

def fetch_data(query, variables=None):
    response = requests.post(GITHUB_API_URL, json={'query': query, 'variables': variables}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"HTTP error occurred: {response.status_code} - {response.text}")

def get_repositories_and_users():
    query = """
    query($cursor: String) {
      organization(login: "w3b3d3v") {
        repositories(first: 10, after: $cursor) {
          edges {
            node {
              name
              pullRequests(states: [MERGED], first: 10) {
                edges {
                  node {
                    additions
                    deletions
                    author {
                      login
                    }
                  }
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

    all_repo_data = []
    all_user_activity = {}

    cursor = None
    has_next_page = True

    while has_next_page:
        variables = {'cursor': cursor}
        data = fetch_data(query, variables)
        organization_data = data['data'].get('organization', {})
        repositories = organization_data.get('repositories', {}).get('edges', [])
        page_info = organization_data.get('repositories', {}).get('pageInfo', {})
        has_next_page = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor')

        for edge in repositories:
            repo = edge.get('node', {})
            repo_name = repo.get('name', 'Unknown')
            pr_nodes = repo.get('pullRequests', {}).get('edges', [])

            total_lines_changed = sum(pr.get('node', {}).get('additions', 0) + pr.get('node', {}).get('deletions', 0) for pr in pr_nodes)

            all_repo_data.append({
                'repo_name': repo_name,
                'total_lines_changed': total_lines_changed
            })

            for pr in pr_nodes:
                user = pr.get('node', {}).get('author', {}).get('login', 'Unknown')
                lines_changed = pr.get('node', {}).get('additions', 0) + pr.get('node', {}).get('deletions', 0)
                if user in all_user_activity:
                    all_user_activity[user] += lines_changed
                else:
                    all_user_activity[user] = lines_changed

    df_repos = pd.DataFrame(all_repo_data)
    df_repo_codelines = df_repos.sort_values(by='total_lines_changed', ascending=False)
    
    df_users = pd.DataFrame(all_user_activity.items(), columns=['user', 'total_lines_changed'])
    df_user_codelines = df_users.sort_values(by='total_lines_changed', ascending=False)

    return df_repo_codelines, df_user_codelines

def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS CodeLines_from_repo (
        repo_name TEXT PRIMARY KEY,
        total_lines_changed INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS CodeLines_from_user (
        user TEXT PRIMARY KEY,
        total_lines_changed INTEGER
    )
    ''')

    conn.close()

def store_data(df_repo_codelines, df_user_codelines):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with conn:
        for _, row in df_repo_codelines.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO CodeLines_from_repo (repo_name, total_lines_changed)
            VALUES (?, ?)
            ''', (row['repo_name'], row['total_lines_changed']))

        for _, row in df_user_codelines.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO CodeLines_from_user (user, total_lines_changed)
            VALUES (?, ?)
            ''', (row['user'], row['total_lines_changed']))

    conn.close()

def main():
    df_repo_codelines, df_user_codelines = get_repositories_and_users()

    create_tables()

    store_data(df_repo_codelines, df_user_codelines)

    pd.set_option('display.max_rows', None)

    # Consultar dados da tabela CodeLines_from_repo
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM CodeLines_from_repo')
    repos = cursor.fetchall()



    cursor.execute('SELECT * FROM CodeLines_from_user')
    users = cursor.fetchall()



    conn.close()

if __name__ == "__main__":
    main()
