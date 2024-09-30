import re
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
        conteudo = arquivo.read()

        # Regex para encontrar classes e suas propriedades
        pattern = r'([^{]+)\s*\{([^}]*)\}'
        matches = re.findall(pattern, conteudo)

        for classe, propriedades in matches:
            # Limpa e divide múltiplas classes
            for nome_classe in classe.split(','):
                nome_classe = nome_classe.strip().replace('}','').strip()
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
            conteudo = arquivo.read()
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

# Exemplo de uso
arquivo_css = 'bootstrap.css'  # Substitua pelo caminho real
media = extrair_classes_media(arquivo_css)

print("\nClasses @media:")
for media_tipo, classes_media in media.items():
    print(f"{media_tipo}:")
    for classe, propriedades in classes_media.items():
        print(f"  {classe}:")
        for propriedade in propriedades:
            if propriedade:
                print(f"    {propriedade}")


 # Encontra todas as classes normais
classes = extrair_classes_propriedades(arquivo_css)

print("Classes:")
for classe, propriedades in classes.items():
    if not classe.__contains__('@media'):
        print(f"{classe}:")
        for propriedade in propriedades:
            if propriedade:  # Ignora propriedades vazias
                print(f"    {propriedade.strip()}")