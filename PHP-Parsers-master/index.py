import os
import json
import sqlite3
from compiler.php.phplex import PHPLexer  # Caminho corrigido
from compiler.php.phpparse import PHPParser  # Caminho corrigido
from modules.php.traversers.bf import BFTraverser
from modules.php.base import Visitor
from modules.php.syntax_tree import build_syntax_tree, SyntaxTree

# Classe de visitante para imprimir os nós da AST
class MyVisitor(Visitor):  # Herda da classe Visitor do projeto
    def visit(self, node):
        print(f"{type(node).__name__}: {getattr(node, 'name', '')}")

# Caminho para o arquivo PHP a ser analisado
file_path = r"C:\Users\nepom\Downloads\una-master\inc\classes\BxDolMenu.php"

# Cria o lexer e o parser do projeto PHP-Parsers
lexer = PHPLexer()
parser = PHPParser()

# Converte o código PHP em uma AST
with open(file_path, "r") as f:
    php_code = f.read()
parser.parse(php_code, lexer=lexer)
ast_root = parser.root

# Cria a árvore sintática
syntax_tree = SyntaxTree(ast_root)

# Cria o percorredor da AST
traverser = BFTraverser(syntax_tree)

# Registra o visitante
visitor = MyVisitor()
traverser.register_visitor(visitor)

# Percorre a AST
traverser.traverse()