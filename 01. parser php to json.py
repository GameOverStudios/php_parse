import os
import json
import sqlite3
import shutil
from modules.php.traversers.bf import BFTraverser
from modules.php.base import Visitor
from modules.php.syntax_tree import build_syntax_tree

output_dir = r"output"
php_dir = r"C:\Users\nepom\Downloads\una-master"
end_directory_path_split = 'master_'
database = 'una_cms.db'

class EstruturaEncontrada:
    def __init__(self, tipo, atributos):
        self.tipo = tipo
        self.atributos = atributos

class ColetorEstruturas:
    def __init__(self):
        self.estruturas = []

    def adicionar_estrutura(self, tipo, atributos):
        self.estruturas.append(EstruturaEncontrada(tipo, atributos))

    def obter_estruturas_por_tipo(self, tipo):
        return [estrutura for estrutura in self.estruturas if estrutura.tipo == tipo]

class CustomVisitor(Visitor):
    def __init__(self, coletor_estruturas, conn, extrair_tudo=False):
        super().__init__()
        self.coletor_estruturas = coletor_estruturas
        self.conn = conn  # Armazena a conexão com o banco de dados
        self.visited = set()
        self.results = []
        self.extrair_tudo = extrair_tudo
        self.relevant_attributes = ["name", "value", "lineno", "col_offset", "args", "expr", "left", "right", "attributes", "tipo", "params", "modifier"]

    def visit(self, node):
        try:
            if id(node) in self.visited:
                return
            self.visited.add(id(node))

            node_info = {
                "type": type(node).__name__,
                "attributes": {}
            }

            if self.extrair_tudo:  # Extrair todas as propriedades
                for attr_name in dir(node):
                    if not attr_name.startswith('_'):
                        attr_value = getattr(node, attr_name)
                        node_info["attributes"][attr_name] = self.format_complex_attribute(attr_value)
            else:  # Extrair apenas atributos relevantes
                for attr_name in self.relevant_attributes:
                    if hasattr(node, attr_name):  # Verifica se o nó possui o atributo
                        attr_value = getattr(node, attr_name)
                        node_info["attributes"][attr_name] = self.format_complex_attribute(attr_value)
            self.results.append(node_info)
        except Exception as e:
            print(f">>>>>>>>>>>>>>>>>>>> [ Erro ] <<<<<<<<<<<<<<<<<<<<<<<< {node}: {e}")

    def get_node_info(self, node):
        if id(node) in self.visited:
            return {"type": type(node).__name__, "id": id(node)}
        return self.results[-1] if self.results else None

    def inserir_dados_sqlite(self, nome_tabela, dados):
        cursor = self.conn.cursor()

        colunas = ', '.join([f'"{coluna.replace("default", "default_value").replace("end", "end_value")}"' for coluna in dados.keys()])
        placeholders = ', '.join(['?' for _ in dados.keys()])

        try:
            # Converter listas e dicionários em strings JSON:
            valores_formatados = [json.dumps(valor) if isinstance(valor, (list, dict)) else valor for valor in dados.values()]

            cursor.execute(f'INSERT INTO "{nome_tabela}" ({colunas}) VALUES ({placeholders})', tuple(valores_formatados))
            self.conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Erro ao inserir dados na tabela '{nome_tabela}': {e}")

    def format_complex_attribute(self, attr_value, visited=None):
        """Formata qualquer tipo de atributo recursivamente, 
           protegendo contra loops infinitos.
        """
        if visited is None:
            visited = set()

        if id(attr_value) in visited:
            return f"<Referência recursiva a {type(attr_value).__name__}>"
        visited.add(id(attr_value))

        if isinstance(attr_value, (list, tuple)):
            return [self.format_complex_attribute(item, visited.copy()) for item in attr_value]
        elif hasattr(attr_value, '__dict__'):
            formatted_dict = {}
            for key, value in attr_value.__dict__.items():
                if not key.startswith('_'):
                    if key == 'default':
                        key = 'default_value'
                    if key == 'end':  # Verifica se a chave é 'end'
                        key = 'end_value'  # Renomeia para 'end_value'
                    formatted_dict[key] = self.format_complex_attribute(value, visited.copy())
            self.coletor_estruturas.adicionar_estrutura(type(attr_value).__name__, formatted_dict)
            #criar_tabelas_sqlite(self.coletor_estruturas, "ast_database.db")  # Chama a função para criar a tabela aqui
            #self.inserir_dados_sqlite(type(attr_value).__name__, formatted_dict)  # Chama a função para inserir dados no SQLite
            return formatted_dict
        elif hasattr(attr_value, 'accept'):
            attr_value.accept(self)
            return self.get_node_info(attr_value)
        else:
            return str(attr_value)

