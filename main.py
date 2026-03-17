import sys
from pathlib import Path
from loader import loadData
from parser import parseModel


def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    # Load and parse the model
    data = loadData("tests//testdata//ModestSTA.jani")
    model = parseModel(data)
    print(model.properties[0].expression.operands)


if __name__ == "__main__":
    main()
