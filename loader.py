import json
from pathlib import Path

# Retrieve models from directory
def retrieveModelNames() -> list[Path]:
    files = []
    for file in Path().glob("models/benchmark/jani/*.jani"):
        if file.is_file():
            files.append(file)
    return files

# Select models from list
def selectModels(files: list[Path]) -> Path:
    for i, models in enumerate(files):
        print(i, models)

    userInput = int(input())
    return files[userInput]

# Load the JANI file
def loadData(path: Path | str) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    return data
