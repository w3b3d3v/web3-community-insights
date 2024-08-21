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

df_repo_stars, df_users_stars = get_repositories_with_pagination()

pd.set_option('display.max_rows', None)

print("Estrelas por repositórios:")
print(df_repo_stars)

print("\nUsuários e quantidade de repositórios que deram estrelas:")
print(df_users_stars)

