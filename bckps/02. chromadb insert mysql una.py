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
        persist_directory="chroma"
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
    
    print(f"    [++] Creating Collection for table: {table_name}")

    # Criar uma nova coleção no ChromaDB sem passar a função de embedding se não estiver sendo usada
    if USE_EMBEDDINGS and embedding_function:
        collection = chroma_client.get_or_create_collection(name=table_name, embedding_function=embedding_function)
    else:
        collection = chroma_client.get_or_create_collection(name=table_name)

    # Buscar todos os registros da tabela
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    if rows:
        print(f"    [++] Found data in table: {table_name}")
        documents = [str(row) for row in rows]  # Converte os registros em strings

        ids = [f"{table_name}_{i}" for i in range(len(documents))]  # Cria IDs únicos para os documentos

        # Se estiver usando embeddings, gera os embeddings, senão adiciona sem embeddings
        if USE_EMBEDDINGS and embedding_function:
            print(f"        [++] Generating embeddings for table: {table_name}")
            embeddings = embedding_function(documents)  # Gera embeddings
            collection.add(
                documents=documents,
                embeddings=embeddings,  # Adiciona os embeddings gerados
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

# Função principal para importar todas as tabelas para o ChromaDB
def import_all_tables_to_chromadb():
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
        else:
            print(f"    [--] Table {table_name} is empty")

        # Cria a coleção e insere dados
        create_collection_and_insert_data(conn, table_name, chroma_client, embedding_function)

    conn.close()

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

# Executa o processo de importação
import_all_tables_to_chromadb()

# Exemplo de uso:
#search_in_collection("nome_da_tabela", "consulta que deseja", num_results=3)
