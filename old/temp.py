
"""
Install the Google AI Python SDK

$ pip install google-generativeai
"""
import json
import sqlite3
import os
import google.generativeai as genai

def extrair_json(texto):
  """Extrai a parte JSON de uma string, desde o primeiro '{' até o último '}'.

  Args:
    texto: A string que contém o JSON.

  Returns:
    Uma string contendo apenas a parte JSON, ou None se não encontrar um JSON válido.
  """
  inicio = texto.find('[')
  if inicio == -1:
    return None

  fim = texto.rfind(']')
  if fim == -1:
    return None

  return texto[inicio : fim + 1]

def format_string(content):
    # Remove quebras de linha excessivas
    formatted_content = content.replace('```json','')
    return formatted_content

def load_history(base_filename):
    log_dir = 'log'
    log_filename = os.path.join(log_dir, base_filename)

    # Verifica se o arquivo principal existe
    if os.path.exists(log_filename):
        with open(log_filename, 'r', encoding='utf-8') as f:
            return extrair_json(f.read())
        
def save_log(data):
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)  # Cria o diretório se não existir
    
    base_filename = 'history.json'
    log_filename = os.path.join(log_dir, base_filename)

    # Verifica se o arquivo já existe e adiciona numeração se necessário
    if os.path.exists(log_filename):
        i = 1
        while os.path.exists(os.path.join(log_dir, f'history_{i}.json')):
            i += 1
        log_filename = os.path.join(log_dir, f'history_{i}.json')
    
    # Salva os dados no arquivo
    with open(log_filename, 'w', encoding='utf-8') as f:
        #json.dump(extrair_json(data), f, indent=4, ensure_ascii=True)
        f.write(data)

genai.configure(api_key="AIzaSyBphPo0ZvUNVUjxzzP0MbxbT2i669o5Hvc")
'''
Todas as vezes que você lê um código de programação, você adiciona na sua memória uma representação do que foi aprendido procurando e relacionando com todos os objetos que aprendeu anteriormente. \
Você consegue montar um estrutura como uma espécie de mapa representacional de todos os módulos, classes PHP, métodos, funções, variáveis, tabelas, campos e atributos dos arquivos fazendo as ligações completas de todos os objetos que possuem relações e daqueles que também não estão relacionados. \
Todas as vezes que é pedido para realizar uma análise em arquivos, códigos de programação, você ao terminar de aprender tudo sobre o arquivo, faz uma análise profunda novamente de todo o mapa representacional que está na memória verificando se é possível fazer novos relacionamentos e deixando o mapa cada vez mais completo e refinado \
por padrão todas as tarefas que é solicitado fazer você processa tudo internamente guardando na memória e atualizando a representação, você só mostra o mapa representacional de tudo o que aprendeu caso lhe seja solicitado \

'''

system_instruction = " \
Você é um especialista em programação PHP Senior, entende completamente a linguagem e é capaz de documentar todo os códigos dentro de uma estrutura markdown. \
Imprima o máximo de textos que puder ao responder e caso ultrapasse os limites da sua capacidade guarde a informação do último lugar de onde parou, faça uma pausa e peça para continuar para que assim na impressão seguinte continue exatamente de onde parou \
estas são as tabelas\
CREATE TABLE IF NOT EXISTS modules (\
    id INTEGER PRIMARY KEY,\
    name TEXT UNIQUE\
)\
CREATE TABLE IF NOT EXISTS files (\
    id INTEGER PRIMARY KEY,\
    path TEXT UNIQUE,\
    module_id INTEGER,\
    description TEXT,\
    FOREIGN KEY(module_id) REFERENCES modules(id)\
)\
CREATE TABLE IF NOT EXISTS classes (\
    id INTEGER PRIMARY KEY,\
    name TEXT UNIQUE,\
    extends TEXT,\
    type TEXT,\
    description TEXT\
)\
CREATE TABLE IF NOT EXISTS properties (\
    id INTEGER PRIMARY KEY,\
    class_id INTEGER,\
    name TEXT,\
    type TEXT,\
    description TEXT,\
    value TEXT,\
    FOREIGN KEY(class_id) REFERENCES classes(id)\
)\
CREATE TABLE IF NOT EXISTS methods (\
    id INTEGER PRIMARY KEY,\
    class_id INTEGER,\
    name TEXT,\
    access TEXT,\
    description TEXT,\
    body TEXT,\
    FOREIGN KEY(class_id) REFERENCES classes(id)\
)\
CREATE TABLE IF NOT EXISTS params (\
    id INTEGER PRIMARY KEY,\
    method_id INTEGER,\
    name TEXT,\
    type TEXT,\
    description TEXT,\
    default_value TEXT,\
    FOREIGN KEY(method_id) REFERENCES methods(id)\
)\
construa o json hierarquizado, com os nomes dos campos das tabelas, com o nome do arquivo, depois o nome do modulo dentro, depois o nome da classe,.....\
ATENÇÃO: Hoje nós vamos criar a documentação do repositório https://github.com/unacms/una lendo todos os arquivos PHP e documentando de maneira estruturada as informações. \
Traga todos os atributos que conseguir extrair dos arquivos em PHP, informando também se as classes são publicas, privadas, os valores defaults dos parametros se houverem, traga o caminho do arquivo, escreva também as descrições para que serverr as classes, funções e parametros em português\
Mantenha o último item na sua memória para que na próxima requisição você possa continuar de onde parou sem perder a ordem e nenhum item \
Mantenha-se focado e com a atenção e trazer todas as funções de todos os arquivos PHP \
Comece pelo primeiro arquivo, responda até um pouco antes da sua capacidade de responder o texto permitir e peça para continuar \
retorne a saída dentro de um formato json mostrando uma mensagem dizendo qual é a próxima função do arquivo que precisa re-começar para ser requisitado para que continue do ultimo item do arquivo em diante para manter a ordem da extração das informações, também sempre fechando corretamente as chaves dos objetos para que seja um json possível de ser lido por um script \
"