def analyze_file(file_path, coletor_estruturas, conn, extrair_tudo=False):
    """Analisa um único arquivo PHP e retorna a AST como um dicionário."""
    try:
        s_tree = build_syntax_tree(file_path)
        visitor = CustomVisitor(coletor_estruturas, conn, extrair_tudo) 
        traverser = BFTraverser(s_tree)
        traverser.register_visitor(visitor)
        traverser.traverse()
        results = visitor.results
        results.insert(0, {"file_path": file_path})
        return results
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except Exception as e:
        print(f"Erro ao analisar o arquivo {file_path}: {e}")
    return None

def save_ast_to_json(ast, file_path):
    # Obtém o caminho relativo do arquivo PHP e troca a extensão para .json
    relative_path = os.path.relpath(file_path, php_dir).replace(".php", ".json")
    
    # Substitui os separadores de diretório por '_'
    file_name = file_path.replace('//','').replace('\\','_').replace(os.sep, "_").replace(".php", ".json").split(end_directory_path_split, 1)[-1]
    
    # Cria o caminho completo para o arquivo JSON
    output_file_path = os.path.join(output_dir, file_name)

    # Garante que o diretório de saída exista
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(output_file_path, "w", encoding='utf-8') as f:
        json.dump(ast, f, ensure_ascii=False, indent=4)

def criar_tabelas_sqlite(coletor_estruturas, nome_banco):
    conn = sqlite3.connect(nome_banco)
    cursor = conn.cursor()

    nomes_tabelas = set()  # Conjunto para armazenar os nomes das tabelas

    for estrutura in coletor_estruturas.estruturas:
        nomes_tabelas.add(estrutura.tipo)  # Adiciona o nome da tabela ao conjunto

    for nome_tabela in nomes_tabelas:  # Itera sobre o conjunto de nomes de tabelas
        nome_tabela_escapado = f'"{nome_tabela}"'
        
        # Obtém os atributos da primeira estrutura com esse tipo
        atributos = next((e.atributos for e in coletor_estruturas.estruturas if e.tipo == nome_tabela), {})

        colunas = ', '.join([
            f'"{nome_coluna.replace("default", "default_value").replace("end", "end_value")}" TEXT' 
            for nome_coluna in atributos.keys()
        ]) 

        print({nome_tabela_escapado})
        print({colunas})
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {nome_tabela_escapado} ({colunas})")

    conn.commit()
    conn.close()

def extract_from_php(extrair_tudo=False): 
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    coletor_estruturas = ColetorEstruturas()

    conn = sqlite3.connect("ast_database.db")  # Cria a conexão aqui

    for root, _, files in os.walk(php_dir):
        for file in files:
            if file.endswith(".php"):
                print(file+'...')
                file_path = os.path.join(root, file)
                ast = analyze_file(file_path, coletor_estruturas, conn, extrair_tudo)  # Passa a conexão aqui
                if ast is not None:
                    save_ast_to_json(ast, file_path)

    conn.close()  # Fecha a conexão quando terminar

    print(f"Resultados salvos em arquivos JSON no diretório '{output_dir}'.")

def analisar_ast(arquivo_json):
    """Analisa um arquivo JSON contendo a AST e imprime 
       informações relevantes, adaptando-se a diferentes estruturas.
    """

    try:
        with open(arquivo_json, 'r') as f:
            ast = json.load(f)

        # Extraindo o caminho do arquivo
        caminho_arquivo = next(
            (item['file_path'] for item in ast if 'file_path' in item),
            "Caminho do arquivo não encontrado."
        )
        print(f"Arquivo: {caminho_arquivo}\n")

        # Analisando cada nó da AST
        for i, no in enumerate(ast):
            tipo_no = no.get('type', 'Tipo Desconhecido')
            atributos = no.get('attributes', {})
            print(f"Nó {i + 1}:")
            print(f"  Tipo: {tipo_no}")
            for chave, valor in atributos.items():
                print(f"  {chave}: {valor}")
            print("-" * 20)  # Separador visual

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado: {arquivo_json}")
    except json.JSONDecodeError:
        print(f"Erro: Arquivo JSON inválido: {arquivo_json}")

