import sys
from pathlib import Path
from loader import load_data
from parser import parse_model


def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    # Load and parse the model
    data = load_data("tests//testdata//ModestSTA.jani")
    model = parse_model(data)
    print(f"Model name: {model.name}")
    print(f"locals: {model.automata[0].locations}")


if __name__ == "__main__":
    main()
