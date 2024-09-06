import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv('DB_PATH', 'github_insights/process_datas/github_data.db')

conn = sqlite3.connect(db_path)

df_users_forks = pd.read_sql_query("SELECT * FROM Forks_from_user", conn)
df_users_pr_merged = pd.read_sql_query("SELECT * FROM PR_from_user", conn)
df_users_issues = pd.read_sql_query("SELECT * FROM Issues_from_user", conn)
df_users_stars = pd.read_sql_query("SELECT * FROM Stars_from_user", conn)

conn.close()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("GitHub Insights Dashboard"), className="mb-4 mt-4")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='user-forks-graph'), md=6),
        dbc.Col(dcc.Graph(id='user-pr-graph'), md=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='user-issues-graph'), md=6),
        dbc.Col(dcc.Graph(id='user-stars-graph'), md=6)
    ])
])

# Callbacks para atualizar os gráficos
@app.callback(
    Output('user-forks-graph', 'figure'),
    Output('user-pr-graph', 'figure'),
    Output('user-issues-graph', 'figure'),
    Output('user-stars-graph', 'figure'),
    Input('user-forks-graph', 'id')
)
def update_graphs(_):
    fig_user_forks = px.bar(df_users_forks, x='user', y='forks_count',
                            title='Forks por Usuário',
                            labels={'user': 'Usuário', 'forks_count': 'Quantidade de Forks'},
                            template='plotly_dark')

    fig_user_pr = px.bar(df_users_pr_merged, x='user', y='merged_pull_requests_count',
                         title='PRs Mescladas por Usuário',
                         labels={'user': 'Usuário', 'merged_pull_requests_count': 'Quantidade de PRs Mescladas'},
                         template='plotly_dark')

    fig_user_issues = px.bar(df_users_issues, x='user', y='issues_count',
                             title='Issues por Usuário',
                             labels={'user': 'Usuário', 'issues_count': 'Quantidade de Issues'},
                             template='plotly_dark')

    fig_user_stars = px.bar(df_users_stars, x='user', y='repositories_stared_count',
                            title='Estrelas por Usuário',
                            labels={'user': 'Usuário', 'repositories_stared_count': 'Quantidade de Repositórios Estrelados'},
                            template='plotly_dark')

    return fig_user_forks, fig_user_pr, fig_user_issues, fig_user_stars

if __name__ == '__main__':
    app.run_server(debug=True)
