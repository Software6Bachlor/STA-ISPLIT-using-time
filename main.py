import os
import sys
import subprocess
import argparse
from loader import retrieveModelNames, selectModels

HOSTRESULTS = os.path.abspath("./results")
IMAGE_NAME = "simulation-image"

def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    memory = parseMemoryArg(sys.argv)

    models = retrieveModelNames()
    userInput = selectModels(models)

    selectedModel = os.path.abspath(str(userInput))
    runDocker(memory, selectedModel)


def parseMemoryArg(args: list[str]) -> int:
    """Parse the memory argument from CLI args.

    Usage:
        python main.py -m <memoryMb>
        python main.py --memoryMb <memoryMb>
        python main.py <memoryMb>
    """
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("legacyMemory", nargs="?", type=int)
    parser.add_argument("-m", "--memoryMb", dest="memoryMb", type=int)
    parsed = parser.parse_args(args[1:])

    memory = parsed.memoryMb if parsed.memoryMb is not None else parsed.legacyMemory
    if memory is None:
        print("Missing memory argument. Usage: python main.py -m <memoryMb>")
        raise SystemExit(1)

    if memory <= 0:
        print("Invalid memory argument. Please provide a positive integer in MB.")
        raise SystemExit(1)

    return memory


def runDocker(memory: int, modelPath: str):
    """Run the builder with the given memory limit
    Args:
        memory (int): Memory limit in MB
        modelPath (str): Absolute host path to the selected model file
    """

    if not os.path.isfile(modelPath):
        print(f"Selected model file does not exist: {modelPath}")
        raise SystemExit(1)

    hostModelDir = os.path.dirname(modelPath)
    modelName = os.path.basename(modelPath)
    containerModelPath = f"/input/{modelName}"
    hostResultsDockerPath = HOSTRESULTS.replace("\\", "/")
    hostInputDockerPath = hostModelDir.replace("\\", "/")

    os.makedirs(HOSTRESULTS, exist_ok=True)
    print(f"Starting Docker with memory limit: {memory} MB")
    print(f"Selected model: {modelPath}")

    result = subprocess.run([
        "docker", "run",
        "--rm",
        "-m", f"{memory}m",
        "-v", f"{hostResultsDockerPath}:/results",
        "-v", f"{hostInputDockerPath}:/input:ro",
        IMAGE_NAME,
        containerModelPath
    ])

    if result.returncode != 0:
        raise SystemExit(result.returncode)

if __name__ == "__main__":
    main()
