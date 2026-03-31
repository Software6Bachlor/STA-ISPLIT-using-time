import os
import subprocess
from loader import loadData, retrieveModelNames, selectModels
from parser import parseModel

HOSTRESULTS = os.path.abspath("./results")

def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    models = retrieveModelNames()
    userInput = selectModels(models)

    data = loadData(userInput)
    model = parseModel(data)
    print(model)

def runDocker(memory: int):
    """Run the builder with the given memory limit
    Args:
        memory (int): Memory limit in MB
    """

    subprocess.run([
        "docker", "run",
        "--rm",
        "-m", f"{memory}m",
        "-v", f"{HOSTRESULTS}:/results",
        "simulation-image"
    ])


if __name__ == "__main__":
    main()
