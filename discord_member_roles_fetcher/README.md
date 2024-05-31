Sure, here is the revised README focusing on setting up the project and adding necessary comments in the code.

# Discord Role Members Counter

This project collects and extracts the number of members for each role in a Discord server and stores this data in Google BigQuery. The script runs daily to track the historical number of roles such as student groups, leaders, and specific tech interests.

## Prerequisites

1. **Python 3.8 or later**
2. **Discord.py library**
3. **Pandas library**
4. **Google Cloud BigQuery client library**
5. **Google Cloud Secret Manager client library**
6. **dotenv library**

## Setup

1. **Install dependencies**:
   ```sh
   pip install discord.py pandas google-cloud-bigquery google-cloud-secret-manager python-dotenv
   ```

2. **Google Cloud Setup**:
   - Ensure you have a Google Cloud project.
   - Enable BigQuery and Secret Manager APIs.
   - Create a dataset `discord_insights` and a table `roles_info` in BigQuery.
   - Store your Discord bot token in Secret Manager.

3. **Environment Variables**:
   - Create a `.env` file in the project root:
     ```ini
     GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
     DISCORD_BOT_TOKEN=your_discord_bot_token
     ```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.