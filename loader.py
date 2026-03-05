import json
from models.STA import Model
from parser import parse_model

# Load the JANI file
def load(path: str) -> Model:
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    return parse_model(data)
