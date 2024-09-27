import os
import json
import sqlite3
from modules.php.traversers.bf import BFTraverser
from modules.php.base import Visitor
from modules.php.syntax_tree import build_syntax_tree

output_dir = r"output"
php_dir = r"C:\xampp\htdocs\una"
split_path_name = "una_"

# Função para criar tabelas no banco de dados
def create_tables(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Criar tabela para arquivos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE
        )
    ''')

    # Criar tabela para nós da AST
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ast_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            type TEXT, 
            attributes TEXT,
            lineno INTEGER,
            description TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id)
        );
    ''')

    connection.commit()
    connection.close()

# Função para inserir um arquivo no banco de dados
def insert_file(db_path, file_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO files (file_path) VALUES (?)
    ''', (file_path,))

    connection.commit()
    connection.close()

# Função para inserir um nó da AST
def insert_ast_node(db_path, file_id, node_type, attributes, lineno, description):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO ast_nodes (file_id, type, attributes, lineno, description) VALUES (?, ?, ?, ?, ?)
    ''', (file_id, node_type, json.dumps(attributes), lineno, description))

    connection.commit()
    connection.close()

# Função para obter o ID do arquivo
def get_file_id(db_path, file_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute('SELECT id FROM files WHERE file_path = ?', (file_path,))
    file_id = cursor.fetchone()[0]

    connection.close()
    return file_id

# Função para processar arquivos PHP em um diretório
def process_php_directory(directory_path, db_path):
    for filename in os.listdir(directory_path):
        if filename.endswith('.php'):
            file_path = os.path.join(directory_path, filename)
            process_php_file(file_path, db_path)

# Função para processar um arquivo PHP
def process_php_file(file_path, db_path):
    try:
        # Analisar o arquivo PHP usando php-parser
        s_tree = build_syntax_tree(file_path)
        ast = analyze_ast(s_tree)

        # Inserir o arquivo no banco de dados
        insert_file(db_path, file_path)
        file_id = get_file_id(db_path, file_path)  # Obtém o ID do arquivo

        # Percorrer a AST e inserir nós no banco de dados
        process_ast(db_path, file_id, ast)

    except Exception as e:
        print(f"Erro ao processar o arquivo {file_path}: {e}")

# Função para processar a AST recursivamente
def process_ast(db_path, file_id, ast):
    # Verifique se a AST tem nós. Caso contrário, não tente processar.
    if hasattr(ast, 'children'):
        for node in ast.children:
            # Converter os atributos para JSON
            attributes = node.get('attributes', {})  # Obtenha atributos se existirem
            lineno = node.get('attributes', {}).get('lineno', None) # Obtém lineno se existir
            description = node.get('description', '')
            # Inserir o nó no banco de dados
            insert_ast_node(db_path, file_id, node['type'], attributes, lineno, description)
            # Chamar recursivamente para processar sub-nós
            # process_ast(db_path, file_id, node) # Não é necessário recursão neste caso

# Função para analisar a AST
def analyze_ast(ast):
    results = []
    # Verifique se a AST tem nós. Caso contrário, retorne uma lista vazia.
    if hasattr(ast, 'children'):
        for node in ast.children:
            node_info = {
                "type": type(node).__name__,
                "attributes": {}
            }
            # ... (mesmo código da versão anterior)
            # ... (adicionar atributos ao node_info)
            results.append(node_info)
    return results

# Executando o código
if __name__ == "__main__":
    db_path = 'data.db'  # Caminho do banco de dados SQLite

    create_tables(db_path)  # Criar tabelas no banco de dados
    process_php_directory(php_dir, db_path)  # Processar todos os arquivos PHP no diretório

    print("Processamento concluído.")