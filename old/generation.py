import json
import sqlite3
import os
import shutil
import glob
import google.generativeai as genai

genai.configure(api_key="AIzaSyBphPo0ZvUNVUjxzzP0MbxbT2i669o5Hvc")

system_instruction = " \
    Você é um especialista em programação PHP Senior, entende completamente a linguagem e é capaz de documentar todo os códigos dentro de uma estrutura markdown. \
    Imprima o máximo de textos que puder ao responder e caso ultrapasse os limites da sua capacidade guarde a informação do último lugar de onde parou, faça uma pausa e peça para continuar para que assim na impressão seguinte continue exatamente de onde parou \
    este é o padrão do arquivo:\
    [\
        {\
            \"module\": \"Module1\",\
            \"files\": [\
                {\
                    \"file\": \"/path/to/file1.php\",\
                    \"description\": \"Descrição do arquivo\",\
                    \"classes\": [\
                        {\
                            \"name\": \"MyClass1\",\
                            \"extends\": \"ParentClass\",\
                            \"type\": \"public\",\
                            \"description\": \"Esta classe faz alguma coisa.\",\
                            \"properties\": [\
                                {\
                                    \"name\": \"property1\",\
                                    \"type\": \"string\",\
                                    \"description\": \"Uma propriedade de string.\",\
                                    \"value\": \"valor padrão\"\
                                },\
                                {\
                                    \"name\": \"property2\",\
                                    \"type\": \"integer\",\
                                    \"description\": \"Uma propriedade inteira.\"\
                                }\
                            ],\
                            \"methods\": [\
                                {\
                                    \"name\": \"myMethod1\",\
                                    \"access\": \"public\",\
                                    \"description\": \"Este método faz alguma coisa.\",\
                                    \"return\": \"retorno do método\",\
                                    \"params\": [\
                                        {\
                                            \"name\": \"param1\",\
                                            \"type\": \"string\",\
                                            \"description\": \"O primeiro parâmetro.\",\
                                            \"default_value\": \"valor padrão\"\
                                        },\
                                        {\
                                            \"name\": \"param2\",\
                                            \"type\": \"integer\",\
                                            \"description\": \"O segundo parâmetro.\"\
                                        }\
                                    ]\
                                }\
                            ]\
                        }\
                    ]\
                }\
            ]\
        },\
        {\
            \"module\": \"Module2\",\
            \"files\": [\
                {\
                    \"file\": \"/path/to/file2.php\",\
                    \"description\": \"Descrição do arquivo\",\
                    \"classes\": [\
                        {\
                            \"name\": \"MyClass2\",\
                            \"extends\": null,\
                            \"type\": \"private\",\
                            \"description\": \"Outra classe.\",\
                            \"properties\": [],\
                            \"methods\": []\
                        }\
                    ]\
                }\
            ]\
        }\
    ]\
    converta o campo default_value para string \
    construa o json hierarquizado, com os nomes dos campos das tabelas, com o nome do arquivo, depois o nome do modulo dentro, depois o nome da classe,.....\
    ATENÇÃO: Hoje nós vamos criar a documentação do repositório https://github.com/unacms/una lendo todos os arquivos PHP e documentando de maneira estruturada as informações. \
    Traga todos os atributos que conseguir extrair dos arquivos em PHP, informando também se as classes são publicas, privadas, os valores defaults dos parametros se houverem, traga o caminho do arquivo, escreva também as descrições para que serverr as classes, funções e parametros em português\
    Mantenha o último item na sua memória para que na próxima requisição você possa continuar de onde parou sem perder a ordem e nenhum item \
    Mantenha-se focado e com a atenção e trazer todas as funções de todos os arquivos PHP \
    Comece pelo primeiro arquivo, responda até um pouco antes da sua capacidade de responder o texto permitir e peça para continuar \
    retorne a saída dentro de um formato json mostrando uma mensagem dizendo qual é a próxima função do arquivo que precisa re-começar para ser requisitado para que continue do ultimo item do arquivo em diante para manter a ordem da extração das informações\
    SEMPRE FECHE CORRETAMENTE COM CHAVES } OS OBJETOS JSON para que seja um json possível de ser lido por um script, \
    SEMPRE TRAGA UMA RESPOSTA MOSTRANDO QUAL O PRÒXIMO ITEM A REQUISITAR NA PRÓXIMA INTERAÇÃO \
    "

# Configuração do modelo
generation_config = {
    "temperature": .3,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Inicializando o modelo
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-exp-0827",
    generation_config=generation_config,
    system_instruction=system_instruction
)

