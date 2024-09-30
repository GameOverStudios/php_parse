import json
import os
from collections import defaultdict  # Importar defaultdict

def extrair_dados_php(json_data):
    """
    Extrai as informações sobre as classes PHP do JSON.
    """
    classes = defaultdict(lambda: {"methods": defaultdict(dict)})

    def percorrer(node):
        if node.get("kind") == "class":
            class_name = node["name"]["name"]
            classes[class_name]["name"] = class_name
            classes[class_name]["visibility"] = node.get("visibility", "public")
            classes[class_name]["isAbstract"] = node.get("isAbstract", False)
            classes[class_name]["isFinal"] = node.get("isFinal", False)
            classes[class_name]["isReadonly"] = node.get("isReadonly", False)
            classes[class_name]["description"] = node.get("description", "")

            for child in node.get("children", []):
                if child.get("kind") == "method":
                    method_name = child["name"]["name"]
                    classes[class_name]["methods"][method_name]["name"] = method_name
                    classes[class_name]["methods"][method_name]["visibility"] = child.get("visibility", "public")
                    classes[class_name]["methods"][method_name]["isStatic"] = child.get("isStatic", False)
                    classes[class_name]["methods"][method_name]["isAbstract"] = child.get("isAbstract", False)
                    classes[class_name]["methods"][method_name]["isFinal"] = child.get("isFinal", False)
                    classes[class_name]["methods"][method_name]["description"] = child.get("description", "")

                    for param in child.get("arguments", []):
                        param_data = {
                            "name": param["name"]["name"],
                            "type": param.get("type"),
                            "value": param.get("value"),
                            "description": param.get("description", "")
                        }
                        classes[class_name]["methods"][method_name].setdefault("parameters", []).append(param_data)

                    if child.get("type"):
                        classes[class_name]["methods"][method_name]["return_type"] = child["type"]

                for grandchild in child.get("children", []):
                    if grandchild.get("kind") == "property":
                        property_name = grandchild["name"]["name"]
                        classes[class_name].setdefault("properties", []).append({
                            "name": property_name,
                            "visibility": grandchild.get("visibility", "public"),
                            "isStatic": grandchild.get("isStatic", False),
                            "description": grandchild.get("description", "")
                        })

        for child in node.get("children", []):
            percorrer(child)

    percorrer(json_data)
    return classes

def imprimir_class_info(classes):
    for class_name, class_data in classes.items():
        print(f"Classe: {class_name}")
        print(f"Visibilidade: {class_data.get('visibility', 'public')}")
        print(f"Abstrata: {class_data.get('isAbstract', False)}")
        print(f"Final: {class_data.get('isFinal', False)}")
        print(f"Só leitura: {class_data.get('isReadonly', False)}")
        print(f"Descrição: {class_data.get('description', '')}")
        print()

        if 'properties' in class_data:
            print("Propriedades:")
            for prop in class_data['properties']:
                print(f"  - {prop['name']} (Visibilidade: {prop['visibility']}, Estática: {prop['isStatic']})")
                print(f"    Descrição: {prop['description']}")
                print()
        else:
            print("Nenhuma propriedade encontrada.")

        if 'methods' in class_data:
            print("Métodos:")
            for method_name, method_data in class_data['methods'].items():
                print(f"  - {method_name} (Visibilidade: {method_data.get('visibility', 'public')}, Estática: {method_data.get('isStatic', False)})")
                print(f"    Descrição: {method_data.get('description', '')}")
                print(f"    Tipo de retorno: {method_data.get('return_type', 'N/A')}")
                if 'parameters' in method_data:
                    for param in method_data['parameters']:
                        print(f"      - {param['name']} (Tipo: {param['type']}, Valor: {param['value']})")
                        print(f"        Descrição: {param['description']}")
                else:
                    print("Nenhum parâmetro encontrado.")
        else:
            print("Nenhum método encontrado.")




input_dir = "output"  # Replace com o diretório de origem do arquivo

for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        json_file = os.path.join(input_dir, filename)
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        classes = extrair_dados_php(json_data)
        imprimir_class_info(classes)