###--->

def create_tables(conn, cursor):

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE
        )
    ''')
    conn.commit()

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_file_path ON files(file_path)
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS virtualtables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            type TEXT,
            lineno INTEGER,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    ''')
    conn.commit()

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_virtualtables ON virtualtables(file_id, type, lineno)
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS virtualfields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            virtualtable_id INTEGER,
            parent_id INTEGER,
            name TEXT,
            value TEXT,
            type TEXT,  -- Adicionar a coluna type
            FOREIGN KEY (virtualtable_id) REFERENCES virtualtables(id),
            FOREIGN KEY (parent_id) REFERENCES virtualfields(id)
        )
    ''')
    conn.commit()

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_virtualfields ON virtualfields(virtualtable_id, parent_id, name, value)
    ''')
    conn.commit()

def insert_json(conn, cursor, json_obj, file_id=None, virtualtable_id=None, parent_id=None, level=0):
    # Inserir o caminho do arquivo, se não existir
    if 'file_path' in json_obj:
        cursor.execute('SELECT id FROM files WHERE file_path = ?', (json_obj['file_path'],))
        row = cursor.fetchone()
        if row:
            file_id = row[0]
        else:
            cursor.execute('INSERT INTO files (file_path) VALUES (?)', (json_obj['file_path'],))
            file_id = cursor.lastrowid
    
    # No primeiro nível, o campo `type` representa uma tabela virtual
    if 'type' in json_obj and level == 0:
        lineno = json_obj.get('attributes', {}).get('lineno', None)
        cursor.execute('SELECT id FROM virtualtables WHERE file_id = ? AND type = ? AND lineno = ?', 
                       (file_id, json_obj['type'], lineno))
        row = cursor.fetchone()
        if row:
            virtualtable_id = row[0]
        else:
            cursor.execute('INSERT INTO virtualtables (file_id, type, lineno) VALUES (?, ?, ?)', 
                           (file_id, json_obj['type'], lineno))
            virtualtable_id = cursor.lastrowid
        
        # Processar recursivamente os atributos de `attributes`
        for key, value in json_obj.get('attributes', {}).items():
            if isinstance(value, dict):
                insert_json(conn, cursor, value, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=None, level=level+1)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    insert_json(conn, cursor, item, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=None, level=level+1)
            else:
                cursor.execute('SELECT id FROM virtualfields WHERE virtualtable_id = ? AND name = ? AND value = ?', 
                               (virtualtable_id, key, str(value)))
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO virtualfields (virtualtable_id, parent_id, name, value) VALUES (?, ?, ?, ?)', 
                                   (virtualtable_id, None, key, str(value)))

    # Nos subníveis, o campo `type` é tratado como coluna em `virtualfields`
    if 'type' in json_obj and level > 0:
        lineno = json_obj.get('lineno', None)
        cursor.execute('SELECT id FROM virtualfields WHERE virtualtable_id = ? AND name = ? AND value = ?', 
                       (virtualtable_id, 'lineno', str(lineno)))
        if row := cursor.fetchone():
            parent_id = row[0]
        
        # Processar os campos e valores recursivamente
        for key, value in json_obj.items():
            if isinstance(value, dict):
                insert_json(conn, cursor, value, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=parent_id, level=level+1)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    insert_json(conn, cursor, item, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=parent_id, level=level+1)
            else:
                cursor.execute('SELECT id FROM virtualfields WHERE virtualtable_id = ? AND name = ? AND value = ?', 
                               (virtualtable_id, key, str(value)))
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO virtualfields (virtualtable_id, parent_id, name, value, type) VALUES (?, ?, ?, ?, ?)', 
                                   (virtualtable_id, parent_id, key, str(value), json_obj.get('type', None)))

