# C:\Projects\stc\stc-core\constraints\validator.py
import json
import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Import Paths
ENV_DATA = 'stc-core/data/all_environments.yaml'
S_ENV_SING = 'stc-core/schemas/single_environment_schema.json'
S_ENV_LIST = 'stc-core/schemas/environments.json'

def load_json_file(path):
    with open(path, 'r') as file:
        try:
            data = json.load(file)
            return data
        except json.JSONDecodeError as e:
            print(f"Error: Failed to load JSON. Details: {e}")
            exit()

def load_yaml_file(path):
    with open(path, 'r') as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as e:
            print(f"Error: Failed to load YAML. Details: {e}")
            exit()

def get_combined_schema(list_schema_path, single_schema_path):
    """Links the single item schema into the list schema."""
    list_schema = load_json_file(list_schema_path)
    single_schema = load_json_file(single_schema_path)
    
    root_key = next(iter(list_schema['properties']))
    list_schema['properties'][root_key]['items'] = single_schema
    return list_schema

def open_environments():
    try:
        # Load data
        env_schema = get_combined_schema(S_ENV_LIST, S_ENV_SING)
        env_data = load_yaml_file(ENV_DATA)

        environment_profiles = env_data['environments']
        print(f"Successfully loaded {len(environment_profiles)} environments.")
        return env_data, env_schema
    except FileNotFoundError as e:
        print(f"Error: Failed to find root key. Details: {e}") 
        exit()
