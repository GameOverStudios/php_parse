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
    FOREIGN KEY(key_id) REFERENCES Keys(id),
    FOREIGN KEY(file_id) REFERENCES Files(id)
)
''')

def process_json(json_data, file_id):
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            cursor.execute('INSERT OR IGNORE INTO Keys (key) VALUES (?)', (key,))
            key_id = cursor.lastrowid if cursor.lastrowid else cursor.execute('SELECT id FROM Keys WHERE key = ?', (key,)).fetchone()[0]

            if isinstance(value, (dict, list)):
                process_json(value, file_id)
            else:
                cursor.execute('INSERT INTO JsonValues (value, key_id, file_id) VALUES (?, ?, ?)', (value, key_id, file_id))
    elif isinstance(json_data, list):
        for item in json_data:
            process_json(item, file_id)

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
    conn.close()

# Alterar o caminho do diretório conforme necessário
main('output')
