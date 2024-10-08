import os
import json
import chromadb
from chromadb import Settings

settings = Settings(
    is_persistent=True,
    persist_directory="chroma"
)

client = chromadb.Client(settings=settings)
default_collection_name = "php_parse_collection"
collection = client.get_or_create_collection(default_collection_name)

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

def process_json_files_and_insert_in_chromadb(directory):
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
                
                # Converter JSON em uma string para inserir no ChromaDB
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

def process_single_json_file(file_path, collection_name):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)

        # Adicionar descrições ao JSON
        if isinstance(json_data, list):
            for item in json_data:
                add_descriptions_to_json(item)
        else:
            add_descriptions_to_json(json_data)
        
        # Converter JSON em uma string para inserir no ChromaDB
        json_str = json.dumps(json_data)
        document_id = os.path.basename(file_path).replace('.json', '')
        collection = client.get_or_create_collection(collection_name)
        try:
            collection.add(
                documents=[json_str],
                metadatas=[{'source': file_path}],
                ids=[document_id]
            )
            print(f"Successfully inserted {file_path} into collection '{collection_name}'")
        except Exception as e:
            print(f"Error inserting {file_path}: {e}")

directory = 'output'
#process_json_files_and_insert_in_chromadb(directory)

#print('creating una cms structure database...')
#process_single_json_file('output_database\\una_database_structure.json', 'database_una_cms')

# Exemplo de consulta
results = collection.query(
query_texts=["kind:program", ""],
    n_results=1
)

# Acesse o campo correto
if 'documents' in results:
    for doc in results['documents']:  # 'results['documents']' é uma lista
        # Verificando se 'doc' é um dicionário
        if isinstance(doc, dict):
            kind = doc.get('kind')  # Acessando o campo 'kind'
            loc = doc.get('loc')  # Acessando o campo 'loc'
            
            if kind:
                print(f"Kind: {kind}")
            if loc:
                print(f"Location: {loc}")
        else:
            print("Documento não é um dicionário:", doc)
else:
    print("Nenhum documento encontrado.")