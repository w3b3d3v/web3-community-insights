import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = 'https://api.github.com/graphql'

headers = {
    'Authorization': f'bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}

def fetch_data(query):
    response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"HTTP error occurred: {response.status_code} - {response.text}")

def get_repositories_and_users():
    query = """
    {
      organization(login: "w3b3d3v") {
        repositories(first: 100) {
          nodes {
            name
            pullRequests(states: [MERGED], first: 50) {
              nodes {
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
    }
    """
    
    data = fetch_data(query)
    organization_data = data['data'].get('organization', {})
    repositories = organization_data.get('repositories', {}).get('nodes', [])

    repo_data = []
    user_activity = {}

    for repo in repositories:
        repo_name = repo.get('name', 'Unknown')
        pr_nodes = repo.get('pullRequests', {}).get('nodes', [])

        total_lines_changed = sum(pr.get('additions', 0) + pr.get('deletions', 0) for pr in pr_nodes)

        repo_data.append({
            'repo_name': repo_name,
            'total_lines_changed': total_lines_changed
        })

        for pr in pr_nodes:
            user = pr.get('author', {}).get('login', 'Unknown')
            lines_changed = pr.get('additions', 0) + pr.get('deletions', 0)
            if user in user_activity:
                user_activity[user] += lines_changed
            else:
                user_activity[user] = lines_changed

    df_repos = pd.DataFrame(repo_data)
    df_repo_codelines = df_repos.sort_values(by='total_lines_changed', ascending=False)
    
    df_users = pd.DataFrame(user_activity.items(), columns=['user', 'total_lines_changed'])
    df_user_codelines = df_users.sort_values(by='total_lines_changed', ascending=False)

    return df_repo_codelines, df_user_codelines

def main():
    df_repo_codelines, df_user_codelines = get_repositories_and_users()
    pd.set_option('display.max_rows', None)

    print("Total de linhas de código alteradas por repositório:")
    print(df_repo_codelines)

    print("\nTotal de linhas de código alteradas por usuário:")
    print(df_user_codelines)

if __name__ == "__main__":
    main()
