import requests
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def get_github_data(org_name, access_token):
    url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {'Authorization': f'token {access_token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Parse the JSON response
        repos = response.json()
        df = pd.DataFrame(repos)
        print(df)
        return df
        for repo in repos:
            print("repo: ", repo)
            # print(f"Repository Name: {repo['name']}")
            # print(f"Stars: {repo['stargazers_count']}")
            # print(f"Forks: {repo['forks_count']}")
            # print(f"Open Issues: {repo['open_issues_count']}")
            print("--------------------------------------------------")
    else:
        print("Failed to retrieve data:", response.status_code, response.text)

# Replace 'your_org_name' with your organization's name and 'your_access_token' with your actual GitHub access token

get_github_data('w3b3d3v', GITHUB_TOKEN)