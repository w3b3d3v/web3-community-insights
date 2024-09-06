import sqlite3
import os
import subprocess
import pandas as pd

db_path = os.getenv('DB_PATH', 'github_insights/process_datas/github_data.db')

stars_script_path = os.getenv('STARS_SCRIPT_PATH', 'github_insights/process_datas/stars.py')
codelines_script_path = os.getenv('CODELINES_SCRIPT_PATH', 'github_insights/process_datas/codelines.py')
forks_script_path = os.getenv('FORKS_SCRIPT_PATH', 'github_insights/process_datas/forks.py')
issues_script_path = os.getenv('ISSUES_SCRIPT_PATH', 'github_insights/process_datas/issues.py')
pullrequest_script_path = os.getenv('PULLREQUEST_SCRIPT_PATH', 'github_insights/process_datas/pullrequest.py')
timetoclose_script_path = os.getenv('TIMETOCLOSE_SCRIPT_PATH', 'github_insights/process_datas/timetoclose.py')

def list_tables():
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
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
    except sqlite3.Error as e:
        print(f"Erro ao visualizar dados da tabela '{table_name}': {e}")
        df = pd.DataFrame()
    finally:
        conn.close()

    return df

def run_script(script_path):
    try:
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar {script_path}: {e}")

def drop_table(table_name):
    """Exclui uma tabela do banco de dados."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao excluir a tabela '{table_name}': {e}")
    finally:
        conn.close()

def create_users_contribution_table():
    """Cria a tabela 'Users_contribution'."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        drop_table('Users_contribution')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users_contribution (
            username TEXT PRIMARY KEY,
            PR_from_user INTEGER DEFAULT 0,
            Issues_from_user INTEGER DEFAULT 0,
            CodeLines_from_user INTEGER DEFAULT 0,
            Forks_from_user INTEGER DEFAULT 0,
            Stars_from_user INTEGER DEFAULT 0,
            Time_to_close INTEGER DEFAULT 0
        )
        ''')
        conn.commit()
        print("Tabela 'Users_contribution' criada com sucesso.")
    except sqlite3.Error as e:
        print(f"Erro ao criar a tabela 'Users_contribution': {e}")
    finally:
        conn.close()

def insert_data_into_users_contribution():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        tables = {
            "PR_from_user": "PR_from_user",
            "Issues_from_user": "Issues_from_user",
            "CodeLines_from_user": "CodeLines_from_user",
            "Forks_from_user": "Forks_from_user",
            "Stars_from_user": "Stars_from_user",
            "Time_to_close": "Time_to_close"
        }

        user_data = {table: {} for table in tables.values()}

        for table_name, column_name in tables.items():
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            for row in rows:
                username = row[0]
                contribution = row[1]

                if username not in user_data[column_name]:
                    user_data[column_name][username] = 0
                
                user_data[column_name][username] += contribution

        cursor.execute("DELETE FROM Users_contribution")

        for column_name, users in user_data.items():
            for username, contribution in users.items():
                cursor.execute(f'''
                INSERT INTO Users_contribution (username, {column_name})
                VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET {column_name} = excluded.{column_name}
                ''', (username, contribution))

        conn.commit()

    except sqlite3.Error as e:
        print(f"Erro ao popular a tabela 'Users_contribution': {e}")
    finally:
        conn.close()

def main():
    print("Atualizando o banco de dados...")

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

    create_users_contribution_table()
    insert_data_into_users_contribution()

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

    df = view_table_data(selected_table)
    if not df.empty:
        print(f"\nDados da tabela '{selected_table}':")
        print(df.to_string(index=False))
    else:
        print("Nenhum dado encontrado para exibir.")

if __name__ == "__main__":
    main()
