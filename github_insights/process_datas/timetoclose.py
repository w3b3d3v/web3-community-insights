import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
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

def calculate_time_to_close(created_at, closed_at):
    """Calcula o tempo em dias para fechar uma issue."""
    created_date = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
    closed_date = datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%SZ')
    return (closed_date - created_date).days

def process_data(all_issues):
    """Processa os dados das issues para calcular o tempo médio de fechamento por usuário."""
    user_activity = {}
    
    for issue in all_issues:
        assignees = issue.get('assignees', [])
        time_to_close = issue.get('time_to_close_days', 0)
        
        for assignee in assignees:
            user = assignee.get('login', 'Unassigned')
            if user in user_activity:
                user_activity[user]['total_time'] += time_to_close
                user_activity[user]['issue_count'] += 1
            else:
                user_activity[user] = {'total_time': time_to_close, 'issue_count': 1}

    for user, stats in user_activity.items():
        avg_time = stats['total_time'] / stats['issue_count']
        user_activity[user] = avg_time

    df_time_to_close = pd.DataFrame(user_activity.items(), columns=['user', 'average_time_to_close_days'])
    df_time_to_close = df_time_to_close.sort_values(by='average_time_to_close_days', ascending=False)

    return df_time_to_close

def get_repositories_with_pagination():
    """Obtém dados das issues dos repositórios com paginação."""
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) {
          nodes {
            name
            issues(states: [CLOSED], first: 100) {
              nodes {
                number
                createdAt
                closedAt
                assignees(first: 10) {
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
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """
    
    all_issues = []
    has_next_page = True
    end_cursor = None

    while has_next_page:
        paginated_query = query
        if end_cursor:
            paginated_query = paginated_query.replace('repositories(first: 100)', f'repositories(first: 100, after: "{end_cursor}")')
        
        data = fetch_data(paginated_query)
        
        if 'data' not in data:
            print("Response does not contain 'data':", data)
            break
        
        organization_data = data['data'].get('organization', {})
        if not organization_data:
            print("No organization data found in the response:", data)
            break
        
        repositories = organization_data.get('repositories', {}).get('nodes', [])
        page_info = organization_data.get('repositories', {}).get('pageInfo', {})
        
        has_next_page = page_info.get('hasNextPage', False)
        end_cursor = page_info.get('endCursor', None)

        for repo in repositories:
            repo_name = repo.get('name', 'Unknown')
            issue_nodes = repo.get('issues', {}).get('nodes', [])

            for issue in issue_nodes:
                created_at = issue.get('createdAt', '')
                closed_at = issue.get('closedAt', '')
                assignees = issue.get('assignees', {}).get('nodes', [])
                
                if created_at and closed_at:
                    time_to_close = calculate_time_to_close(created_at, closed_at)
                    all_issues.append({
                        'repo_name': repo_name,
                        'issue_number': issue.get('number', 'Unknown'),
                        'time_to_close_days': time_to_close,
                        'assignees': assignees
                    })

    df_time_to_close = process_data(all_issues)
    
    return df_time_to_close

def create_tables():
    """Cria a tabela no banco de dados se não existir."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Time_to_close (
        user TEXT PRIMARY KEY,
        average_time_to_close_days REAL
    )
    ''')

    conn.close()

def store_data(df_time_to_close):
    """Armazena os dados no banco de dados SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with conn:
        for _, row in df_time_to_close.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO Time_to_close (user, average_time_to_close_days)
            VALUES (?, ?)
            ''', (row['user'], row['average_time_to_close_days']))

    conn.close()

def main():
    df_time_to_close = get_repositories_with_pagination()

    create_tables()

    store_data(df_time_to_close)

    pd.set_option('display.max_rows', None)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Time_to_close')
    users = cursor.fetchall()


    conn.close()

if __name__ == "__main__":
    main()
