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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS styles_themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        theme TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS styles_themes_parameters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        theme_id INTEGER,
        parameter TEXT,
        value TEXT,
        FOREIGN KEY (theme_id) REFERENCES styles_themes(id)
    )
    ''')


     #Criar tabela styles_classes_componentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS styles_classes_componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER,
            component_id INTEGER,
            FOREIGN KEY (class_id) REFERENCES styles_classes(id),
            FOREIGN KEY (component_id) REFERENCES BootstrapComponents(id)
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

def criar_temas(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute ('INSERT OR IGNORE INTO styles_themes (theme) VALUES("light")')
    cursor.execute ('INSERT OR IGNORE INTO styles_themes (theme) VALUES("dark")')

    cursor.execute (
    '''
    INSERT OR IGNORE INTO styles_themes_parameters (theme_id, parameter, value) VALUES
        (1,'bs-blue', '#0d6efd'),
        (1,'bs-indigo', '#6610f2'),
        (1,'bs-purple', '#6f42c1'),
        (1,'bs-pink', '#d63384'),
        (1,'bs-red', '#dc3545'),
        (1,'bs-orange', '#fd7e14'),
        (1,'bs-yellow', '#ffc107'),
        (1,'bs-green', '#198754'),
        (1,'bs-teal', '#20c997'),
        (1,'bs-cyan', '#0dcaf0'),
        (1,'bs-black', '#000'),
        (1,'bs-white', '#fff'),
        (1,'bs-gray', '#6c757d'),
        (1,'bs-gray-dark', '#343a40'),
        (1,'bs-gray-100', '#f8f9fa'),
        (1,'bs-gray-200', '#e9ecef'),
        (1,'bs-gray-300', '#dee2e6'),
        (1,'bs-gray-400', '#ced4da'),
        (1,'bs-gray-500', '#adb5bd'),
        (1,'bs-gray-600', '#6c757d'),
        (1,'bs-gray-700', '#495057'),
        (1,'bs-gray-800', '#343a40'),
        (1,'bs-gray-900', '#212529'),
        (1,'bs-primary', '#0d6efd'),
        (1,'bs-secondary', '#6c757d'),
        (1,'bs-success', '#198754'),
        (1,'bs-info', '#0dcaf0'),
        (1,'bs-warning', '#ffc107'),
        (1,'bs-danger', '#dc3545'),
        (1,'bs-light', '#f8f9fa'),
        (1,'bs-dark', '#212529'),
        (1,'bs-primary-rgb', '13, 110, 253'),
        (1,'bs-secondary-rgb', '108, 117, 125'),
        (1,'bs-success-rgb', '25, 135, 84'),
        (1,'bs-info-rgb', '13, 202, 240'),
        (1,'bs-warning-rgb', '255, 193, 7'),
        (1,'bs-danger-rgb', '220, 53, 69'),
        (1,'bs-light-rgb', '248, 249, 250'),
        (1,'bs-dark-rgb', '33, 37, 41'),
        (1,'bs-primary-text-emphasis', '#052c65'),
        (1,'bs-secondary-text-emphasis', '#2b2f32'),
        (1,'bs-success-text-emphasis', '#0a3622'),
        (1,'bs-info-text-emphasis', '#055160'),
        (1,'bs-warning-text-emphasis', '#664d03'),
        (1,'bs-danger-text-emphasis', '#58151c'),
        (1,'bs-light-text-emphasis', '#495057'),
        (1,'bs-dark-text-emphasis', '#495057'),
        (1,'bs-primary-bg-subtle', '#cfe2ff'),
        (1,'bs-secondary-bg-subtle', '#e2e3e5'),
        (1,'bs-success-bg-subtle', '#d1e7dd'),
        (1,'bs-info-bg-subtle', '#cff4fc'),
        (1,'bs-warning-bg-subtle', '#fff3cd'),
        (1,'bs-danger-bg-subtle', '#f8d7da'),
        (1,'bs-light-bg-subtle', '#fcfcfd'),
        (1,'bs-dark-bg-subtle', '#ced4da'),
        (1,'bs-primary-border-subtle', '#9ec5fe'),
        (1,'bs-secondary-border-subtle', '#c4c8cb'),
        (1,'bs-success-border-subtle', '#a3cfbb'),
        (1,'bs-info-border-subtle', '#9eeaf9'),
        (1,'bs-warning-border-subtle', '#ffe69c'),
        (1,'bs-danger-border-subtle', '#f1aeb5'),
        (1,'bs-light-border-subtle', '#e9ecef'),
        (1,'bs-dark-border-subtle', '#adb5bd'),
        (1,'bs-white-rgb', '255, 255, 255'),
        (1,'bs-black-rgb', '0, 0, 0'),
        (1,'bs-font-sans-serif', 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"'),
        (1,'bs-font-monospace', 'SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace'),
        (1,'bs-gradient', 'linear-gradient(180deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0))'),
        (1,'bs-body-font-family', 'var(--bs-font-sans-serif)'),
        (1,'bs-body-font-size', '1rem'),
        (1,'bs-body-font-weight', '400'),
        (1,'bs-body-line-height', '1.5'),
        (1,'bs-body-color', '#212529'),
        (1,'bs-body-color-rgb', '33, 37, 41'),
        (1,'bs-body-bg', '#fff'),
        (1,'bs-body-bg-rgb', '255, 255, 255'),
        (1,'bs-emphasis-color', '#000'),
        (1,'bs-emphasis-color-rgb', '0, 0, 0'),
        (1,'bs-secondary-color', 'rgba(33, 37, 41, 0.75)'),
        (1,'bs-secondary-color-rgb', '33, 37, 41'),
        (1,'bs-secondary-bg', '#e9ecef'),
        (1,'bs-secondary-bg-rgb', '233, 236, 239'),
        (1,'bs-tertiary-color', 'rgba(33, 37, 41, 0.5)'),
        (1,'bs-tertiary-color-rgb', '33, 37, 41'),
        (1,'bs-tertiary-bg', '#f8f9fa'),
        (1,'bs-tertiary-bg-rgb', '248, 249, 250'),
        (1,'bs-heading-color', 'inherit'),
        (1,'bs-link-color', '#0d6efd'),
        (1,'bs-link-color-rgb', '13, 110, 253'),
        (1,'bs-link-decoration', 'underline'),
        (1,'bs-link-hover-color', '#0a58ca'),
        (1,'bs-link-hover-color-rgb', '10, 88, 202'),
        (1,'bs-code-color', '#d63384'),
        (1,'bs-highlight-color', '#212529'),
        (1,'bs-highlight-bg', '#fff3cd'),
        (1,'bs-border-width', '1px'),
        (1,'bs-border-style', 'solid'),
        (1,'bs-border-color', '#dee2e6'),
        (1,'bs-border-color-translucent', 'rgba(0, 0, 0, 0.175)'),
        (1,'bs-border-radius', '0.375rem'),
        (1,'bs-border-radius-sm', '0.25rem'),
        (1,'bs-border-radius-lg', '0.5rem'),
        (1,'bs-border-radius-xl', '1rem'),
        (1,'bs-border-radius-xxl', '2rem'),
        (1,'bs-border-radius-2xl', 'var(--bs-border-radius-xxl)'),
        (1,'bs-border-radius-pill', '50rem'),
        (1,'bs-box-shadow', '0 0.5rem 1rem rgba(0, 0, 0, 0.15)'),
        (1,'bs-box-shadow-sm', '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)'),
        (1,'bs-box-shadow-lg', '0 1rem 3rem rgba(0, 0, 0, 0.175)'),
        (1,'bs-box-shadow-inset', 'inset 0 1px 2px rgba(0, 0, 0, 0.075)'),
        (1,'bs-focus-ring-width', '0.25rem'),
        (1,'bs-focus-ring-opacity', '0.25'),
        (1,'bs-focus-ring-color', 'rgba(13, 110, 253, 0.25)'),
        (1,'bs-form-valid-color', '#198754'),
        (1,'bs-form-valid-border-color', '#198754'),
        (1,'bs-form-invalid-color', '#dc3545'),
        (1,'bs-form-invalid-border-color', '#dc3545');
    ''')

    cursor.execute (
    '''    
    INSERT OR IGNORE INTO styles_themes_parameters (theme_id, parameter, value) VALUES
        (2, '--bs-body-color', '#dee2e6'),
        (2, '--bs-body-color-rgb', '222, 226, 230'),
        (2, '--bs-body-bg', '#212529'),
        (2, '--bs-body-bg-rgb', '33, 37, 41'),
        (2, '--bs-emphasis-color', '#fff'),
        (2, '--bs-emphasis-color-rgb', '255, 255, 255'),
        (2, '--bs-secondary-color', 'rgba(222, 226, 230, 0.75)'),
        (2, '--bs-secondary-color-rgb', '222, 226, 230'),
        (2, '--bs-secondary-bg', '#343a40'),
        (2, '--bs-secondary-bg-rgb', '52, 58, 64'),
        (2, '--bs-tertiary-color', 'rgba(222, 226, 230, 0.5)'),
        (2, '--bs-tertiary-color-rgb', '222, 226, 230'),
        (2, '--bs-tertiary-bg', '#2b3035'),
        (2, '--bs-tertiary-bg-rgb', '43, 48, 53'),
        (2, '--bs-primary-text-emphasis', '#6ea8fe'),
        (2, '--bs-secondary-text-emphasis', '#a7acb1'),
        (2, '--bs-success-text-emphasis', '#75b798'),
        (2, '--bs-info-text-emphasis', '#6edff6'),
        (2, '--bs-warning-text-emphasis', '#ffda6a'),
        (2, '--bs-danger-text-emphasis', '#ea868f'),
        (2, '--bs-light-text-emphasis', '#f8f9fa'),
        (2, '--bs-dark-text-emphasis', '#dee2e6'),
        (2, '--bs-primary-bg-subtle', '#031633'),
        (2, '--bs-secondary-bg-subtle', '#161719'),
        (2, '--bs-success-bg-subtle', '#051b11'),
        (2, '--bs-info-bg-subtle', '#032830'),
        (2, '--bs-warning-bg-subtle', '#332701'),
        (2, '--bs-danger-bg-subtle', '#2c0b0e'),
        (2, '--bs-light-bg-subtle', '#343a40'),
        (2, '--bs-dark-bg-subtle', '#1a1d20'),
        (2, '--bs-primary-border-subtle', '#084298'),
        (2, '--bs-secondary-border-subtle', '#41464b'),
        (2, '--bs-success-border-subtle', '#0f5132'),
        (2, '--bs-info-border-subtle', '#087990'),
        (2, '--bs-warning-border-subtle', '#997404'),
        (2, '--bs-danger-border-subtle', '#842029'),
        (2, '--bs-light-border-subtle', '#495057'),
        (2, '--bs-dark-border-subtle', '#343a40'),
        (2, '--bs-heading-color', 'inherit'),
        (2, '--bs-link-color', '#6ea8fe'),
        (2, '--bs-link-hover-color', '#8bb9fe'),
        (2, '--bs-link-color-rgb', '110, 168, 254'),
        (2, '--bs-link-hover-color-rgb', '139, 185, 254'),
        (2, '--bs-code-color', '#e685b5'),
        (2, '--bs-highlight-color', '#dee2e6'),
        (2, '--bs-highlight-bg', '#664d03'),
        (2, '--bs-border-color', '#495057'),
        (2, '--bs-border-color-translucent', 'rgba(255, 255, 255, 0.15)'),
        (2, '--bs-form-valid-color', '#75b798'),
        (2, '--bs-form-valid-border-color', '#75b798'),
        (2, '--bs-form-invalid-color', '#ea868f'),
        (2, '--bs-form-invalid-border-color', '#ea868f');
    ''')
    
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
            cursor.execute("INSERT OR IGNORE INTO styles_classes_properties (class_id, property_name) VALUES (?, ?)", (class_id, prop_name))
            conn.commit()
            property_id = cursor.lastrowid
        else:
            property_id = existe_propriedade(class_id, propriedade)[0]

        cursor.execute("INSERT OR IGNORE INTO styles_classes_properties_values (property_id, value) VALUES (?, ?)", (property_id, valor))
        conn.commit()

def cadastra_componentes(conn, cursor, componentes_extraidos):
    for nome_componente, html_estruturas in componentes_extraidos.items():
        for html_estrutura in html_estruturas:
            # **Regex mais robusta para extrair classes (uso de re.findall):**
            classes_css = re.findall(r'class="([^"]+)"', html_estrutura)
            if classes_css:
                classes_css_string = ','.join(classes_css)
            else:
                classes_css_string = ""

            # Inserir o componente no banco de dados
            cursor.execute("INSERT OR IGNORE INTO BootstrapComponents (componentName, htmlStructure, cssClasses) VALUES (?, ?, ?)",
                           (nome_componente, html_estrutura, classes_css_string))
            conn.commit()
            component_id = cursor.lastrowid

            # **Registrando as classes CSS do componente na tabela styles_classes:**
            for css_class in classes_css:
                cursor.execute("SELECT id FROM styles_classes WHERE class_name = ? AND media_type = ?", (css_class, None))
                class_id_result = cursor.fetchone()

                if class_id_result:
                    class_id = class_id_result[0]  # Obter o ID da classe
                    cursor.execute("INSERT OR IGNORE INTO styles_classes_componentes (class_id, component_id) VALUES (?, ?)", (class_id, component_id))
                    conn.commit()

def gerar_exemplo_html(classe):
    """Gera um exemplo de HTML a partir da classe."""
    if classe.startswith("btn"):
        return f'<button class="{classe}">Button example</button>'
    elif classe.startswith("card"):
        return f'<div class="{classe}"><div class="card-body">Card example content</div></div>'
    elif classe.startswith("table"):
        return f'<table class="{classe}"></table>'
    elif classe.startswith("img"):
        return f'<img src="placeholder.jpg" alt="Imagem" class="{classe}">'
    elif classe.startswith("list-group"):
        return f'<ul class="{classe}"><li class="list-group-item">Item da lista</li></ul>'
    elif classe.startswith("form-control"):
        return f'<input type="text" class="{classe}" placeholder="Exemplo de input">'
    elif classe.startswith("navbar"):
        return f'<nav class="{classe}"></nav>'
    elif classe.startswith("row") or classe.startswith("col"):
        return f'<div class="{classe}"></div>'
    elif classe.startswith("alert"):
        return f'<div class="{classe}">Exemplo de alerta</div>'
    elif classe.startswith("progress"):
        return f'<div class="{classe}"><div class="progress-bar" role="progressbar" style="width: 25%;" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100">25%</div></div>'
    elif classe.startswith("pagination"):
        return f'<nav><ul class="{classe}"><li class="page-item"><a class="page-link" href="#">1</a></li></ul></nav>'
    elif classe.startswith("badge"):
        return f'<span class="{classe}">Exemplo de badge</span>'
    elif classe.startswith("breadcrumb"):
        return f'<nav aria-label="breadcrumb"><ol class="{classe}"><li class="breadcrumb-item active" aria-current="page">Home</li></ol></nav>'
    elif classe.startswith("accordion"):
        return f'<div class="{classe}"><div class="accordion-item"><h2 class="accordion-header"><button class="accordion-button" type="button">Cabeçalho do Acordèo</button></h2><div class="accordion-collapse"><div class="accordion-body">Corpo do Acordèo</div></div></div></div>'
    elif classe.startswith("list-group-item"):
        return f'<li class="{classe}">Exemplo de item de lista</li>'
    elif classe.startswith("modal"):
      return f'<div class="{classe}"><div class="modal-dialog"><div class="modal-content">Modal example content</div></div></div>'
    elif classe.startswith("dropdown"):
      return f'<div class="{classe}"><a href="#" class="dropdown-toggle" id="dropdownMenuButton1" data-bs-toggle="dropdown" aria-expanded="false">Dropdown</a><ul class="dropdown-menu" aria-labelledby="dropdownMenuButton1"><li><a class="dropdown-item" href="#">Action</a></li></ul></div>'	
    elif classe.startswith("dropdown-item"):
      return f'<a class="{classe}" href="#">Dropdown item example</a>'
    elif classe.startswith("modal-dialog"):
        return f'<div class="{classe}"></div>'  
    elif classe.startswith("modal-content"):
        return f'<div class="{classe}"></div>'  
    elif classe.startswith("modal-header"):
        return f'<div class="{classe}"></div>'  
    elif classe.startswith("modal-body"):
        return f'<div class="{classe}">Modal body example</div>'  
    elif classe.startswith("modal-footer"):
        return f'<div class="{classe}"></div>'
    elif classe.startswith("input-group"):
        return f'<div class="{classe}"><span class="input-group-text">Exemplo</span><input type="text" class="form-control"></div>'
    elif classe.startswith("figure"):
        return f'<figure class="{classe}"><img src="placeholder.jpg" alt="Imagem" class="figure-img img-fluid"></figure>'
    elif classe.startswith("blockquote"):
        return f'<blockquote class="{classe}"><p>Exemplo de citação</p></blockquote>'
    elif classe.startswith("form-check"):
        return f'<div class="{classe}"><input type="checkbox" class="form-check-input"> <label class="form-check-label">Check example</label></div>'
    elif classe.startswith("form-select"):
        return f'<select class="{classe}"> <option>Option 1</option> </select>'
    elif classe.startswith("progress-bar"):
        return f'<div class="progress"><div class="progress-bar {classe}" role="progressbar" style="width: 25%;" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100">25%</div></div>'
    elif classe.startswith("progress"):
        return f'<div class="{classe}"><div class="progress-bar" style="width: 25%;"></div></div>'
    elif classe.startswith("modal-dialog-scrollable"):
        return f'<div class="{classe}"><div class="modal-content"><div class="modal-body"><p>Exemplo de conteúdo modal</p></div></div></div>'
    elif classe.startswith("dropdown-menu"):
        return f'<ul class="{classe}"><li><a class="dropdown-item" href="#">Action</a></li></ul>'
    elif classe.startswith("nav-link"):
        return f'<a class="{classe}" href="#">Link example</a>'
    elif classe.startswith("nav-tabs"):
        return f'<ul class="{classe}"><li class="nav-item"><a class="nav-link active" aria-current="page" href="#">Home</a></li></ul>'
    elif classe.startswith("nav-pills"):
        return f'<ul class="{classe}"><li class="nav-item"><a class="nav-link active" href="#">Link</a></li></ul>'
    elif classe.startswith("figure-img"):
        return f'<img src="placeholder.jpg" alt="Imagem" class="{classe} img-fluid">'
    elif classe.startswith("form-check-input"):
        return f'<input class="{classe}" type="checkbox">'
    elif classe.startswith("form-check-label"):
        return f'<label class="{classe}">Check example</label>'
    elif classe.startswith("form-range"):
        return f'<input type="range" class="{classe}">'
    elif classe.startswith("pagination-lg") or classe.startswith("pagination-sm"):
        return f'<nav><ul class="{classe}"><li class="page-item"><a class="page-link" href="#">1</a></li></ul></nav>'
    elif classe.startswith("list-group-item-action"):
        return f'<a class="{classe}" href="#">Link de item de lista</a>'
    elif classe.startswith("navbar-brand"):
        return f'<a href="#" class="{classe}">Brand example</a>'
    elif classe.startswith("navbar-nav") or classe.startswith("navbar-toggler"):
        return f'<div class="{classe}"></div>'
    elif classe.startswith("navbar-nav-link"):
        return f'<a class="{classe}" href="#">Link da navbar</a>'
    elif classe.startswith("carousel-item"):
        return f'<div class="{classe}"><img src="placeholder.jpg" alt="Imagem de carrossel" class="d-block w-100"></div>'
    elif classe.startswith("carousel-control-prev") or classe.startswith("carousel-control-next"):
        return f'<button class="{classe}" type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide="prev"><span class="carousel-control-prev-icon" aria-hidden="true"></span><span class="visually-hidden">Previous</span></button>'
    elif classe.startswith("carousel-indicators"):
        return f'<div class="{classe}"><button type="button" data-bs-target="#carouselExampleCaptions" data-bs-slide-to="0" aria-current="true" aria-label="Slide 1"></button></div>'
    elif classe.startswith("offcanvas"):
        return f'<div class="{classe}"><div class="offcanvas-body">Offcanvas example</div></div>'
    elif classe.startswith("toast"):
        return f'<div class="{classe}"><div class="toast-body">Toast example</div></div>'
    elif classe.startswith("tooltip"):
        return f'<button class="{classe}" data-bs-toggle="tooltip" title="Tooltip example">Hover me</button>'
    elif classe.startswith("spinner"):
        return f'<div class="{classe}" role="status"><span class="visually-hidden">Loading...</span></div>'
    elif classe.startswith("bg-") or classe.startswith("text-"):
        return f'<div class="{classe}">Example text or background</div>'
    elif classe.startswith("d-"):
        return f'<div class="{classe}">Example of display utility</div>'
    elif classe.startswith("flex-"):
        return f'<div class="{classe} d-flex">Example of flexbox utility</div>'
    elif classe.startswith("float-"):
        return f'<div class="{classe}">Floating example</div>'
    elif classe.startswith("position-"):
        return f'<div class="{classe}">Positioning example</div>'
    elif classe.startswith("shadow-"):
        return f'<div class="{classe} shadow-sm">Example with shadow</div>'
    else:
        return None

db = 'cms.db'
arquivo_css = 'bootstrap.css'

deletar_banco_de_dados(db)
conn = sqlite3.connect(db)
cursor = conn.cursor()

criar_tabelas(db)
criar_temas(db)


#cadastra_componentes(conn, cursor, componentes)

print('Media Classes...')
media = extrair_classes_media(arquivo_css)
for media_tipo, classes_media in media.items():
    for classe, propriedades in classes_media.items():
        print(classe)
        if not existe_classe(classe, media_tipo):
            cursor.execute("INSERT OR IGNORE INTO styles_classes (class_name, media_type) VALUES (?, ?)", (classe, media_tipo))
            conn.commit()
            class_id = cursor.lastrowid
        else:
            class_id = existe_classe(classe, media_tipo)[0]

        cadastra_propriedades(conn, cursor, propriedades)

print('Classes...')
classes = extrair_classes_propriedades(arquivo_css)
for classe, propriedades in classes.items():
    if not classe.__contains__('@media'):
        media_tipo = None
        for classe, propriedades in classes.items():
            if not classe.__contains__('@media'):
                print(classe)
                if not existe_classe(classe, media_tipo):
                    cursor.execute("INSERT OR IGNORE INTO styles_classes (class_name, media_type) VALUES (?, ?)", (classe, media_tipo))
                    conn.commit()
                    class_id = cursor.lastrowid
                else:
                    class_id = existe_classe(classe, media_tipo)[0]
                
                cadastra_propriedades(conn, cursor, propriedades)

conn.close()