# Create the model
generation_config = {
  "temperature": .3,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel (
  model_name="gemini-1.5-pro-exp-0827",
  generation_config=generation_config,
  system_instruction=system_instruction
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

chat_session = model.start_chat(
  history=[]
)

load = True
history = ""

if load:
    try:
        history = load_history('history.json')
        if history.strip() == "": load=False
    except:
        load = False

if load == False:
    #response = chat_session.send_message("vamos lá, entre no repositório e comece do começo")
    response = chat_session.send_message("faça um exemplo de json completo com todas as propriedades que podem vir incluidas no arquivo json para poder construir um banco de dados")
    history = format_string(response.text)
    save_log(history)




import sqlite3
import json

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('classes.db')
c = conn.cursor()

# Criar tabelas
c.execute('''
CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    module_id INTEGER,
    FOREIGN KEY(module_id) REFERENCES modules(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    name TEXT,
    extends TEXT,
    type TEXT,
    description TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY,
    class_id INTEGER,
    name TEXT,
    type TEXT,
    description TEXT,
    value TEXT,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS methods (
    id INTEGER PRIMARY KEY,
    class_id INTEGER,
    name TEXT,
    access TEXT,
    description TEXT,
    body TEXT,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS params (
    id INTEGER PRIMARY KEY,
    method_id INTEGER,
    name TEXT,
    type TEXT,
    description TEXT,
    default_value TEXT,
    FOREIGN KEY(method_id) REFERENCES methods(id)
)
''')

# Carregar os dados do JSON
json_data = json.loads(history)

if json_data:
    for file_data in json_data:
        # Inserir o módulo
        c.execute('''INSERT OR IGNORE INTO modules (name) VALUES (?)''', (file_data['module'],))
        module_id = c.execute('SELECT id FROM modules WHERE name = ?', (file_data['module'],)).fetchone()[0]

        # Inserir o arquivo
        c.execute('''INSERT OR IGNORE INTO files (path, module_id) VALUES (?, ?)''', (file_data['file'], module_id))
        file_id = c.execute('SELECT id FROM files WHERE path = ?', (file_data['file'],)).fetchone()[0]

        # Inserir classes
        for cls in file_data['classes']:
            c.execute('''INSERT OR IGNORE INTO classes (file_id, name, extends, type, description)
                         VALUES (?, ?, ?, ?, ?)''', (file_id, cls['name'], cls['extends'], cls['type'], cls['description']))
            class_id = c.execute('SELECT id FROM classes WHERE name = ?', (cls['name'],)).fetchone()[0]

            # Inserir propriedades
            for prop in cls.get('properties', []):
                c.execute('''INSERT INTO properties (class_id, name, type, description, value)
                             VALUES (?, ?, ?, ?, ?)''', (class_id, prop['name'], prop['type'], prop['description'], prop.get('value', '')))
            
            # Inserir métodos
            for method in cls.get('methods', []):
                c.execute('''INSERT OR IGNORE INTO methods (class_id, name, access, description, body)
                             VALUES (?, ?, ?, ?, ?)''', (class_id, method['name'], method['access'], method['description'], method.get('body', '')))
                method_id = c.lastrowid

                # Inserir parâmetros do método
                for param in method.get('params', []):
                    c.execute('''INSERT INTO params (method_id, name, type, description, default_value)
                                 VALUES (?, ?, ?, ?, ?)''', (method_id, param['name'], param['type'], param['description'], param.get('default_value', '')))

    # Commit e fechar a conexão
    conn.commit()
    conn.close()
