import mysql.connector
import json

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='una'
    )

def get_table_info(cursor):
    tables_info = {}
    cursor.execute("SHOW TABLES")
    
    for (table_name,) in cursor.fetchall():
        print(table_name)
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        # Inicializa as informações da tabela
        table_info = {
            'name': table_name,
            'description': '',  # Campo de descrição da tabela
            'columns': [],
            'primary_keys': [],
            'foreign_keys': [],
            'indexes': [],
        }
        
        for column in columns:
            col_info = {
                'Field': column[0],
                'Type': column[1],
                'Null': column[2],
                'Key': column[3],
                'Default': column[4],
                'Extra': column[5],
                'Description': '',  # Adicione a descrição aqui se disponível
            }
            table_info['columns'].append(col_info)
            
            if col_info['Key'] == 'PRI':
                table_info['primary_keys'].append(col_info['Field'])
            elif col_info['Key'] == 'MUL':
                table_info['foreign_keys'].append(col_info['Field'])
        
        # Obtendo índices
        cursor.execute(f"SHOW INDEX FROM {table_name}")
        for index in cursor.fetchall():
            index_info = {
                'Key_name': index[2],
                'Column_name': index[4],
                'Non_unique': index[1],
            }
            table_info['indexes'].append(index_info)
        
        tables_info[table_name] = table_info
    
    return tables_info

def export_to_json(data, filename='output_database\\una_database_structure.json'):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        tables_info = get_table_info(cursor)
        export_to_json(tables_info)
        print(f"Exportado com sucesso para 'database_info.json'")
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    main()
