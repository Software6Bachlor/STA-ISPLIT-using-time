from loader import loadData, retrieveModelNames, selectModels
from parser import parseModel
from models.simulation import RestartSimulation, SingleSimulation, STASimulator
from models.state import State


# def main():
#     """Main entry point"""
#     print("STA-ISPLIT Project")

#     # Load and parse the model
#     data = load_data("tests/testData/ModestSTA.jani")
#     model = parse_model(data)
#     print(model.automata[0].edges[0].destinations[0])


def main():
    print("STA-ISPLIT Project")
    data = loadData("models/benchmark/jani/long-sta.jani")  
    model = parseModel(data)
    STAsim = SingleSimulation(model, 1)   
    STAsim.run_multiple(
    target_automaton="STop", 
    target_location="loc_0", 
    max_time=500.0, 
    iterations=10000
)

if __name__ == "__main__":
    main()
