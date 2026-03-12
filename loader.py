import json

# Load the JANI file
def load_data(path: str) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    return data
