# C:\Projects\stc\stc-core\constraints\validator.py
import json
import yaml
import os
from pathlib import Path

# 1. Get the directory where THIS script is located
current_dir = Path(__file__).resolve().parent

# 2. Go up two levels to reach C:\Projects\stc\
# (One to get out of /src, one to get out of /stc-simulation)
project_root = current_dir.parents[2]

# 3. Join with the core repo path
BASE_DIR = project_root / "stc-core" / "schemas"

S_MIS_SING = os.path.join(BASE_DIR, 'single_mission.json')
S_MIS_LIST = os.path.join(BASE_DIR, 'mission.json')
MIS_DATA = 'data/all_mission_profiles.yaml'

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
    try:
        """Links the single item schema into the list schema."""
        list_schema = load_json_file(list_schema_path)
        single_schema = load_json_file(single_schema_path)
        
        # Identify the root key (either 'environments', 'modules', or 'missions')
        root_key = next(iter(list_schema['properties']))
        list_schema['properties'][root_key]['items'] = single_schema
        return list_schema
    except FileNotFoundError as e:
        print(f"Error: Failed to find root key. Details: {e}") 
        exit()

def open_missions():
    try:
        # Load data
        mis_schema = get_combined_schema(S_MIS_LIST, S_MIS_SING)
        mis_data = load_yaml_file(MIS_DATA)

        # Now this will work because the root key is 'missions'
        mission_profiles = mis_data['missions']
        print(f"Successfully loaded {len(mission_profiles)} missions.")
        return mis_data, mis_schema, mission_profiles
    except FileNotFoundError as e:
        print(f"Error: Failed to find root key. Details: {e}") 
        exit()
                