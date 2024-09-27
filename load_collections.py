import chromadb
from chromadb import Settings

def get_chroma_client():
    settings = Settings(
        is_persistent=True,
        persist_directory="chroma"
    )
    return chromadb.Client(settings=settings)

# Função para carregar todas as coleções no ChromaDB
def print_all_collections(client):
    collections = client.list_collections()
    print("Collections:")
    for collection in collections:
        print(f"- {collection}")

print_all_collections(get_chroma_client())