import sys
from pathlib import Path
from loader import loadData
from parser import parseModel
from models.simulation import RestartSimulation, STASimulator
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
    STAsim = STASimulator(model)

    initState = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                      globalVars={"queue": 0.0, "served_customer": False},
                      autoVars={"Arrivals": {"c": 0.0, "x": 0.0}, "Server": {"c": 0.0, "x": 0.0}})

   
   
   
    STAsim.step(initState)

    



if __name__ == "__main__":
    main()
