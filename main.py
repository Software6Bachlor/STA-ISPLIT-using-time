import os
import sys
import subprocess
import argparse
from loader import retrieveModelNames, selectModels

HOSTRESULTS = os.path.abspath("./results")
HOSTPROJECTROOT = os.path.abspath(os.path.dirname(__file__))
IMAGE_NAME = "simulation-image"

def main():
    """Main entry point"""
    print("STA-ISPLIT Project")

    memory = parseMemoryArg(sys.argv)
    cpuLimit = parseCpuArg(sys.argv)
    selectedModelArg = parseModelArg(sys.argv)

    if selectedModelArg is None:
        models = retrieveModelNames()
        userInput = selectModels(models)
        selectedModel = os.path.abspath(str(userInput))
    else:
        selectedModel = os.path.abspath(selectedModelArg)

    ensureDockerEngineAvailable()
    runDocker(memory, selectedModel, cpuLimit)


def parseCliArgs(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-m", "--memoryMb", dest="memoryMb", type=int)
    parser.add_argument("--cpus", dest="cpus", type=float)
    parser.add_argument("--model", dest="modelPath", type=str)
    return parser.parse_args(args[1:])


def parseMemoryArg(args: list[str]) -> int:
    """Parse the memory argument from CLI args.

    Usage:
        python main.py -m <memoryMb>
        python main.py --memoryMb <memoryMb>
    """
    parsed = parseCliArgs(args)

    memory = parsed.memoryMb if parsed.memoryMb is not None else None
    if memory is None:
        print("Missing memory argument. Usage: python main.py -m <memoryMb>")
        raise SystemExit(1)

    if memory <= 0:
        print("Invalid memory argument. Please provide a positive integer in MB.")
        raise SystemExit(1)

    return memory


def parseModelArg(args: list[str]) -> str | None:
    parsed = parseCliArgs(args)
    if parsed.modelPath is None:
        return None

    if not os.path.isfile(parsed.modelPath):
        print(f"Selected model file does not exist: {parsed.modelPath}")
        raise SystemExit(1)

    return parsed.modelPath


def parseCpuArg(args: list[str]) -> float | None:
    """Parse optional CPU limit for docker run.

    Usage:
        python main.py --cpus <cpuLimit>
    """
    parsed = parseCliArgs(args)
    cpus = parsed.cpus

    if cpus is None:
        return None

    if cpus <= 0:
        print("Invalid CPU limit. Please provide a positive number for --cpus.")
        raise SystemExit(1)

    return cpus


def ensureDockerEngineAvailable() -> None:
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
    except FileNotFoundError:
        print("Docker CLI is not installed or not on PATH.")
        print("Install Docker Desktop and reopen the terminal.")
        raise SystemExit(1)

    if result.returncode != 0:
        print("Docker engine is not reachable. Start Docker Desktop and wait until it is running.")
        if result.stderr:
            print(result.stderr.strip())
        raise SystemExit(1)


def runDocker(memory: int, modelPath: str, cpuLimit: float | None = None):
    """Run the builder with the given memory limit
    Args:
        memory (int): Memory limit in MB
        modelPath (str): Absolute host path to the selected model file
        cpuLimit (float | None): Optional Docker CPU limit passed to --cpus
    """

    if not os.path.isfile(modelPath):
        print(f"Selected model file does not exist: {modelPath}")
        raise SystemExit(1)

    hostModelDir = os.path.dirname(modelPath)
    modelName = os.path.basename(modelPath)
    containerModelPath = f"/input/{modelName}"
    hostProjectDockerPath = HOSTPROJECTROOT.replace("\\", "/")
    hostResultsDockerPath = HOSTRESULTS.replace("\\", "/")
    hostInputDockerPath = hostModelDir.replace("\\", "/")

    os.makedirs(HOSTRESULTS, exist_ok=True)
    print("[HOST] Docker preflight passed")
    print(f"[HOST] Development bind mount: {HOSTPROJECTROOT} -> /app")
    print(f"Starting Docker with memory limit: {memory} MB")
    if cpuLimit is not None:
        print(f"Starting Docker with CPU limit: {cpuLimit}")
    print(f"Selected model: {modelPath}")
    print("[HOST] Launching container...")

    command = [
        "docker", "run",
        "--rm",
        "-m", f"{memory}m",
        "-v", f"{hostProjectDockerPath}:/app",
        "-v", f"{hostResultsDockerPath}:/results",
        "-v", f"{hostInputDockerPath}:/input:ro",
        IMAGE_NAME,
        containerModelPath
    ]

    if cpuLimit is not None:
        command.insert(3, "--cpus")
        command.insert(4, str(cpuLimit))

    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("[HOST] Container execution completed successfully")

if __name__ == "__main__":
    main()
