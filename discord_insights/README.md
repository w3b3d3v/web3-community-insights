# Discord Insights: Exportando Dados de Engajamento do Discord

Este script em Python foi desenvolvido para processar dados obtidos a partir de uma requisição cURL para o Discord. Ele converte a resposta JSON em um arquivo CSV.

## Instruções

### 1. Copiar o comando cURL

Antes de executar o script, é necessário obter o comando cURL correspondente à requisição feita pelo site do Discord. Para isso, siga as instruções abaixo:

1. Abra o site do Discord Insights e clique em Engagement no navegador.
2. Abra as ferramentas de desenvolvedor do navegador (geralmente, pressionando F12).
3. Vá para a guia "Network" ou "Rede" nas ferramentas de desenvolvedor.
4. Inicie o monitoramento das requisições.
5. Atualize a página do Discord.
6. Localize a requisição desejada na lista de requisições.
7. Clique com o botão direito na requisição e selecione "Copy as cURL" ou "Copiar como cURL".
8. Cole o comando cURL no arquivo `request.txt` (adicione a opção `-o output.txt` antes da URL).

Certifique-se de colar o comando cURL no arquivo `request.txt`, substituindo a linha `curl -o output.txt https://exemplo.com/dados`. Mantenha a opção `-o output.txt` antes da URL.

### 2. Executar o Script

Após copiar o comando cURL para o arquivo `request.txt`, siga as instruções abaixo para executar o script Python:

1. Certifique-se de ter o ambiente Python configurado corretamente.
2. No terminal ou prompt de comando, navegue até o diretório onde o script Python `process.py` e o arquivo `request.txt` estão localizados.
3. Coloque o arquivo request.txt no mesmo diretório do script Python.
4. Execute o script Python usando o seguinte comando:
`bash get_data.sh`


Após a execução do script, um arquivo `output.csv` será gerado com os dados convertidos.

## Dependências

Este script requer as seguintes bibliotecas Python:

- csv
- json