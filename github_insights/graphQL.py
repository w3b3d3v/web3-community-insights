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

# Consulta GraphQL atualizada
query = """
{
  user(login: "Mitish98") {
    repositories(first: 100) {
      nodes {
        name
        forks {
          totalCount
        }
        pullRequests(states: [OPEN, CLOSED], first: 100) {
          nodes {
            title
            state
            createdAt
            author {
              login
            }
            comments(first: 10) {
              nodes {
                body
                createdAt
                author {
                  login
                }
              }
            }
          }
        }
        object(expression: "HEAD") {
          ... on Commit {
            history(first: 100) {
              edges {
                node {
                  message
                  committedDate
                  author {
                    user {
                      login
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def fetch_data():
    response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

def process_data(data):
    # Check if 'data' and 'data['data']' exist and are not None
    if not data or 'data' not in data or not data['data']:
        raise ValueError("Unexpected data structure: {}".format(data))
    
    user_data = data['data'].get('user', {})
    
    # Check if 'user' data is present
    if not user_data:
        raise ValueError("User data not found in the response: {}".format(data))
    
    repositories = user_data.get('repositories', {}).get('nodes', [])

    repo_contributions = {}

    for repo in repositories:
        repo_name = repo.get('name', 'Unknown')
        forks_count = repo.get('forks', {}).get('totalCount', 0)

        if repo_name not in repo_contributions:
            repo_contributions[repo_name] = {
                'users': {},
                'forks': forks_count
            }

        # Pull Requests data
        for pr in repo.get('pullRequests', {}).get('nodes', []):
            pr_author = pr.get('author', {}).get('login', 'Unknown')
            if pr_author not in repo_contributions[repo_name]['users']:
                repo_contributions[repo_name]['users'][pr_author] = {
                    'pull_requests': 0,
                    'comments': 0,
                    'forks': 0,
                    'commits': 0
                }

            repo_contributions[repo_name]['users'][pr_author]['pull_requests'] += 1

            for comment in pr.get('comments', {}).get('nodes', []):
                comment_author = comment.get('author', {}).get('login', 'Unknown')
                if comment_author not in repo_contributions[repo_name]['users']:
                    repo_contributions[repo_name]['users'][comment_author] = {
                        'pull_requests': 0,
                        'comments': 0,
                        'forks': 0,
                        'commits': 0
                    }
                repo_contributions[repo_name]['users'][comment_author]['comments'] += 1

        # Commits data
        history = repo.get('object', {}).get('history', {})
        if history:
            history_edges = history.get('edges', [])
            for edge in history_edges:
                commit_node = edge.get('node', {})
                if commit_node:
                    author = commit_node.get('author', {})
                    if author:
                        user = author.get('user', {})
                        if user:
                            commit_author = user.get('login', 'Unknown')
                            if commit_author not in repo_contributions[repo_name]['users']:
                                repo_contributions[repo_name]['users'][commit_author] = {
                                    'pull_requests': 0,
                                    'comments': 0,
                                    'forks': 0,
                                    'commits': 0
                                }
                            repo_contributions[repo_name]['users'][commit_author]['commits'] += 1
                        else:
                            print(f"Missing user data in commit_node: {commit_node}")
                    else:
                        print(f"Missing author data in commit_node: {commit_node}")
                else:
                    print(f"Missing commit_node data in edge: {edge}")
        else:
            print(f"Missing history data in repo: {repo}")

    # Creating DataFrames
    repo_data = []
    user_contrib_data = []

    for repo_name, data in repo_contributions.items():
        for user, stats in data['users'].items():
            user_contrib_data.append({
                'repo_name': repo_name,
                'user': user,
                'pull_requests': stats['pull_requests'],
                'comments': stats['comments'],
                'forks': stats['forks'],
                'commits': stats['commits']
            })

        repo_data.append({
            'repo_name': repo_name,
            'forks_count': data['forks']
        })

    df_repos = pd.DataFrame(repo_data)
    df_user_contribs = pd.DataFrame(user_contrib_data)

    return df_repos, df_user_contribs



# Coletar e processar os dados
data = fetch_data()
df_repos, df_user_contribs = process_data(data)

# Exibir ou salvar os dataframes conforme necessário
print(df_repos.head())
print(df_user_contribs.head())
