import json
import sqlite3

# Definição do parâmetro global para a versão
global_version = "1.0"

def remove_comments(css_content):
    # Remove os comentários do CSS
    return '\n'.join(line for line in css_content.splitlines() if not line.strip().startswith('/*'))

def extract_data_from_css(css_content):
    properties = []
    classes = []
    class_count = 0  # Inicializa o contador de classes

    lines = css_content.splitlines()
    current_class = None
    current_properties = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('/*'):
            continue  # Ignora linhas em branco ou comentários

        # Se a linha contém uma classe
        if line.endswith('{'):
            class_name = line.split('{')[0].strip('. ')
            current_class = class_name
            current_properties = []  # Reseta as propriedades para a nova classe
            class_count += 1  # Incrementa o contador de classes

        # Se a linha contém propriedades
        elif current_class and line.endswith('}'):
            # Ao encontrar '}', termina a captura das propriedades
            if current_properties:
                properties_ids = [prop.split(':')[0].strip() for prop in current_properties]
                properties_values = [prop.split(':')[1].strip().rstrip(';') for prop in current_properties]
                classes.append({
                    'name': current_class,
                    'category': get_category_for_class(current_class),
                    'property_ids': json.dumps(properties_ids),
                    'property_values': properties_values,  # Adiciona os valores das propriedades
                })
            current_class = None  # Reseta a classe atual
        elif current_class:
            # Captura as propriedades
            current_properties.append(line)

    return {
        'properties': properties,
        'classes': classes,
        'class_count': class_count  # Adiciona a contagem de classes ao retorno
    }

def get_category_for_property(property_name):
    property_name = property_name.lower()
    if property_name.startswith(("bg", "bg-", "background")):
        return "Background"
    elif property_name.startswith(("font", "font-", "font-family")):
        return "Typography"
    elif property_name.startswith(("border", "border-", "border-color", "border-width", "border-style")):
        return "Styling"
    elif property_name.startswith(("font-weight", "fw")):
        return "Typography"
    elif property_name.startswith(("font-size", "fs")):
        return "Typography"
    elif property_name.startswith(("text", "text-", "text-align", "text-decoration", "text-emphasis")):
        return "Typography"
    elif property_name.startswith(("rounded", "rounded-")):
        return "Styling"
    elif property_name.startswith(("opacity", "opacity-")):
        return "Appearance"
    elif property_name.startswith(("position", "position-")):
        return "Positioning"
    elif property_name.startswith(("gap", "gap-", "row-gap", "column-gap")):
        return "Spacing"
    elif property_name.startswith(("m", "mt", "mb", "ml", "mr", "mx", "my")):
        return "Spacing"
    elif property_name.startswith(("p", "pt", "pb", "pl", "pr", "px", "py")):
        return "Spacing"
    elif property_name.startswith(("width", "min-width", "max-width")):
        return "Dimensions"
    elif property_name.startswith(("height", "min-height", "max-height")):
        return "Dimensions"
    elif property_name.startswith(("color", "color-")):
        return "Colors"
    elif property_name.startswith(("z-index")):
        return "Z-Index"
    elif property_name.startswith(("overflow", "overflow-")):
        return "Overflow"
    elif property_name.startswith(("flex", "flex-", "flex-direction", "flex-wrap", "justify-content", "align-items", "align-content", "align-self", "order")):
        return "Flexbox"
    elif property_name.startswith(("text-shadow")):
        return "Text Effects"
    elif property_name.startswith(("text-transform")):
        return "Text Effects"
    elif property_name.startswith(("line-height")):
        return "Typography"
    elif property_name.startswith(("ratio", "aspect-ratio")):
        return "Image Aspect Ratio"
    elif property_name.startswith(("visually-hidden")):
        return "Hidden Elements"
    elif property_name.startswith(("float")):
        return "Floats"
    elif property_name.startswith(("object-fit")):
        return "Object Fit"
    

