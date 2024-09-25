import os
import json
import sqlite3
from src.modules.php.traversers.bf import BFTraverser
from src.modules.php.base import Visitor
from src.modules.php.syntax_tree import build_syntax_tree

output_dir = "output"
path_php_dir = "C:\\Users\\nepom\\Downloads\\una-master\\inc\\classes"

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
        self.conn = conn
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

            if self.extrair_tudo:
                for attr_name in dir(node):
                    if not attr_name.startswith('_'):
                        attr_value = getattr(node, attr_name)
                        node_info["attributes"][attr_name] = self.format_complex_attribute(attr_value)
            else:
                for attr_name in self.relevant_attributes:
                    if hasattr(node, attr_name):
                        attr_value = getattr(node, attr_name)
                        node_info["attributes"][attr_name] = self.format_complex_attribute(attr_value)

            self.results.append(node_info)
            self.inserir_dados_sqlite(node_info["type"], node_info["attributes"])

        except Exception as e:
            print(f">>>>>>>>>>>>>>>>>>>> [ Erro ] <<<<<<<<<<<<<<<<<<<<<<<< {node}: {e}")

    def inserir_dados_sqlite(self, nome_tabela, dados):
        cursor = self.conn.cursor()

        # Verifica se a tabela já existe, caso contrário, cria a tabela
        colunas = ', '.join([f'"{coluna.replace("default", "default_value").replace("end", "end_value")}" TEXT' for coluna in dados.keys()])
        try:
            cursor.execute(f'CREATE TABLE IF NOT EXISTS "{nome_tabela}" ({colunas})')
            self.conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Erro ao criar tabela '{nome_tabela}': {e}")
            return

        placeholders = ', '.join(['?' for _ in dados.keys()])
        try:
            valores_formatados = [json.dumps(valor) if isinstance(valor, (list, dict)) else str(valor) for valor in dados.values()]
            cursor.execute(f'INSERT INTO "{nome_tabela}" ({colunas}) VALUES ({placeholders})', tuple(valores_formatados))
            self.conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Erro ao inserir dados na tabela '{nome_tabela}': {e}")
        except Exception as e:
            print(f"Erro geral ao inserir dados no SQLite: {e}")

    def format_complex_attribute(self, attr_value, visited=None):
        if visited is None:
            visited = set()

        if id(attr_value) in visited:
            return f"<Referência recursiva a {type(attr_value).__name__}>"
        visited.add(id(attr_value))

        if isinstance(attr_value, (list, tuple)):
            return [self.format_complex_attribute(item, visited.copy()) for item in attr_value]
        elif isinstance(attr_value, dict):
            return {key: self.format_complex_attribute(value, visited.copy()) for key, value in attr_value.items()}
        elif hasattr(attr_value, '__dict__'):
            formatted_dict = {}
            for key, value in attr_value.__dict__.items():
                if not key.startswith('_'):
                    if key == 'default':
                        key = 'default_value'
                    if key == 'end':
                        key = 'end_value'
                    formatted_dict[key] = self.format_complex_attribute(value, visited.copy())
            return formatted_dict
        elif hasattr(attr_value, 'accept'):
            attr_value.accept(self)
            return self.get_node_info(attr_value)

        return str(attr_value)

def analyze_file(file_path, coletor_estruturas, conn, extrair_tudo=False):
    print(f"Analisando arquivo: {file_path}")
    try:
        s_tree = build_syntax_tree(file_path)
        visitor = CustomVisitor(coletor_estruturas, conn, extrair_tudo) 
        traverser = BFTraverser(s_tree)
        traverser.register_visitor(visitor)
        traverser.traverse()
        return visitor.results
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except Exception as e:
        print(f"Erro ao analisar o arquivo {file_path}: {e}")
    return None

def save_ast_to_json(ast, file_path):
    relative_path = os.path.relpath(file_path, path_php_dir).replace(".php", ".json")
    file_name = relative_path.replace(os.sep, "_")
    output_file_path = os.path.join(output_dir, file_name)

    with open(output_file_path, "w") as f:
        json.dump(ast, f, indent=4)
        print(f"AST salva em: {output_file_path}")

def extract_from_php(extrair_tudo=False):
    os.makedirs(output_dir, exist_ok=True)
    coletor_estruturas = ColetorEstruturas()
    conn = sqlite3.connect("ast_database.db")

    for root, _, files in os.walk(path_php_dir):
        for file in files:
            if file.endswith(".php"):
                file_path = os.path.join(root, file)
                print('--------------------------------------------------------------------------------------------')
                print(file)
                print('--------------------------------------------------------------------------------------------')
                ast = analyze_file(file_path, coletor_estruturas, conn, extrair_tudo)
                if ast is not None:
                    save_ast_to_json(ast, file_path)

    conn.close()
    print(f"Resultados salvos em arquivos JSON no diretório '{output_dir}'.")

extract_from_php(extrair_tudo=True)