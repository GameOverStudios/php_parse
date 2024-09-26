import os
import shutil

def contar_arquivos(diretorio):
    total_arquivos = 0
    arquivos_com_updates = 0

    # Itera sobre os arquivos no diretório
    for raiz, dirs, arquivos in os.walk(diretorio):
        for arquivo in arquivos:
            total_arquivos += 1
            # Verifica se a palavra "updates" está no nome do arquivo
            if arquivo.lower().__contains__('upgrade') or arquivo.lower().__contains__('update'):
                arquivos_com_updates += 1
                caminho_origem = os.path.join(raiz, arquivo)
                caminho_destino = os.path.join('output_nomake', arquivo)
                shutil.move(caminho_origem, caminho_destino)

    # Calcula a diferença
    arquivos_sem_updates = total_arquivos - arquivos_com_updates

    print(f'Total de arquivos: {total_arquivos}')
    print(f'Arquivos com "updates": {arquivos_com_updates}')
    print(f'Arquivos sem "updates": {arquivos_sem_updates}')

# Exemplo de uso
diretorio = 'PHP-Parsers-master\\output'
contar_arquivos(diretorio)
