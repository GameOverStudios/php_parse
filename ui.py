import tkinter as tk
from tkinter import messagebox
import chromadb
from chromadb import Settings

# Configurações do ChromaDB
settings = Settings(
    is_persistent=True,
    persist_directory="chroma"
)
client = chromadb.Client(settings=settings)

# Obter todas as coleções disponíveis
collections = client.list_collections()  # Obtém a lista de coleções

# Se não houver coleções, cria uma coleção padrão
if not collections:
    collection_name = "php_parse_collection"
    collection = client.get_or_create_collection(collection_name)
    collections = [collection_name]
else:
    collections = [col.name for col in collections]  # Extrai os nomes das coleções

# Define a coleção padrão
current_collection = collections[0]

def search_database():
    query_text = entry.get()
    if not query_text:
        messagebox.showwarning("Input Error", "Please enter a search term.")
        return

    # Obtém a coleção selecionada
    selected_collection = collection_var.get()
    collection = client.get_collection(selected_collection)

    # Realiza a consulta na ChromaDB
    results = collection.query(
        query_texts=[query_text],
        n_results=5  # Número de resultados desejados
    )

    # Exibe os resultados
    result_window.delete(1.0, tk.END)  # Limpa a janela de resultados
    for result in results["documents"]:
        result_window.insert(tk.END, result + "\n")

# Cria a interface do Tkinter
root = tk.Tk()
root.title("ChromaDB Search Interface")

# Campo de entrada
entry = tk.Entry(root, width=50)
entry.pack(pady=20)

# Dropdown para selecionar a coleção
collection_var = tk.StringVar(root)
collection_var.set(current_collection)  # Define a coleção padrão
collection_menu = tk.OptionMenu(root, collection_var, *collections)
collection_menu.pack(pady=10)

# Botão de pesquisa
search_button = tk.Button(root, text="Search", command=search_database)
search_button.pack(pady=10)

# Janela para exibir resultados
result_window = tk.Text(root, height=10, width=70)
result_window.pack(pady=20)

root.mainloop()
