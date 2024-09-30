import json
import os
from collections import defaultdict

def extrair_dados_php(json_data):
    """
    Extrai as informações sobre as classes PHP do JSON.
    """
    classes = defaultdict(lambda: {"methods": defaultdict(dict)})

    def percorrer(node):
        if node.get("kind") == "class":
            class_name = node["name"]["name"]
            classes[class_name]["name"] = class_name
            for child in node["body"]:
                if child.get("kind") == "method":
                    method_name = child["name"]["name"]
                    classes[class_name]["methods"][method_name]["name"] = method_name
                    classes[class_name]["methods"][method_name]["parameters"] = []
                    for param in child.get("arguments", []):
                        if param.get('kind') == 'parameter':
                            # Inicializa param_name
                            param_name = None
                            param_type = None

                            # Verifica se o nome do parâmetro está presente
                            if "name" in param:
                                param_name = param["name"]["name"]

                            # Extraindo tipo
                            if param.get("type") and param["type"]:
                                param_type = param["type"]["name"]
                            elif param.get("value") and param["value"].get("kind"):
                                param_type = param["value"]["kind"]

                            # Verificação da chave "value"
                            default_value = None
                            if "value" in param and param["value"] is not None:
                                default_value = param["value"].get("value")

                            param_data = {
                                "name": param_name,
                                "type": param_type,
                                "default_value": default_value
                            }
                            classes[class_name]["methods"][method_name]["parameters"].append(param_data)

                    # Tipo de retorno
                    if child.get("type") and 'name' in child["type"]:
                        classes[class_name]["methods"][method_name]["return_type"] = child["type"]["name"]
                    else:
                        classes[class_name]["methods"][method_name]["return_type"] = None

        for child in node.get("children", []):
            percorrer(child)

    percorrer(json_data)
    return classes

def imprimir_class_info(classes):
    for class_name, class_data in classes.items():
        print(f"Classe: {class_name}")
        print(f"Propriedades: {class_data.get('fields', [])}")
        print("Métodos:")
        for method_name, method_data in class_data["methods"].items():
            print(f"  - {method_name}")
            for param in method_data.get("parameters", []):
                param_type = param['type'] if param['type'] else ""
                default_value = param['default_value'] if param['default_value'] is not None else ""
                print(f"      - {param['name']} {param_type}: {default_value}")
            if method_data.get("return_type"):
                return_type = method_data["return_type"] if method_data["return_type"] else ""
                print(f"    Retorno: {return_type}")
        print()

def main():
    """
    Processes JSON files in a directory and prints the class information.
    """
    input_dir = "output"  # Substitua pelo seu diretório

    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            json_file = os.path.join(input_dir, filename)
            with open(json_file, 'r') as f:
                json_data = json.load(f)
            classes = extrair_dados_php(json_data)
            imprimir_class_info(classes)
            print('--------------------------------------------------------')

if __name__ == "__main__":
    main()
