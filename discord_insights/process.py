import csv
import json

# Abrir arquivo de entrada e saída
input_file = 'output.txt'
output_file = 'output.csv'

# Carregar dados do arquivo de entrada
with open(input_file, 'r') as file:
    data = json.load(file)

# Lista das chaves esperadas no formato CSV
csv_fields = [
    'interval_start_timestamp',
    'channel_name',
    'channel_id',
    'participators',
    'communicators',
    'messages_sent',
    'pct_participated_in_channel',
    'pct_communicated_in_channel'
]

# Processar dados e converter em formato CSV
csv_data = []
csv_data.append(csv_fields)

for item in data:
    csv_row = []
    for field in csv_fields:
        value = item.get(field, '')
        csv_row.append(value)
    csv_data.append(csv_row)

# Escrever dados no arquivo CSV
with open(output_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)

print('Arquivo CSV gerado com sucesso!')
