import sys
from pathlib import Path
from loader import load_data
from parser import parse_model
from models import RestartSimulation, MonteCarloSimulation


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
    data = load_data("tests//testdata//ModestSTA.jani")  
    model = parse_model(data)
    RESTART_sim = RestartSimulation(model)
    RESTART_sim.run()

    



if __name__ == "__main__":
    main()
