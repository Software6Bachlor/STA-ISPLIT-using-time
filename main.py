import sys
from pathlib import Path
from loader import load


def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    # Load and parse the model
    model = load("tests//testdata//ModestSTA.jani")
    print(f"Model name: {model.name}")



if __name__ == "__main__":
    main()
