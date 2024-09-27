import json
import os
import sqlite3

# Criação ou conexão ao banco de dados SQLite
conn = sqlite3.connect('files.db')
cursor = conn.cursor()

# Criação das tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS Files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS JsonValues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value TEXT,
    key_id INTEGER,
    file_id INTEGER,
    parent_id INTEGER,
    FOREIGN KEY(key_id) REFERENCES Keys(id),
    FOREIGN KEY(file_id) REFERENCES Files(id),
    FOREIGN KEY(parent_id) REFERENCES JsonValues(id)
)
''')

def process_json(json_data, file_id, parent_id=None):
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            cursor.execute('INSERT OR IGNORE INTO Keys (key) VALUES (?)', (key,))
            key_id = cursor.lastrowid if cursor.lastrowid else cursor.execute('SELECT id FROM Keys WHERE key = ?', (key,)).fetchone()[0]

            # Insere o valor no banco, vinculando-o ao seu pai
            cursor.execute('INSERT INTO JsonValues (key_id, file_id, parent_id) VALUES (?, ?, ?)', (key_id, file_id, parent_id))
            new_id = cursor.lastrowid
            
            if isinstance(value, (dict, list)):
                process_json(value, file_id, new_id)  # Passa o novo ID como parent_id
            else:
                cursor.execute('UPDATE JsonValues SET value = ? WHERE id = ?', (value, new_id))  # Atualiza o valor

    elif isinstance(json_data, list):
        for item in json_data:
            process_json(item, file_id, parent_id)

def main(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                cursor.execute('INSERT OR IGNORE INTO Files (path) VALUES (?)', (file_path,))
                file_id = cursor.lastrowid if cursor.lastrowid else cursor.execute('SELECT id FROM Files WHERE path = ?', (file_path,)).fetchone()[0]

                with open(file_path, 'r') as json_file:
                    json_data = json.load(json_file)
                    process_json(json_data, file_id)
                    break

    conn.commit()

def print_tree(parent_id=None, indent=""):
    cursor.execute('SELECT * FROM JsonValues WHERE parent_id IS ?', (parent_id,))
    values = cursor.fetchall()

    for value in values:
        key_id = value[2]
        cursor.execute('SELECT key FROM Keys WHERE id = ?', (key_id,))
        key = cursor.fetchone()

        if key:
            print(f"{indent}[+]: Key: {key[0]}")
            if value[1] is not None:
                print(f"{indent}\tValue: {value[1]}")
            print_tree(value[0], indent + "\t")  # Passa o ID do filho para buscar subníveis

def print_all_trees():
    cursor.execute('SELECT * FROM Files')
    files = cursor.fetchall()

    for file in files:
        file_id = file[0]
        print(f"File: {file[1]}")
        print_tree()  # Inicia a impressão da árvore com parent_id = None
        print("\n" + "-"*40 + "\n")

# Descomente para processar arquivos
main('output')

# Chame a função após conectar ao banco de dados
print_all_trees()

# Não esqueça de fechar a conexão ao final
conn.close()
