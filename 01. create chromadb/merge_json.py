import os
import json

def merge_json_files(directory):
    merged_data = []

    # Percorre todos os arquivos no diretório
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            
            with open(file_path, 'r', encoding='utf-8') as json_file:
                # Carregar o conteúdo JSON
                json_data = json.load(json_file)
                
                # Adicionar o caminho do arquivo e a árvore parseada ao documento final
                merged_data.append({
                    "file_path": file_path,
                    "parse_tree": json_data
                })

    return merged_data

# Diretório contendo os arquivos JSON
directory = r'../output'

# Mesclar todos os arquivos JSON em um único documento
merged_json = merge_json_files(directory)

# Salvar o documento final em um novo arquivo
with open('merged_data.json', 'w', encoding='utf-8') as outfile:
    json.dump(merged_json, outfile, indent=4)

print("Todos os arquivos JSON foram mesclados com sucesso.")
