import sys
from pathlib import Path
from loader import loadData
from parser import parseModel
from models.simulation import RestartSimulation, SingleSimulation, STASimulator
from models.state import State


# def main():
#     """Main entry point"""
#     print("STA-ISPLIT Project")

#     # Load and parse the model
#     data = load_data("tests//testdata//ModestSTA.jani")
#     model = parse_model(data)
#     print(model.automata[0].edges[0].destinations[0])


# Main used to test RESTART.
def main():
    print("STA-ISPLIT Project")
    data = loadData("tests//testdata//ModestSTA.jani")  
    model = parseModel(data)
    STAsim = SingleSimulation(model)   
    STAsim.run()

if __name__ == "__main__":
    main()
