import os
import yaml

def read_yaml(file_path='config.yaml'):
    """Load YAML file into a dictionary."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