def fetch_file_data(cursor, file_path):
    cursor.execute('''
        SELECT f.file_path, vt.type, vt.lineno, vf.name, vf.value, vf.type
        FROM files f
        JOIN virtualtables vt ON f.id = vt.file_id
        JOIN virtualfields vf ON vt.id = vf.virtualtable_id
        WHERE f.file_path like "%"+file+"%"
    ''', (file_path,))
    
    results = cursor.fetchall()
    for row in results:
        print(f"File: {row[0]}, Table Type: {row[1]}, Line: {row[2]}, Field: {row[3]}, Value: {row[4]}, Sub-Type: {row[5]}")

def insert_json(conn, cursor, json_obj, file_id=None, virtualtable_id=None, parent_id=None, level=0):
    # Inserir o caminho do arquivo, se não existir
    if 'file_path' in json_obj:
        cursor.execute('SELECT id FROM files WHERE file_path = ?', (json_obj['file_path'],))
        row = cursor.fetchone()
        if row:
            file_id = row[0]
        else:
            cursor.execute('INSERT INTO files (file_path) VALUES (?)', (json_obj['file_path'],))
            file_id = cursor.lastrowid
    
    # No primeiro nível, o campo `type` representa uma tabela virtual
    if 'type' in json_obj and level == 0:
        lineno = json_obj.get('attributes', {}).get('lineno', None)
        cursor.execute('SELECT id FROM virtualtables WHERE file_id = ? AND type = ? AND lineno = ?', 
                       (file_id, json_obj['type'], lineno))
        row = cursor.fetchone()
        if row:
            virtualtable_id = row[0]
        else:
            cursor.execute('INSERT INTO virtualtables (file_id, type, lineno) VALUES (?, ?, ?)', 
                           (file_id, json_obj['type'], lineno))
            virtualtable_id = cursor.lastrowid
        
        # Processar recursivamente os atributos de `attributes`
        for key, value in json_obj.get('attributes', {}).items():
            if isinstance(value, dict):
                insert_json(conn, cursor, value, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=None, level=level+1)
            elif isinstance(value, list):
                for item in value:
                    insert_json(conn, cursor, item, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=None, level=level+1)
            else:
                cursor.execute('SELECT id FROM virtualfields WHERE virtualtable_id = ? AND name = ? AND value = ?', 
                               (virtualtable_id, key, str(value)))
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO virtualfields (virtualtable_id, parent_id, name, value) VALUES (?, ?, ?, ?)', 
                                   (virtualtable_id, None, key, str(value)))

    # Nos subníveis, o campo `type` é tratado como coluna em `virtualfields`
    if 'type' in json_obj and level > 0:
        lineno = json_obj.get('lineno', None)
        cursor.execute('SELECT id FROM virtualfields WHERE virtualtable_id = ? AND name = ? AND value = ?', 
                       (virtualtable_id, 'lineno', str(lineno)))
        if row := cursor.fetchone():
            parent_id = row[0]
        
        # Processar os campos e valores recursivamente
        for key, value in json_obj.items():
            if isinstance(value, dict):
                insert_json(conn, cursor, value, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=parent_id, level=level+1)
            elif isinstance(value, list):
                for item in value:
                    insert_json(conn, cursor, item, file_id=file_id, virtualtable_id=virtualtable_id, parent_id=parent_id, level=level+1)
            else:
                cursor.execute('SELECT id FROM virtualfields WHERE virtualtable_id = ? AND name = ? AND value = ?', 
                               (virtualtable_id, key, str(value)))
                if not cursor.fetchone():
                    cursor.execute('INSERT INTO virtualfields (virtualtable_id, parent_id, name, value, type) VALUES (?, ?, ?, ?, ?)', 
                                   (virtualtable_id, parent_id, key, str(value), json_obj.get('type', None)))

conn = sqlite3.connect('virtual.db')
cursor = conn.cursor()

#extract_from_php(extrair_tudo=False)
create_tables(conn, cursor)

for filename in os.listdir(output_dir):
    if filename.endswith('.json'):
        file_path = os.path.join(output_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                print(file_path)
                
                #if isinstance(json_data, list):
                #    for item in json_data:
                #        insert_json(conn, cursor, item)  # Chama a função para inserir os dados

                print(fetch_file_data(cursor, file_path))
                break
        except:
            print("****** ERROR::::> " + file_path)

conn.commit()
conn.close()