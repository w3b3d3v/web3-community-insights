import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime

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

def calculate_time_to_close(created_at, closed_at):
    created_date = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
    closed_date = datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%SZ')
    return (closed_date - created_date).days

def process_data(all_issues):
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

    # Calculate average time to close per issue
    for user, stats in user_activity.items():
        avg_time = stats['total_time'] / stats['issue_count']
        user_activity[user] = avg_time

    df_time_to_close = pd.DataFrame(user_activity.items(), columns=['user', 'average_time_to_close_days'])
    df_time_to_close = df_time_to_close.sort_values(by='average_time_to_close_days', ascending=False)

    return df_time_to_close

def get_repositories_with_pagination():
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
        
        # Check if 'data' is in the response
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

df_time_to_close = get_repositories_with_pagination()

pd.set_option('display.max_rows', None)

print("\nMédia de tempo para fechamento de issues por usuário:")
print(df_time_to_close)
