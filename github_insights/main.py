from process_datas.pullrequest import df_repo_pr_merged, df_users_pr_merged
from process_datas.forks import df_repo_forks, df_users_forks
from process_datas.issues import df_repo_issues, df_users_issues
from process_datas.stars import df_repo_stars, df_users_stars
from process_datas.timetoclose import df_time_to_close
from process_datas.codelines import df_repo_codelines, df_user_codelines



def main():
    
    df_repo_pr_merged()
    df_users_pr_merged()

    df_repo_forks()
    df_users_forks()

    df_repo_issues()
    df_users_issues()

    df_repo_stars()
    df_users_stars()

    df_repo_codelines()
    df_user_codelines()
   
    df_time_to_close()