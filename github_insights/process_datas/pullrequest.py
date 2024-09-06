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

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS PR_from_user (
    user TEXT PRIMARY KEY,
    merged_pull_requests_count INTEGER
)
''')

def fetch_data(query):
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
    
    repositories = organization_data.get('repositories', {}).get('nodes', [])

    repo_data = []
    user_activity = {}

    for repo in repositories:
        repo_name = repo.get('name', 'Unknown')
        pr_nodes = repo.get('pullRequests', {}).get('nodes', [])

        merged_pr_count = len(pr_nodes)
        repo_data.append({
            'repo_name': repo_name,
            'merged_pull_requests_count': merged_pr_count
        })

        for pr in pr_nodes:
            user = pr.get('author', {}).get('login', 'Unknown')
            if user in user_activity:
                user_activity[user] += 1
            else:
                user_activity[user] = 1

    
    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'merged_pull_requests_count'])
    df_users_pr_merged = df_users.sort_values(by='merged_pull_requests_count', ascending=False)

    return df_users_pr_merged

def get_repositories_with_pagination():
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) {
          nodes {
            name
            pullRequests(states: [MERGED], first: 100) {
              nodes {
                number
                state
                author {
                  login
                }
              }
              totalCount
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
            pr_nodes = repo.get('pullRequests', {}).get('nodes', [])

            merged_pr_count = len(pr_nodes)

            all_repos.append({
                'repo_name': repo_name,
                'merged_pull_requests_count': merged_pr_count
            })

            for pr in pr_nodes:
                user = pr.get('author', {}).get('login', 'Unknown')
                if user in user_activity:
                    user_activity[user] += 1
                else:
                    user_activity[user] = 1


    
    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'merged_pull_requests_count'])
    df_users_pr_merged = df_users.sort_values(by='merged_pull_requests_count', ascending=False)

    return df_users_pr_merged

def store_data(df_users_pr_merged):
    with conn:
 

        for _, row in df_users_pr_merged.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO PR_from_user (user, merged_pull_requests_count)
            VALUES (?, ?)
            ''', (row['user'], row['merged_pull_requests_count']))

df_users_pr_merged = get_repositories_with_pagination()
store_data(df_users_pr_merged)



cursor.execute('SELECT * FROM PR_from_user')
users = cursor.fetchall()



conn.close()
