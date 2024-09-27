import os
import json
from modules.php.traversers.bf import BFTraverser
from modules.php.base import Visitor
from modules.php.syntax_tree import build_syntax_tree

output_dir = r"output"
php_dir = r"C:\xampp\htdocs\una"
split_path_name = "una_"

class EstruturaEncontrada:
    def __init__(self, tipo, atributos):
        self.tipo = tipo
        self.atributos = atributos

class ColetorEstruturas:
    def __init__(self):
        self.estruturas = []

    def adicionar_estrutura(self, tipo, atributos):
        self.estruturas.append(EstruturaEncontrada(tipo, atributos))

class CustomVisitor(Visitor):
    def __init__(self, coletor_estruturas, extrair_tudo=False):
        super().__init__()
        self.coletor_estruturas = coletor_estruturas
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
        except Exception as e:
            print(f">>>>>>>>>>>>>>>>>>>> [ Erro ] <<<<<<<<<<<<<<<<<<<<<<<< {node}: {e}")

    def format_complex_attribute(self, attr_value, visited=None):
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
                    formatted_dict[key] = self.format_complex_attribute(value, visited.copy())
            self.coletor_estruturas.adicionar_estrutura(type(attr_value).__name__, formatted_dict)
            return formatted_dict
        elif hasattr(attr_value, 'accept'):
            attr_value.accept(self)
            return self.get_node_info(attr_value)
        else:
            return str(attr_value)

def analyze_file(file_path, coletor_estruturas, extrair_tudo=False):
    try:
        s_tree = build_syntax_tree(file_path)
        visitor = CustomVisitor(coletor_estruturas, extrair_tudo) 
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
    relative_path = os.path.relpath(file_path, php_dir).replace(".php", ".json")
    file_name = file_path.replace('//','').replace('\\','_').replace(os.sep, "_").replace(".php", ".json").split(split_path_name, 1)[-1]
    output_file_path = os.path.join(output_dir, file_name)
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(output_file_path, "w", encoding='utf-8') as f:
        json.dump(ast, f, ensure_ascii=False, indent=4)

def extract_from_php(file_path=None, directory_path=None, extrair_tudo=False): 
    os.makedirs(output_dir, exist_ok=True)
    coletor_estruturas = ColetorEstruturas()

    if file_path:
        print(f"Analisando arquivo: {file_path}...")
        ast = analyze_file(file_path, coletor_estruturas, extrair_tudo)
        if ast is not None:
            save_ast_to_json(ast, file_path)

    elif directory_path:
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(".php"):
                    file_path = os.path.join(root, file)
                    print(f"Analisando arquivo: {file_path}...")
                    ast = analyze_file(file_path, coletor_estruturas, extrair_tudo)
                    if ast is not None:
                        save_ast_to_json(ast, file_path)

    print(f"Resultados salvos em arquivos JSON no diretório '{output_dir}'.")

def analisar_ast(arquivo_json):
    try:
        with open(arquivo_json, 'r') as f:
            ast = json.load(f)

        caminho_arquivo = next((item['file_path'] for item in ast if 'file_path' in item), "Caminho do arquivo não encontrado.")
        print(f"Arquivo: {caminho_arquivo}\n")

        for i, no in enumerate(ast):
            tipo_no = no.get('type', 'Tipo Desconhecido')
            atributos = no.get('attributes', {})
            print(f"Nó {i + 1}:")
            print(f"  Tipo: {tipo_no}")
            for chave, valor in atributos.items():
                print(f"  {chave}: {valor}")
            print("-" * 20)  

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado: {arquivo_json}")
    except json.JSONDecodeError:
        print(f"Erro: Arquivo JSON inválido: {arquivo_json}")

# Exemplo de chamada
#extract_from_php(file_path='caminho/do/seu/arquivo.php')
# ou
extract_from_php(directory_path=php_dir)