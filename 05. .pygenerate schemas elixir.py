import json
import os
from collections import defaultdict

def extract_php_data(json_file):
    """Extracts class name, methods, parameters, and return types from a PHP JSON file."""

    with open(json_file, 'r') as f:
        data = json.load(f)

    classes = defaultdict(lambda: {"methods": defaultdict(dict)})

    def traverse(node):
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
            traverse(child)

    traverse(data)
    return classes


def generate_elixir_schemas(classes, output_dir):
    """Generates Elixir schemas from the extracted PHP data."""

    for class_name, class_data in classes.items():
        schema_filename = os.path.join(output_dir, f"{class_name.lower()}.ex")
        with open(schema_filename, 'w') as f:
            f.write(f"""
defmodule PaidLevels.Schema.{class_name} do
  use Ecto.Schema

  import Ecto.Changeset

  @primary_key {{:id, :integer, autogenerate: true}}
  @foreign_key_type :integer
  schema "{class_name.lower()}" do
""")
            for field_name in class_data.get("fields", []):
                f.write(f"    field :id, :integer\n")
            for field_name in class_data.get("fields", []):
                f.write(f"    field :{field_name.lower()}, :string\n")
            for method_name, method_data in class_data["methods"].items():
                for param in method_data.get("parameters", []):
                    param_type = param.get("type")
                    param_default = param.get("value")
                    if param_type == "string":
                        f.write(f"    field :{param['name'].lower()}, :string, default: {param_default!r}\n")
                    elif param_type == "int" or param_type == "integer":
                        f.write(f"    field :{param['name'].lower()}, :integer, default: {param_default}\n")
                    elif param_type == "bool" or param_type == "boolean":
                        f.write(f"    field :{param['name'].lower()}, :boolean, default: {param_default}\n")
                    # Add more type mappings as needed...
            f.write(f"""
    timestamps()
  end

  @doc false
  def changeset({class_name}, attrs) do
    {class_name}
    |> cast(attrs, [
      {{:id, :integer}},
""")
            for field_name in class_data.get("fields", []):
                f.write(f"           {{:{field_name.lower()}, :string}},\n")
            f.write(f"""           ])
    |> validate_required([:id""")
            for field_name in class_data.get("fields", []):
                f.write(f", :{field_name.lower()}")
            f.write(f"""])
  end
end
            """)

def generate_elixir_controller(classes, output_dir):
    """Generates Elixir controller from the extracted PHP data."""

    for class_name, class_data in classes.items():
        controller_filename = os.path.join(output_dir, f"{class_name.lower()}_controller.ex")
        with open(controller_filename, 'w') as f:
            f.write(f"")


def main():
    """Processes JSON files in a directory and generates Elixir code."""

    input_dir = "output"  # Replace with your directory
    output_dir = "ex"  # Replace with your output directory

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            json_file = os.path.join(input_dir, filename)
            classes = extract_php_data(json_file)
            generate_elixir_schemas(classes, output_dir)
            generate_elixir_controller(classes, output_dir)

if __name__ == "__main__":
    main()