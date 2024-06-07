import requests
import datetime
from datetime import timedelta
import pandas as pd
import re

import os
from dotenv import load_dotenv
load_dotenv()

from google.cloud import bigquery

project_id = "web3dev-discord"
service_account_path="/Users/nomadbitcoin/Projects/web3-community-insights/update_bigquery_database/web3dev-discord.json"

def get_latest_date_from_bigquery():
    print("Getting last data point from BigQuery...")
    
    # Configura o cliente do BigQuery
    client = bigquery.Client(project=project_id)
    
    # Constrói a consulta SQL
    query = f"""
    SELECT MAX(date) AS latest_date
    FROM `web3dev-discord.discord_insights.channels_engagement`
    """
    
    # Executa a consulta
    query_job = client.query(query)
    
    # Espera a consulta finalizar e pega o resultado
    results = query_job.result()
    
    # Extrai a data mais recente do resultado
    for row in results:
        latest_date = row.latest_date
        print(f"A data mais recente é: {latest_date}")
        return latest_date
    
def fetch_data(start_date: str):
    print("Fetching discord historical data...")
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6',
        'Authorization': os.getenv("AUTHORIZATION_CODE"),
        'Cookie': os.getenv("COOKIE_CODE"),
        'Referer': f'https://discord.com/developers/servers/898706705779687435/analytics/engagement?interval=2&start={start_date}&end={today}',
        'Sec-CH-UA': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'X-Track': os.getenv("X_TRACK_CODE")
    }

    combined_data = []
    types = ["text", "voice"]  # Definindo os tipos para cada request
    
    
    for type_ in types:
        url = f"https://discord.com/api/v9/guilds/898706705779687435/analytics/engagement/{type_}-channels?start={start_date}&end={today}&interval=1"

        try:
            # Fazendo o request
            response = requests.get(url, headers=headers)
            # Verifica se a resposta foi bem-sucedida
            if response.status_code == 200:
                data = response.json()
                # Adicionando a coluna 'type'
                for item in data:
                    item["type"] = type_
                combined_data.extend(data)
            else:
                print(f"Request para {url} falhou com status code: {response.status_code}")
        except Exception as e:
            print(f"Erro ao fazer request para {url}: {str(e)}")
    
    # Convertendo os dados combinados para um DataFrame
    df = pd.DataFrame(combined_data)
    return df

def clean_channel_names(text):
    text = text.replace("'", "")
    
    # Procura por um dos caracteres "•" ou "・", e captura tudo após ele
    match = re.search(r'[•・](.*)', text)
    if match:
        # Retorna tudo que está após o caractere encontrado
        return match.group(1)
    else:
        # Se nenhum dos caracteres for encontrado, retorna o texto original
        return text
    
def remove_bad_data(df):
    # Step 1: Filter out rows where 'channel_name' is "Unknown"
    filtered_df = df[df['channel_name'] != "Unknown"]
    
    # Step 2: Sort the DataFrame by 'channel_name', 'date', and 'participators' in descending order
    sorted_df = filtered_df.sort_values(by=['channel_name', 'date', 'participators'], ascending=[True, True, False])
    
    # Step 3: Drop duplicates while keeping the first occurrence (the one with the maximum 'participators')
    cleaned_df = sorted_df.drop_duplicates(subset=['channel_name', 'date'], keep='first')
    
    # Step 4: Reset the index of the DataFrame and drop the old index
    cleaned_df = cleaned_df.reset_index(drop=True)
    
    # Return the cleaned DataFrame
    return cleaned_df

def salvar_dataframe_bigquery(dataframe):
    print("Writing historical data at database...")
    # Informações fixas
    dataset_id = "discord_insights"
    table_id = "channels_engagement"
    
    client = bigquery.Client(project=project_id)

    # Define o schema da tabela
    schema = [
        bigquery.SchemaField("date", "TIMESTAMP"),
        bigquery.SchemaField("channel_name", "STRING"),
        bigquery.SchemaField("channel_id", "INTEGER"),
        bigquery.SchemaField("participators", "INTEGER"),
        bigquery.SchemaField("communicators", "INTEGER"),
        bigquery.SchemaField("messages_sent", "FLOAT"),
        bigquery.SchemaField("pct_participated_in_channel", "FLOAT"),
        bigquery.SchemaField("pct_communicated_in_channel", "FLOAT"),
        bigquery.SchemaField("type", "STRING"),
    ]

    # Configura o job para carregar os dados
    job_config = bigquery.LoadJobConfig()
    job_config.schema = schema
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.autodetect = False  # Importante pois estamos fornecendo um esquema

    # Prepara a referência da tabela
    table_ref = client.dataset(dataset_id).table(table_id)

    # Tenta escrever o DataFrame no BigQuery
    try:
        job = client.load_table_from_dataframe(dataframe, table_ref, job_config=job_config)
        job.result()  # Aguarda a finalização do job
        print("DataFrame salvo com sucesso no BigQuery!")
    except Exception as e:
        print(f"Erro ao salvar o DataFrame no BigQuery: {e}")

def fetch_and_store_data():
    last_date = get_latest_date_from_bigquery()
    last_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d") if last_date is not None else "2022-01-01"

    data = fetch_data(last_date)

    print("Processing and cleaning data...")
    data = data.astype({
        'interval_start_timestamp': 'datetime64[ns, UTC]',
        'channel_name': 'string',
        'channel_id': 'int64',
        'participators': 'int64',
        'communicators': 'int64',
        'messages_sent': 'float64',
        'pct_participated_in_channel': 'float64',
        'pct_communicated_in_channel': 'float64',
        'type': 'string'
    })

    data.rename(columns={"interval_start_timestamp": "date"}, inplace=True)
    data['channel_name'] = data['channel_name'].apply(clean_channel_names)
    cleaned_data = remove_bad_data(data)
    salvar_dataframe_bigquery(cleaned_data)

if __name__ == "__main__":
    fetch_and_store_data()
    print("Executed successfully")