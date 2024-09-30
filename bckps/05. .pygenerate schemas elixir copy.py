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
                        param_data = {
                            "name": param["name"]["name"],
                            "type": param.get("type"),
                            "value": param.get("value"),
                        }
                        classes[class_name]["methods"][method_name]["parameters"].append(param_data)
                    if child.get("type"):
                        classes[class_name]["methods"][method_name]["return_type"] = child["type"]

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
                print(f"      - {param['name']} ({param['type']})")
            if method_data.get("return_type"):
                print(f"    Retorno: {method_data['return_type']}")
        print()

def main():
    """
    Processes JSON files in a directory and prints the class information.
    """

    input_dir = "output"  # Replace with your directory

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
