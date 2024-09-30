import json
import sqlite3
import os
import re

def create_connection(db_file):
    """Cria uma conexão com o banco de dados SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
    return conn

def create_table(conn, create_table_sql):
    """Cria uma tabela."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(f"Erro ao criar tabela: {e}")

def insert_json_data(conn, json_data, filename, filter_array, file_id):
    """Insere os dados JSON em uma tabela, filtrando por um array."""
    cursor = conn.cursor()
    print(':::> ' + filename)
    try:
        insert_json_data_recursive(conn, json_data, filename, "", 0, filter_array, file_id)
        conn.commit()  # Commit changes after inserting data
    except sqlite3.Error as e:
        print(f"**** ERROR: {e}")

def insert_json_data_recursive(conn, data, filename, parent_key, level, filter_array, file_id):
    """Insere os dados JSON de forma recursiva, filtrando por um array."""
    cursor = conn.cursor()
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                if key in filter_array or (key == 'kind' and value in ['class', 'method', 'program', 'commentblock', 'identifier', 'propertystatement', 'property', 'parameter', 'block', 'expressionstatement', 'call', 'staticlookup', 'parentreference', 'variable', 'assign', 'propertylookup', 'return', 'entry', 'call', 'call']):
                    if isinstance(value, (dict, list)):
                        insert_json_data_recursive(conn, value, filename, f"{parent_key}.{key}", level + 1, filter_array, file_id)
                    elif isinstance(value, str) and '/**' in value:
                        # Extrai @defgroup e @ingroup
                        defgroup_match = re.search(r'@defgroup\s+(.+)', value)
                        ingroup_match = re.search(r'@ingroup\s+(.+)', value)
                        if defgroup_match:
                            cursor.execute(
                                f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                                (file_id, "defgroup", defgroup_match.group(1).strip(), 0)
                            )
                        if ingroup_match:
                            cursor.execute(
                                f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                                (file_id, "ingroup", ingroup_match.group(1).strip(), 0)
                            )
                        # Insere o comentário em uma única linha
                        value = value.replace('\n', ' ')
                        cursor.execute(
                            f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                            (file_id, key, value, 0)
                        )
                    else:
                        cursor.execute(
                            f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                            (file_id, f"{parent_key}.{key}", json.dumps(value), level + 1)
                        )
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    insert_json_data_recursive(conn, item, filename, f"{parent_key}[{i}]", level + 1, filter_array, file_id)
                elif isinstance(item, str) and '/**' in value:
                    # Extrai @defgroup e @ingroup
                    defgroup_match = re.search(r'@defgroup\s+(.+)', item)
                    ingroup_match = re.search(r'@ingroup\s+(.+)', item)
                    if defgroup_match:
                        cursor.execute(
                            f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                            (file_id, "defgroup", defgroup_match.group(1).strip(), 0)
                        )
                    if ingroup_match:
                        cursor.execute(
                            f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                            (file_id, "ingroup", ingroup_match.group(1).strip(), 0)
                        )
                    # Insere o comentário em uma única linha
                    item = item.replace('\n', ' ')
                    cursor.execute(
                        f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                        (file_id, key, item, 0)
                    )
                else:
                    cursor.execute(
                        f"INSERT INTO json_data (file_id, key, value, level) VALUES (?, ?, ?, ?)",
                        (file_id, f"{parent_key}[{i}]", json.dumps(item), level + 1)
                    )
        conn.commit()  # Commit changes after inserting data
    except sqlite3.Error as e:
        print(f"Erro ao inserir dados: {e}")

def create_database(db_file, directory, filter_fields):
    """Cria o banco de dados e insere os dados JSON, filtrando por um array."""
    conn = create_connection(db_file)
    if conn is not None:
        # Cria a tabela de arquivos
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE
        );
        """
        create_table(conn, create_table_sql)

        # Cria a tabela de dados JSON
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS json_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            level INTEGER,
            FOREIGN KEY (file_id) REFERENCES files(id)
        );
        """
        create_table(conn, create_table_sql)

        # Cria os índices
        conn.execute("CREATE INDEX idx_file_id ON json_data (file_id)")
        conn.execute("CREATE INDEX idx_key ON json_data (key)")
        conn.commit()

        # Insere os dados JSON
        process_json_files_in_directory(conn, directory, filter_fields)

        conn.commit()  # Commit changes after inserting data
        conn.close()
    else:
        print("Erro ao conectar ao banco de dados.")

def process_json_files_in_directory(conn, directory, filter_fields):
    """Processa os arquivos JSON em um diretório, filtrando por um array."""
    cursor = conn.cursor()
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            json_data = load_json(filepath)

            # Insere o nome do arquivo na tabela de arquivos
            cursor.execute(
                "INSERT OR IGNORE INTO files (filename) VALUES (?)", (filename,)
            )
            conn.commit()

            # Obtém o ID do arquivo da tabela de arquivos
            cursor.execute(
                "SELECT id FROM files WHERE filename = ?", (filename,)
            )
            file_id = cursor.fetchone()[0]

            # Insere os dados JSON na tabela de dados JSON
            insert_json_data(conn, json_data, filename, filter_fields, file_id)

def load_json(file_path):
    """Carrega o JSON de um arquivo."""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def query_by_filename(conn, filename):
    """Consulta dados por nome de arquivo."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            json_data.key, 
            json_data.value 
        FROM 
            json_data 
        JOIN 
            files ON json_data.file_id = files.id 
        WHERE 
            files.filename = ?
        """, 
        (filename,)
    )
    rows = cursor.fetchall()
    for row in rows:
        print(f"Chave: {row[0]}, Valor: {row[1]}")

def query_by_key(conn, key):
    """Consulta dados por chave."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT files.filename, json_data.value FROM json_data JOIN files ON json_data.file_id = files.id WHERE json_data.key = ?", (key,)
    )
    rows = cursor.fetchall()
    for row in rows:
        print(f"Arquivo: {row[0]}, Valor: {row[1]}")

def query_filtered_by_key(conn, key_prefix):
    """Consulta dados por chave com filtro de prefixo."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT files.filename, json_data.key, json_data.value FROM json_data JOIN files ON json_data.file_id = files.id WHERE json_data.key LIKE ?", (key_prefix + "%",)
    )
    rows = cursor.fetchall()
    for row in rows:
        print(f"Arquivo: {row[0]}, Chave: {row[1]}, Valor: {row[2]}")

# Configurações do banco de dados
db_file = "json_data.db"
directory = 'output'

# Define os campos que você quer mostrar
filter_fields = ['kind', 'children', 'class', 'value', 'name', 'isAnonymous', 'extends', 'resolution', 'implements', 'body', 'properties', 'value', 'readonly', 'nullable', 'type', 'visibility', 'isStatic', 'arguments', 'byref', 'variadic', 'expr', 'what', 'offset', 'raw', 'unicode', 'isDoubleQuote', 'items', 'key', 'curly', 'unpack', 'shortForm', 'isAbstract', 'isFinal', 'isReadonly', 'isStatic', 'left', 'right', 'operator', 'byRef', 'leadingComments', 'comments']

# Cria o banco de dados e insere os dados
#create_database(db_file, directory, filter_fields)

# Exemplos de consultas
conn = create_connection(db_file)
if conn is not None:
    print("----- Consulta por nome de arquivo -----")
    query_by_filename(conn, "BxAclDb.php.json")

    print("----- Consulta por chave -----")
    query_by_key(conn, "kind")

    print("----- Consulta filtrada por prefixo de chave -----")
    query_filtered_by_key(conn, "children")

    conn.close()