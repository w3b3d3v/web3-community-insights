import sqlite3
import os
import subprocess

# Caminho do banco de dados utilizando variável de ambiente ou caminho padrão
db_path = os.getenv('DB_PATH', 'github_insights/process_datas/github_data.db')

# Caminhos para os scripts utilizando variáveis de ambiente ou caminhos padrão
stars_script_path = os.getenv('STARS_SCRIPT_PATH', 'github_insights/process_datas/stars.py')
codelines_script_path = os.getenv('CODELINES_SCRIPT_PATH', 'github_insights/process_datas/codelines.py')
forks_script_path = os.getenv('FORKS_SCRIPT_PATH', 'github_insights/process_datas/forks.py')
issues_script_path = os.getenv('ISSUES_SCRIPT_PATH', 'github_insights/process_datas/issues.py')
pullrequest_script_path = os.getenv('PULLREQUEST_SCRIPT_PATH', 'github_insights/process_datas/pullrequest.py')
timetoclose_script_path = os.getenv('TIMETOCLOSE_SCRIPT_PATH', 'github_insights/process_datas/timetoclose.py')

def list_tables():
    """Lista todas as tabelas no banco de dados."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Erro ao listar tabelas: {e}")
        tables = []
    finally:
        conn.close()

    return tables

def view_table_data(table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Erro ao visualizar dados da tabela '{table_name}': {e}")
        rows = []
    finally:
        conn.close()

    return rows

print("Atualizando o banco de dados...")

def run_script(script_path):
    try:
        result = subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar {script_path}: {e}")


def drop_table(table_name):
    """Exclui uma tabela do banco de dados."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
        print(f"Tabela '{table_name}' foi excluída com sucesso.")
    except sqlite3.Error as e:
        print(f"Erro ao excluir a tabela '{table_name}': {e}")
    finally:
        conn.close()

def main():
    # Executa todos os scripts necessários
    scripts = [
        stars_script_path,
        codelines_script_path,
        forks_script_path,
        issues_script_path,
        pullrequest_script_path,
        timetoclose_script_path
    ]
    
    for script in scripts:
        run_script(script)

    try:
        print("Banco de dados atualizado!")
        tables = list_tables()

        print("Tabelas do banco de dados:")
        for idx, table in enumerate(tables):
            print(f"{idx + 1}: {table[0]}")

        try:
            table_index = int(input("Escolha o número da tabela para visualizar os dados: ")) - 1
            if table_index < 0 or table_index >= len(tables):
                raise ValueError("Número da tabela inválido.")
            selected_table = tables[table_index][0]
        except (ValueError, IndexError):
            print("Seleção inválida. Encerrando.")
            return

        data = view_table_data(selected_table)
        print(f"\nDados da tabela '{selected_table}':")
        for row in data:
            print(row)
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
