import json
import jmespath

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

file_path = 'output/BxAclDb.php.json'
json_data = load_json(file_path)

class_name = jmespath.search("children[?kind=='class'].name.name", json_data)
class_name_extends = jmespath.search("children[?kind=='class'].extends.name", json_data)
isAnonymous = jmespath.search("children[?kind=='class'].isAnonymous", json_data)

# Extraindo métodos e parâmetros
methods = jmespath.search("children[?kind=='class'].body[?'method']",json_data)

for method in methods:
    for m in range(1, len(method)):
        method_kind = str(method[m]['name']['kind'])
        method_name = str(method[m]['name']['name'])
        method_byref = str(method[m]['byref'])
        method_type = str(method[m]['type'])
        method_nullable = str(method[m]['nullable'])
        method_isAbstract = str(method[m]['isAbstract'])
        method_isFinal = str(method[m]['isFinal'])
        method_isReadonly = str(method[m]['isReadonly'])
        method_isStatic = str(method[m]['isStatic'])

        print('---------------------------------------------------------')
        print(':: '+method_name)
        print('---------------------------------------------------------')
        print(' kind: '+ method_kind)
        print(' ByRef: '+ method_byref)
        print(' Type: '+method_type)
        print(' Nullable: '+method_nullable)
        print(' Abstract: '+method_isAbstract)
        print(' Final: '+method_isFinal)
        print(' Readonly: '+method_isReadonly)
        print(' Static: '+method_isStatic)

        method_arguments = method[m].get('arguments', [])
        # Imprimindo arguments
        print(' Arguments: ')
        for arg in method_arguments:
            args_kind = str(arg['kind'])
            args_name_kind = str(arg['name']['kind'])
            args_name = str(arg['name']['name'])
            xxx = str(arg['name']['kind'])
            for name in arg['name']:
                args_value_kind = str(name['kind'])
                
                args_value_value = str(name['value'])
                args_value_type = str(name['type'])
                args_value_byref = str(name['byref'])
                args_value_variadic = str(name['variadic'])
                args_value_readonly = str(name['readonly'])
                args_value_nullable = str(name['nullable'])
                args_value_byref = str(name['byref'])

            args_type = str(arg['type'])
            args_byref = str(arg['byref'])
            args_variadic = str(arg['variadic'])
            args_readonly = str(arg['readonly'])
            args_nullable = str(arg['nullable'])
            args_byref = str(arg['byref'])

            print('     kind: '+args_kind)
            print('     kind name: '+args_name_kind)
            print('     name: '+args_name.upper())
            print('     value: '+args_value)
            print('     type: '+args_type)
            print('     byref: '+args_byref)
            print('     variadic: '+args_variadic)
            print('     readonly: '+args_readonly)
            print('     nullable: '+args_nullable)
            print('     byref: '+args_byref)