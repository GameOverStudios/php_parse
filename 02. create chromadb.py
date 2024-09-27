import os
import json
import mysql.connector
import chromadb
from chromadb import Settings
from chromadb.utils import embedding_functions

# Configurações de conexão MySQL
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = ''
MYSQL_DATABASE = 'una'

# Flag para usar ou não embeddings
USE_EMBEDDINGS = False

# Função para conectar ao banco MySQL
def connect_to_mysql():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    return conn

# Configuração do ChromaDB
def get_chroma_client():
    settings = Settings(
        is_persistent=True,
        persist_directory="../chroma"
    )
    return chromadb.Client(settings=settings)

# Função de embedding (opcional)
def get_embedding_function():
    if USE_EMBEDDINGS:
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
    return None

# Listar todas as tabelas do banco MySQL
def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

# Verificar se a tabela tem registros
def has_records(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    return count > 0

# Criar uma coleção no ChromaDB e adicionar dados
def create_collection_and_insert_data(conn, table_name, chroma_client, embedding_function):
    prefixed_table_name = f"table_{table_name}"
    print(f"    [++] Creating Collection for table: {prefixed_table_name}")

    # Criar uma nova coleção no ChromaDB
    collection = chroma_client.get_or_create_collection(name=prefixed_table_name, embedding_function=embedding_function)

    # Buscar todos os registros da tabela
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    if rows:
        print(f"    [++] Found data in table: {table_name}")
        documents = [str(row) for row in rows]  # Converte os registros em strings
        ids = [f"{table_name}_{i}" for i in range(len(documents))]  # IDs únicos

        # Se estiver usando embeddings, gera os embeddings
        if USE_EMBEDDINGS and embedding_function:
            print(f"        [++] Generating embeddings for table: {table_name}")
            embeddings = embedding_function(documents)
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=rows,
                ids=ids
            )
        else:
            print(f"        [++] Adding documents without embeddings for table: {table_name}")
            collection.add(
                documents=documents,
                metadatas=rows,
                ids=ids
            )

        print(f"    [OK] Data inserted for table: {table_name}")
    else:
        print(f"    [OK] No data found in table: {table_name}")

# Função para adicionar descrições ao JSON
def add_descriptions_to_json(obj):
    keys = list(obj.keys())
    for key in keys:
        value = obj[key]
        if key not in ['lineno', 'params']:
            if isinstance(value, dict):
                add_descriptions_to_json(value)
                if 'description' not in value:
                    value['description'] = ""
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        add_descriptions_to_json(item)
            else:
                obj['description'] = ""

# Processar arquivos JSON e inserir no ChromaDB
def process_json_files_and_insert_in_chromadb(directory, chroma_client):
    collection_name = "php_parse_collection"
    collection = chroma_client.get_or_create_collection(collection_name)

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                
                # Adicionar descrições ao JSON
                if isinstance(json_data, list):
                    for item in json_data:
                        add_descriptions_to_json(item)
                else:
                    add_descriptions_to_json(json_data)
                
                # Converter JSON em uma string
                json_str = json.dumps(json_data)
                document_id = filename.replace('.json', '')
                try:
                    collection.add(
                        documents=[json_str],
                        metadatas=[{'source': file_path}],
                        ids=[document_id]
                    )
                    print(f"Successfully inserted {file_path}")
                except Exception as e:
                    print(f"Error inserting {file_path}: {e}")
                
                # Sobrescrever o arquivo JSON com descrições
                with open(file_path, 'w', encoding='utf-8') as json_file_write:
                    json.dump(json_data, json_file_write, indent=4)

# Função principal para importar todas as tabelas e JSONs
def import_all_tables_and_jsons_to_chromadb(directory):
    conn = connect_to_mysql()
    chroma_client = get_chroma_client()
    embedding_function = get_embedding_function()

    # Listar todas as tabelas
    tables = list_tables(conn)

    for table_name in tables:
        print(f"::: Processing table: {table_name}")

        # Verifica se a tabela tem registros
        if has_records(conn, table_name):
            print(f"    [++] Table {table_name} has data")
            # Cria a coleção e insere dados
            create_collection_and_insert_data(conn, table_name, chroma_client, embedding_function)
        else:
            print(f"    [--] Table {table_name} is empty")

    # Processar arquivos JSON
    process_json_files_and_insert_in_chromadb(directory, chroma_client)

    conn.close()

# Executa o processo de importação
output_directory = '../output'
import_all_tables_and_jsons_to_chromadb(output_directory)

# Exemplo de busca
def search_in_collection(collection_name, query_text, num_results=5):
    # Conectar ao ChromaDB e obter a coleção
    chroma_client = get_chroma_client()
    collection = chroma_client.get_collection(collection_name)
    
    # Realizar a pesquisa na coleção
    results = collection.query(
        query_texts=[query_text],
        n_results=num_results
    )

    # Exibir os resultados
    for idx, doc in enumerate(results['documents']):
        print(f"Resultado {idx+1}:")
        print("Documento:", doc)
        print("ID:", results['ids'][idx])
        print("Distância:", results['distances'][idx])
        print("Metadados:", results['metadatas'][idx])
        print("-" * 50)

def list_collections(chroma_client):
    collections = chroma_client.list_collections()
    print("Coleções no ChromaDB:")
    for collection in collections:
        print(collection)

# Após a importação
list_collections(get_chroma_client())

# Exemplo de uso da busca
# search_in_collection("php_parse_collection", "FunctionCall", num_results=3)