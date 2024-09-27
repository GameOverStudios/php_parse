import chromadb
from chromadb import Settings

def get_chroma_client():
    settings = Settings(
        is_persistent=True,
        persist_directory="./chroma"
    )
    return chromadb.Client(settings=settings)

# Função para carregar todas as coleções no ChromaDB
def load_collections(chroma_client):
    collections = chroma_client.list_collections()
    print("::: Loaded Collections :::")
    for collection in collections:
        print(f"- Collection Name: {collection['name']}, Document Count: {collection['num_documents']}")
