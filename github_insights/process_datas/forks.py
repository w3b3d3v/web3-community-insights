import requests
import pandas as pd
from dotenv import load_dotenv
import os
import time

# Carregar variáveis de ambiente
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = 'https://api.github.com/graphql'

headers = {
    'Authorization': f'bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}

def fetch_data(query, retries=3, delay=5):
    """Função para buscar dados da API do GitHub com repetição em caso de erro."""
    for attempt in range(retries):
        response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Attempt {attempt + 1} failed with status {response.status_code}. Retrying in {delay} seconds...")
            time.sleep(delay)
    
    # Se todas as tentativas falharem, levanta um erro
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
            paginated_query = paginated_query.replace('repositories(first: 50)', f'repositories(first: 50, after: "{end_cursor}")')
        
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

# Executa a coleta e processamento dos dados
df_repo_forks, df_users_forks = get_repositories_with_pagination()

# Configurações para exibir todos os dados
pd.set_option('display.max_rows', None)

print("Forks por repositórios:")
print(df_repo_forks)

print("\nForks por usuário:")
print(df_users_forks)