def get_category_for_class(class_name):
    if class_name.startswith(("btn-", "btn-group", "btn-link")):
        return "Buttons"
    elif class_name.startswith(("card-", "card-group", "card-img", "card-header", "card-body", "card-footer")):
        return "Cards"
    elif class_name.startswith(("nav-", "navbar", "nav-link", "navbar-brand", "nav-item", "nav-tabs", "nav-pills", "pagination")):
        return "Navigation"
    elif class_name.startswith("table-"):
        return "Tables"
    elif class_name.startswith("list-group"):
        return "List Groups"
    elif class_name.startswith("form-"):
        return "Forms"
    elif class_name.startswith(("text-", "display-", "lead", "initialism", "blockquote")):
        return "Typography"
    elif class_name.startswith(("row-", "col-", "container", "container-fluid")):
        return "Layout"
    elif class_name.startswith(("img-", "figure-img", "figure-caption")):
        return "Images"
    elif class_name.startswith(("carousel-", "carousel-inner", "carousel-item", "carousel-caption")):
        return "Carousels"
    elif class_name.startswith(("modal-", "modal-dialog", "modal-content", "modal-header", "modal-body", "modal-footer")):
        return "Modals"
    elif class_name.startswith(("accordion-", "accordion-item", "accordion-button", "accordion-body")):
        return "Accordions"
    elif class_name.startswith(("progress-", "progress-bar")):
        return "Progress"
    elif class_name.startswith(("alert-", "alert-dismissible", "alert-heading")):
        return "Alerts"
    elif class_name.startswith(("dropdown-menu", "dropdown", "dropdown-toggle")):
        return "Dropdowns"
    elif class_name.startswith(("badge")):
        return "Badges"  
    elif class_name.startswith(("breadcrumb", "breadcrumb-item")):
        return "Breadcrumbs"
    elif class_name.startswith(("spinner-", "spinner-grow")):
        return "Spinners"
    elif class_name.startswith(("offcanvas-", "offcanvas-body")):
        return "Offcanvas"
    elif class_name.startswith(("placeholder")):
        return "Placeholders"
    elif class_name.startswith(("clearfix")):
        return "Clearfix"
    elif class_name.startswith(("text-bg-")):
        return "Background Text"
    elif class_name.startswith(("link-")):
        return "Links"
    elif class_name.startswith(("float-", "position-")):
        return "Positioning"
    elif class_name.startswith(("object-fit-", "ratio-")):
        return "Image Sizing"
    elif class_name.startswith(("visually-hidden")):
        return "Hidden Elements"
    elif class_name.startswith(("stretched-link")):
        return "Links"
    elif class_name.startswith(("opacity-", "visible", "invisible", "d-")):
        return "Appearance"
    elif class_name.startswith(("overflow-")):
        return "Overflow"
    else:
        return "Other"

def create_and_insert_data(css_data, db_name="bootstrap_data.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        # Criação das tabelas
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS Categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS Properties (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES Categories(id)
            )
        """)
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS Presets (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS Classes (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                property_ids TEXT,
                version TEXT,
                category_id INTEGER,
                preset_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES Categories(id),
                FOREIGN KEY (preset_id) REFERENCES Presets(id)
            )
        """)
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS Classes_Properties (
                id INTEGER PRIMARY KEY,
                class_id INTEGER,
                property_id INTEGER,
                property_value TEXT,
                FOREIGN KEY (class_id) REFERENCES Classes(id),
                FOREIGN KEY (property_id) REFERENCES Properties(id)
            )
        """)

    except sqlite3.Error as e:
        print(f"Erro ao criar tabelas: {e}")

    try:
        # Inserção de categorias
        for clas in css_data['classes']:
            cursor.execute("INSERT OR IGNORE INTO Categories (name) VALUES (?)", (clas['category'],))

        # Inserção de propriedades
        properties_dict = {}
        for prop in css_data['classes']:
            for property_name in json.loads(prop['property_ids']):
                category = get_category_for_property(property_name)
                cursor.execute(""" 
                    INSERT OR IGNORE INTO Properties (name, category_id)
                    VALUES (?, (SELECT id FROM Categories WHERE name = ?))
                """, (property_name, category))

                # Captura o ID da propriedade recém-inserida
                property_id = cursor.execute("SELECT id FROM Properties WHERE name = ?", (property_name,)).fetchone()
                if property_id:
                    properties_dict[property_name] = property_id[0]

        # Criar um preset padrão
        cursor.execute(""" 
            INSERT OR IGNORE INTO Presets (name) VALUES (?);
        """, ("default",))

        # Obter o ID do preset padrão
        preset_id = cursor.execute("SELECT id FROM Presets WHERE name = ?", ("default",)).fetchone()[0]

        # Inserção de classes
        for clas in css_data['classes']:
            cursor.execute("INSERT OR IGNORE INTO Categories (name) VALUES (?)", (clas['category'],))

            # Inserir a classe no banco de dados
            cursor.execute(""" 
                INSERT OR IGNORE INTO Classes (name, property_ids, version, category_id, preset_id)
                VALUES (?, ?, ?, (SELECT id FROM Categories WHERE name = ?), ?)
            """, (clas['name'], clas['property_ids'], global_version, clas['category'], preset_id))

            # Obter o ID da classe recém-inserida
            class_id = cursor.execute("SELECT id FROM Classes WHERE name = ?", (clas['name'],)).fetchone()[0]

            # Inserir os valores de propriedades na tabela Classes_Properties
            property_ids = json.loads(clas['property_ids'])
            property_values = clas['property_values']
            for property_name, property_value in zip(property_ids, property_values):
                if property_name in properties_dict:
                    cursor.execute(""" 
                        INSERT INTO Classes_Properties (class_id, property_id, property_value)
                        VALUES (?, ?, ?)
                    """, (class_id, properties_dict[property_name], property_value))

    except sqlite3.Error as e:
        print(f"Erro ao inserir dados: {e}")

    conn.commit()
    conn.close()

def process_css_file(file_path):
    with open(file_path, 'r') as file:
        css_content = file.read()
    
    cleaned_css = remove_comments(css_content)
    css_data = extract_data_from_css(cleaned_css)
    create_and_insert_data(css_data)

    # Mostra o número total de classes encontradas
    print(f"Número total de classes encontradas: {css_data['class_count']}")

process_css_file('bootstrap.css')