import chromadb

# Inicializar o cliente ChromaDB
client = chromadb.Client()

# Criar uma coleção para os seus dados
collection = client.get_or_create_collection(
    name="my_collection",
    embedding_function=None,  # Desabilitando embeddings
)

# Função para construir a consulta de pesquisa com base nos níveis de pesquisa
def build_query(levels):
    query = {}
    for level, value in levels.items():
        query[level] = value
    return query

# Função para pesquisar na coleção ChromaDB
def search(query):
    results = collection.query(
        query_texts=[query],  # Provide the query as text
        n_results=10,
    )
    return results["documents"]

# Exemplo de uso
# Níveis de pesquisa:
levels = {
    "kind": "program",
    "loc.start.line": 1,
}

# Construir a consulta
query = build_query(levels)

# Pesquisar na coleção
results = search(query)

# Imprimir os resultados
print(results)