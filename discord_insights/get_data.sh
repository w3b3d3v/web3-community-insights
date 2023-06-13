#!/bin/bash

# Executar comando curl com base no arquivo request.txt e salvar saída em um arquivo
bash request.txt

# Executar script Python
python3 process.py

# Remover o arquivo de saída intermediário
rm output.txt