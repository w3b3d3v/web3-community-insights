import discord
import pandas as pd

from google.cloud import bigquery
from google.cloud import secretmanager

from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.members = True  # Habilita o intent para acessar membros do servidor
client = discord.Client(intents=intents)

project_id = "web3dev-discord"

# def access_secret_version(secret_id, version_id="latest"):
#     # Verifica se a função está sendo executada no Google Cloud Functions
#     if os.getenv('GOOGLE_CLOUD_PROJECT'):
#         # Acesso ao Secret Manager
#         client = secretmanager.SecretManagerServiceClient()
#         name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/secrets/{secret_id}/versions/{version_id}"
#         response = client.access_secret_version(request={"name": name})
#         return response.payload.data.decode("UTF-8")
#     else:
#         # Uso da variável de ambiente local
#         return os.getenv(secret_id)

def save_roles_bigquery(df):
    dataset_id = "discord_insights"
    table_id = "roles_info"

    try:
        client = bigquery.Client(project=project_id)
        print("BigQuery client created successfully.")
        
        schema = [
            bigquery.SchemaField("role_name", "STRING"),
            bigquery.SchemaField("role_id", "INTEGER"),
            bigquery.SchemaField("member_count", "INTEGER"),
            bigquery.SchemaField("date", "DATE")
        ]

        job_config = bigquery.LoadJobConfig()
        job_config.schema = schema
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

        table_ref = client.dataset(dataset_id).table(table_id)
        print(f"Table reference for {dataset_id}.{table_id} obtained successfully.")

        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        print("Job to load data to BigQuery started...")

        job.result()  # Wait for the job to complete.
        print("Roles data saved successfully to BigQuery!")
    except Exception as e:
        print("An error occurred while saving data to BigQuery.")
        print(e)
        traceback.print_exc()

async def get_roles_data(guild):
    roles_data = []
    for role in guild.roles:
        member_count = sum(1 for member in guild.members if role in member.roles)
        roles_data.append({
            'role_name': role.name,
            'role_id': role.id,
            'member_count': member_count
        })
    return pd.DataFrame(roles_data)

async def main():
    intents = discord.Intents.default()
    intents.members = True  # Habilita o intent para acessar membros do servidor
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        guild = discord.utils.get(client.guilds, name='WEB3DEV')
        if guild:
            print("Getting roles data...")
            roles_df = await get_roles_data(guild)
            roles_df['date'] = pd.Timestamp('today').floor('D')
            save_roles_bigquery(roles_df)
        await client.close()

    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    await client.start(bot_token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    print("Executed successfully")