import os
import re
import sqlite3

def deletar_banco_de_dados(nome_arquivo_db):
    """Deleta um arquivo de banco de dados SQLite."""
    if os.path.exists(nome_arquivo_db):
        try:
            os.remove(nome_arquivo_db)
            print(f"Arquivo de banco de dados '{nome_arquivo_db}' deletado com sucesso.")
        except OSError as e:
            print(f"Erro ao deletar o arquivo: {e}")
    else:
        print(f"O arquivo de banco de dados '{nome_arquivo_db}' não existe.")

def remover_comentarios(conteudo):
    """Remove comentários de um bloco de texto CSS, incluindo comentários multi-linha."""
    
    i = 0
    while i < len(conteudo):
        
        # Procurando por comentário de bloco /* ... */
        inicio_comentario = conteudo.find("/*", i)
        if inicio_comentario != -1:
            fim_comentario = conteudo.find("*/", inicio_comentario + 2)
            if fim_comentario != -1:
                conteudo = conteudo[:inicio_comentario] + conteudo[fim_comentario + 2:]
                #Atualiza o índice para não pular caracteres
                i = inicio_comentario
                continue
        i += 1
    
    return conteudo

def extrair_classes_propriedades(conteudo):
    """
    Extrai as classes e suas propriedades do conteúdo CSS.

    Args:
        conteudo (str): O conteúdo CSS como string.

    Returns:
        dict: Dicionário com as classes como chaves e as propriedades como valores.
    """
    classes = {}
    
    with open(arquivo_css, 'r') as arquivo:
        conteudo = remover_comentarios(arquivo.read())

        # Regex para encontrar classes e suas propriedades
        pattern = r'([^{]+)\s*\{([^}]*)\}'
        matches = re.findall(pattern, conteudo)

        for classe, propriedades in matches:
            # Limpa e divide múltiplas classes
            for nome_classe in classe.split(','):
                nome_classe = nome_classe.replace('}','').strip()
                propriedades = propriedades.strip()
                propriedades_split = [prop.strip() for prop in propriedades.split(';') if prop.strip()]

                if nome_classe in classes:
                    classes[nome_classe].extend(propriedades_split)
                else:
                    classes[nome_classe] = propriedades_split

        return classes

def extrair_classes_media(arquivo_css):
    media = {}
    try:
        with open(arquivo_css, 'r', encoding='utf-8') as arquivo:
            conteudo = remover_comentarios(arquivo.read())
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_css}' não encontrado.")
        return media

    pos = 0
    while pos < len(conteudo):
        # Encontra @media
        start_media = conteudo.find('@media', pos)
        if start_media == -1:
            break
        
        end_media = conteudo.find('{', start_media)
        media_tipo = conteudo[start_media + len('@media'):end_media].strip()

        # Encontra o primeiro { e coleta nomes das classes até o próximo {
        start_classes = end_media + 1
        end_classes = conteudo.find('{', start_classes)
        classes_conteudo = conteudo[start_classes:end_classes].strip()

        classes_media = {}
        
        # Coleta as classes
        for linha in classes_conteudo.splitlines():
            linha = linha.strip()
            if linha:  # Ignora linhas vazias
                classes = linha.split(',')
                for classe in classes:
                    classes_media[classe.strip()] = []  # Inicializa com uma lista vazia

        # A partir do segundo {, coleta propriedades
        start_propriedades = end_classes + 1
        end_propriedades = conteudo.find('}', start_propriedades)
        propriedades_conteudo = conteudo[start_propriedades:end_propriedades]

        for linha in propriedades_conteudo.splitlines():
            linha = linha.strip()
            if linha:  # Ignora linhas vazias
                propriedades = linha.split(';')
                for prop in propriedades:
                    prop = prop.strip()
                    if prop:  # Adiciona propriedade se não estiver vazia
                        for classe in classes_media.keys():
                            classes_media[classe].append(prop)

        media[media_tipo] = classes_media
        pos = end_propriedades + 1

    return media  

def criar_tabelas(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Criar tabela styles_classes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS styles_classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,
        media_type TEXT
    )
    ''')

    # Criar tabela styles_classes_properties
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS styles_classes_properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        property_name TEXT,
        FOREIGN KEY (class_id) REFERENCES styles_classes(id)
    )
    ''')

    # Criar tabela styles_classes_properties_values
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS styles_classes_properties_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER,
        value TEXT,
        FOREIGN KEY (property_id) REFERENCES styles_classes_properties(id)
    )
    ''')

     # Cria índice na tabela styles_classes pelo nome da classe
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_styles_classes_class_name ON styles_classes (class_name)")

    # Cria índice na tabela styles_classes pelo tipo de mídia
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_styles_classes_media_type ON styles_classes (media_type)")

    # Cria índice na tabela styles_classes_properties pelo ID da classe
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_styles_classes_properties_class_id ON styles_classes_properties (class_id)")

    # Cria índice na tabela styles_classes_properties pelo nome da propriedade
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_styles_classes_properties_property_name ON styles_classes_properties (property_name)")

    conn.commit()
    conn.close()

def existe_classe(classe, media_tipo):
    cursor.execute("SELECT id FROM styles_classes WHERE class_name = ? AND media_type = ?", (classe, media_tipo))
    return cursor.fetchone()

def existe_propriedade(class_id, propriedade):
    cursor.execute("SELECT id FROM styles_classes_properties WHERE class_id = ? AND property_name = ?", (class_id, propriedade))
    return cursor.fetchone()

def cadastra_propriedades(conn, cursor, propriedades):
     for propriedade in propriedades:
        prop_name, valor = map(str.strip, propriedade.split(':', 1))
        prop_name = prop_name.strip()
        valor = valor.strip()

        if not existe_propriedade(class_id, propriedade):
            cursor.execute("INSERT INTO styles_classes_properties (class_id, property_name) VALUES (?, ?)", (class_id, prop_name))
            conn.commit()
            property_id = cursor.lastrowid
        else:
            property_id = existe_propriedade(class_id, propriedade)[0]

        cursor.execute("INSERT INTO styles_classes_properties_values (property_id, value) VALUES (?, ?)", (property_id, valor))
        conn.commit()

db = 'cms.db'
arquivo_css = 'bootstrap.css'

deletar_banco_de_dados(db)
conn = sqlite3.connect(db)
cursor = conn.cursor()



criar_tabelas(db)

print('Media Classes...')
media = extrair_classes_media(arquivo_css)
for media_tipo, classes_media in media.items():
    for classe, propriedades in classes_media.items():
        print(classe)
        if not existe_classe(classe, media_tipo):
            cursor.execute("INSERT INTO styles_classes (class_name, media_type) VALUES (?, ?)", (classe, media_tipo))
            conn.commit()
            class_id = cursor.lastrowid
        else:
            class_id = existe_classe(classe, media_tipo)[0]

        cadastra_propriedades(conn, cursor, propriedades)

# Classes
print('Classes...')
classes = extrair_classes_propriedades(arquivo_css)
for classe, propriedades in classes.items():
    if not classe.__contains__('@media'):
        media_tipo = None        
        for classe, propriedades in classes.items():
            if not classe.__contains__('@media'):
                print(classe)
                if not existe_classe(classe, media_tipo):
                    cursor.execute("INSERT INTO styles_classes (class_name, media_type) VALUES (?, ?)", (classe, media_tipo))
                    conn.commit()
                    class_id = cursor.lastrowid
                else:
                    class_id = existe_classe(classe, media_tipo)[0]
                
                cadastra_propriedades(conn, cursor, propriedades)

conn.close()