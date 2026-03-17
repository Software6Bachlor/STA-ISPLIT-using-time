import sys
import argparse
from pathlib import Path
from loader import loadData
from parser import parseModel

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="STA-ISPLIT Project")
    parser.add_argument("model_file_path", nargs="?", default="tests/testdata/ModestSTA.jani",help="Path to the model file")
    args = parser.parse_args()

    # Load and parse the model
    data = loadData(args.model_file_path)
    model = parseModel(data)
    print(model)

if __name__ == "__main__":
    main()
