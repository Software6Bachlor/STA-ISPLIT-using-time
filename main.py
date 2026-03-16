import sys
from pathlib import Path
from loader import load_data
from parser import parse_model
from restart import runRestart


# def main():
#     """Main entry point"""
#     print("STA-ISPLIT Project")

#     # Load and parse the model
#     data = load_data("tests//testdata//ModestSTA.jani")
#     model = parse_model(data)
#     print(model.automata[0].edges[0].destinations[0])


# Main used to test RESTART.
def main():
    runRestart()
    



if __name__ == "__main__":
    main()