# Inicializando sessão de chat
chat_session = model.start_chat(history=[])

log_dir = 'log'
database = 'classes.db'

def get_ultimo_history_file():
    """
    Retorna o caminho para o último arquivo history_X.json gerado.

    Returns:
        O caminho para o último arquivo history_X.json ou None se nenhum arquivo for encontrado.
    """
    files = glob.glob(os.path.join(log_dir, 'history_*.json'))

    if not files:
        return None

    # Ordena os arquivos pelo número no nome do arquivo (history_1, history_2, etc.)
    files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))

    return files[-1]

def load_all_data_tree_view(db_name=database):
    """Carrega todos os dados do banco SQLite e retorna em formato de árvore."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    output = []

    # Recupera os módulos
    c.execute("SELECT id, name FROM modules")
    modules = c.fetchall()

    # Percorre os módulos e coleta os arquivos, classes, propriedades, métodos e parâmetros
    for module_id, module_name in modules:
        output.append(f"📁 Módulo: {module_name}")
        
        # Recupera os arquivos do módulo
        c.execute("SELECT id, path, description FROM files WHERE module_id = ?", (module_id,))
        files = c.fetchall()

        for file_id, file_path, file_description in files:
            output.append(f"  📄 Arquivo: {file_path}")
            output.append(f"    Descrição: {file_description}")

            # Recupera as classes do arquivo
            c.execute("SELECT id, name, extends, type, description FROM classes WHERE file_id = ?", (file_id,))
            classes = c.fetchall()

            for class_id, class_name, class_extends, class_type, class_description in classes:
                output.append(f"    🔹 Classe: {class_name} ({class_type})")
                output.append(f"      Extends: {class_extends if class_extends else 'Nenhuma'}")
                output.append(f"      Descrição: {class_description}")

                # Recupera as propriedades da classe
                c.execute("SELECT name, type, description, value FROM properties WHERE class_id = ?", (class_id,))
                properties = c.fetchall()

                if properties:
                    output.append("      🛠️  Propriedades:")
                    for prop_name, prop_type, prop_description, prop_value in properties:
                        output.append(f"        - {prop_name} ({prop_type})")
                        output.append(f"          Descrição: {prop_description}")
                        output.append(f"          Valor padrão: {prop_value}")
                
                # Recupera os métodos da classe
                c.execute("SELECT id, name, access, description, return FROM methods WHERE class_id = ?", (class_id,))
                methods = c.fetchall()

                if methods:
                    output.append("      🔧 Métodos:")
                    for method_id, method_name, method_access, method_description, method_return in methods:
                        output.append(f"        - {method_name} ({method_access})")
                        output.append(f"          Descrição: {method_description}")
                        output.append(f"          Corpo: {method_return}")
                        
                        # Recupera os parâmetros do método
                        c.execute("SELECT name, type, description, default_value FROM params WHERE method_id = ?", (method_id,))
                        params = c.fetchall()

                        if params:
                            output.append("          Parâmetros:")
                            for param_name, param_type, param_description, param_default in params:
                                output.append(f"            - {param_name} ({param_type})")
                                output.append(f"              Descrição: {param_description}")
                                output.append(f"              Valor padrão: {param_default}")

    conn.close()

    return "\n".join(output)

def load_all_data(db_name=database):
    """Carrega todos os dados do banco SQLite e retorna em formato JSON estruturado."""
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Recupera os módulos
    c.execute("SELECT id, name FROM modules")
    modules = c.fetchall()

    data = []

    # Percorre os módulos e coleta os arquivos, classes, propriedades, métodos e parâmetros
    for module_id, module_name in modules:
        module_data = {
            "module": module_name,
            "files": []
        }

        # Recupera os arquivos do módulo
        c.execute("SELECT id, path, description FROM files WHERE module_id = ?", (module_id,))
        files = c.fetchall()

        for file_id, file_path, file_description in files:
            file_data = {
                "file": file_path,
                "description": file_description,
                "classes": []
            }

            # Recupera as classes do arquivo
            c.execute("SELECT id, name, extends, type, description FROM classes WHERE file_id = ?", (file_id,))
            classes = c.fetchall()

            for class_id, class_name, class_extends, class_type, class_description in classes:
                class_data = {
                    "name": class_name,
                    "extends": class_extends,
                    "type": class_type,
                    "description": class_description,
                    "properties": [],
                    "methods": []
                }

                # Recupera as propriedades da classe
                c.execute("SELECT name, type, description, value FROM properties WHERE class_id = ?", (class_id,))
                properties = c.fetchall()

                for prop_name, prop_type, prop_description, prop_value in properties:
                    property_data = {
                        "name": prop_name,
                        "type": prop_type,
                        "description": prop_description,
                        "value": prop_value
                    }
                    class_data["properties"].append(property_data)

                # Recupera os métodos da classe
                c.execute("SELECT id, name, access, description, return FROM methods WHERE class_id = ?", (class_id,))
                methods = c.fetchall()

                for method_id, method_name, method_access, method_description, method_return in methods:
                    method_data = {
                        "name": method_name,
                        "access": method_access,
                        "description": method_description,
                        "return": method_return,
                        "params": []
                    }

                    # Recupera os parâmetros do método
                    c.execute("SELECT name, type, description, default_value FROM params WHERE method_id = ?", (method_id,))
                    params = c.fetchall()

                    for param_name, param_type, param_description, param_default in params:
                        param_data = {
                            "name": param_name,
                            "type": param_type,
                            "description": param_description,
                            "default_value": param_default
                        }
                        method_data["params"].append(param_data)

                    class_data["methods"].append(method_data)

                file_data["classes"].append(class_data)

            module_data["files"].append(file_data)

        data.append(module_data)

    conn.close()

    return json.dumps(data, indent=4, ensure_ascii=False)

def extrair_json(texto):
    inicio = texto.find('[')
    if inicio == -1:
        return None

    fim = texto.rfind(']')
    if fim == -1:
        return None

    return texto[inicio: fim + 1]

def format_string(content):
    formatted_content = content.replace('```json', '')
    return formatted_content

def load_history_file(base_filename, extract = True):
    log_filename = os.path.join(log_dir, base_filename)

    if os.path.exists(log_filename):
        with open(log_filename, 'r', encoding='utf-8') as f:
            if extract == True:
                return f.read()
            else: return f.read()

def save_log(data):
    os.makedirs(log_dir, exist_ok=True)
    
    base_filename = 'history.json'
    log_filename = os.path.join(log_dir, base_filename)

    if os.path.exists(log_filename):
        i = 1
        while os.path.exists(os.path.join(log_dir, f'history_{i}.json')):
            i += 1
        log_filename = os.path.join(log_dir, f'history_{i}.json')
    
    with open(log_filename, 'w', encoding='utf-8') as f:
        f.write(data)

def create_tables(c):
        
    # Criar tabelas
    c.execute('''CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        module_id INTEGER,
        description TEXT,
        FOREIGN KEY(module_id) REFERENCES modules(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS functions (
        id INTEGER PRIMARY KEY,
        file_id INTEGER,
        name TEXT,
        access TEXT,
        description TEXT,
        return TEXT,
        FOREIGN KEY(file_id) REFERENCES files(id))''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY,
        file_id INTEGER,  -- Essa linha estava faltando
        name TEXT UNIQUE,
        extends TEXT,
        type TEXT,
        description TEXT,
        FOREIGN KEY(file_id) REFERENCES files(id)  -- Chave estrangeira para a tabela files
    )
    ''')

    c.execute('''CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY,
        class_id INTEGER,
        name TEXT,
        type TEXT,
        description TEXT,
        value TEXT,
        FOREIGN KEY(class_id) REFERENCES classes(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS methods (
        id INTEGER PRIMARY KEY,
        class_id INTEGER,
        name TEXT,
        access TEXT,
        description TEXT,
        return TEXT,
        FOREIGN KEY(class_id) REFERENCES classes(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS params (
        id INTEGER PRIMARY KEY,
        method_id INTEGER,
        name TEXT,
        type TEXT,
        description TEXT,
        default_value TEXT,
        FOREIGN KEY(method_id) REFERENCES methods(id))''')

def extrair_apos_ultimo_colchete(texto):
        """
        Extrai tudo que estiver depois do último ']' de uma string.

        Args:
            texto: A string de entrada.

        Returns:
            A substring após o último ']' ou uma string vazia se ']' não for encontrado.
        """
        ultimo_colchete = texto.rfind(']')
        if ultimo_colchete == -1:
            return ""
        else:
            resultado = ""
            for i in range(ultimo_colchete + 1, len(texto)):
                resultado += texto[i]
            return resultado.strip()

def create_database(json_data, c):
    if json_data:
        for file_data in json_data:
            # Inserir o módulo
            c.execute('''INSERT OR IGNORE INTO modules (name) VALUES (?)''', (file_data['module'],))
            module_id = c.execute('SELECT id FROM modules WHERE name = ?', (file_data['module'],)).fetchone()[0]

            for data in file_data.get('files', []):
                # Inserir o arquivo
                c.execute('''INSERT OR IGNORE INTO files (path, module_id) VALUES (?, ?)''', (data['file'], module_id))
                file_id = c.execute('SELECT id FROM files WHERE path = ?', (data['file'],)).fetchone()[0]

                # Inserir funções sem classes
                for func in data.get('functions', []):
                    c.execute('''INSERT INTO functions (file_id, name, access, description, return)
                                VALUES (?, ?, ?, ?, ?)''', (file_id, func['name'], func['access'], func['description'], func.get('return', '')))
                    function_id = c.lastrowid

                    # Inserir parâmetros da função
                    for param in func.get('params', []):
                        c.execute('''INSERT INTO params (method_id, name, type, description, default_value)
                                    VALUES (?, ?, ?, ?, ?)''', (function_id, param['name'], param['type'], param['description'], param.get('default_value', '')))
                        

                # Inserir classes
                for cls in data['classes']:
                    c.execute('''INSERT OR IGNORE INTO classes (file_id, name, extends, type, description)
                                VALUES (?, ?, ?, ?, ?)''', (file_id, cls['name'], cls['extends'], cls['type'], cls['description']))
                    class_id = c.execute('SELECT id FROM classes WHERE name = ?', (cls['name'],)).fetchone()[0]

                    # Inserir propriedades
                    for prop in cls.get('properties', []):
                        c.execute('''INSERT INTO properties (class_id, name, type, description, value)
                                    VALUES (?, ?, ?, ?, ?)''', (class_id, prop['name'], prop['type'], prop['description'], prop.get('value', '')))
                    
                    # Inserir métodos
                    for method in cls.get('methods', []):
                        c.execute('''INSERT OR IGNORE INTO methods (class_id, name, access, description, return)
                                    VALUES (?, ?, ?, ?, ?)''', (class_id, method['name'], method['access'], method['description'], method.get('return', '')))
                        method_id = c.lastrowid

                        # Inserir parâmetros do método
                        for param in method.get('params', []):
                            c.execute('''INSERT INTO params (method_id, name, type, description, default_value)
                                        VALUES (?, ?, ?, ?, ?)''', (method_id, param['name'], param['type'], param['description'], param.get('default_value', '')))

def start(filename, load_history = True, rebuild_all = False, next_prompt = ''):

    history = ""
    #if load_history and rebuild_all == False and next_prompt == '':
        #next_prompt == 'continue de mostrando todas as funções de onde parou por favor'

    if rebuild_all:
        if os.path.exists(log_dir):
            shutil.rmtree(log_dir)
            os.makedirs(log_dir, exist_ok=True)
        if os.path.exists(database):
            os.remove(database)

    if (load_history and next_prompt == '') or (load_history == False and next_prompt != ''):
        try:
            history = load_history_file(filename)
            if history.strip() == "": load_history = False
            else:
                next_prompt = extrair_apos_ultimo_colchete(load_history_file(filename, False))
                history = extrair_json(history)
        except:
            load_history = False

    sql = True
    if load_history == False or next_prompt != '':
        if rebuild_all == True:
            prompt = "Ok, vamos começar pelo começo e ordenadamente, entre no repositório e traga as informações do primeiro arquivo"
        else: prompt = next_prompt
        print('----------------------------------------------------------------------------')
        print(prompt)
        print('----------------------------------------------------------------------------')
        response = chat_session.send_message(prompt)
        history = format_string(response.text)
        save_log(history)
        next_prompt = extrair_apos_ultimo_colchete(history)
        history = extrair_json(history)
    
    elif next_prompt == '':
        print('***ERROR***')
        sql = False

    if sql == True:
        conn = sqlite3.connect(database)
        c = conn.cursor()

        #cria banco dados
        create_tables(c)

        # Carregar dados JSON
        json_data = json.loads(history)

        # faz inserts
        create_database(json_data, c)

        # Commit e fechar a conexão
        conn.commit()
        conn.close()

        json_data = load_all_data_tree_view()

        print(json_data)
        print('\r\n\r\n] Continue mostrando as funções a partir de: ' + next_prompt)

        if rebuild_all == True: rebuild_all = False
        start(filename, load_history, rebuild_all, next_prompt)


print (system_instruction)


#Rebuild_All = False
#Use_LastHistory = True
#start(get_ultimo_history_file(), Use_LastHistory, Rebuild_All, '')


