from jsonschema import validate
from jsonschema.exceptions import ValidationError

def validate_mission_file(data_path, schema):
    """Returns True if valid, raises ValidationError otherwise."""
    try:
        validate(instance=data_path, schema=schema)
        print("Successfully validated missions")
        return data_path
    except ValidationError as e:
        print(f"❌ VALIDATION FAILED in {data_path}")
        print(f"Path to error: {list(e.path)}")
        print(f"Message: {e.message}") # This tells you EXACTLY what is wrong
        raise