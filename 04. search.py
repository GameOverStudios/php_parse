import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('files.db')
cursor = conn.cursor()

# Função para pesquisar por chave específica e retornar o arquivo relacionado
def search_by_key(key_name):
    cursor.execute('''
        SELECT jv.id, f.path, k.key, jv.value, jv.parent_id
        FROM JsonValues jv
        JOIN Keys k ON jv.key_id = k.id
        JOIN Files f ON jv.file_id = f.id
        WHERE k.key = ?
    ''', (key_name,))
    
    results = cursor.fetchall()
    for row in results:
        print(f"ID: {row[0]}, File: {row[1]}, Key: {row[2]}, Value: {row[3]}, Parent ID: {row[4]}")

# Função para buscar por valor específico e retornar o arquivo relacionado
def search_by_value(value):
    cursor.execute('''
        SELECT jv.id, f.path, k.key, jv.value, jv.parent_id
        FROM JsonValues jv
        JOIN Keys k ON jv.key_id = k.id
        JOIN Files f ON jv.file_id = f.id
        WHERE jv.value = ?
    ''', (value,))
    
    results = cursor.fetchall()
    for row in results:
        print(f"ID: {row[0]}, File: {row[1]}, Key: {row[2]}, Value: {row[3]}, Parent ID: {row[4]}")

# Função para buscar por ID de pai e retornar o arquivo relacionado
def search_by_parent(parent_id):
    cursor.execute('''
        SELECT jv.id, f.path, k.key, jv.value, jv.parent_id
        FROM JsonValues jv
        JOIN Keys k ON jv.key_id = k.id
        JOIN Files f ON jv.file_id = f.id
        WHERE jv.parent_id = ?
    ''', (parent_id,))
    
    results = cursor.fetchall()
    for row in results:
        print(f"ID: {row[0]}, File: {row[1]}, Key: {row[2]}, Value: {row[3]}, Parent ID: {row[4]}")

# Exemplo de uso das funções
print("Pesquisando pela chave 'end':")
search_by_key('end')

print("\nPesquisando por valor 'program':")
search_by_value('program')

print("\nPesquisando por ID de pai 1:")
search_by_parent(1)

# Fechar conexão ao banco de dados
conn.close()
