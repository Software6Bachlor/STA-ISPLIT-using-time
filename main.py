import ast
import json
import os
import sys
import subprocess
import argparse
from loader import retrieveModelNames, selectModels

HOSTRESULTS = os.path.abspath("./results")
HOSTPROJECTROOT = os.path.abspath(os.path.dirname(__file__))
IMAGE_NAME = "simulation-image"

def main():
    print("STA-ISPLIT Project")

    memory = parseMemoryArg(sys.argv)
    cpuLimit = parseCpuArg(sys.argv)
    rareLocation = parseRareLocationArg(sys.argv)
    selectedModelArg = parseModelArg(sys.argv)
    ifTimeLimit = parseIfTimeLimitArg(sys.argv)
    parsedArgs = parseCliArgs(sys.argv)
    numTrials = parsedArgs.numTrials
    wallClockLimit = parsedArgs.wallClockLimit
    method = parsedArgs.method

    if selectedModelArg is None:
        models = retrieveModelNames()
        userInput = selectModels(models)
        selectedModel = os.path.abspath(str(userInput))
    else:
        selectedModel = os.path.abspath(selectedModelArg)

    selectedModel = resolveModelConstants(selectedModel)

    ensureDockerEngineAvailable()
    runDocker(memory, selectedModel, cpuLimit, rareLocation, ifTimeLimit, numTrials, wallClockLimit, method)

def benchmarkMain(memoryMb = None, ifTimeLimit = None):
    ensureDockerEngineAvailable()
    runDocker(memoryMb, cpuLimit=None, ifTimeLimit=ifTimeLimit)


def parseCliArgs(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
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


def parseRareLocationArg(args: list[str]) -> str:
    parsed = parseCliArgs(args)
    rareLocation = parsed.rareLocation

    if not isinstance(rareLocation, str) or not rareLocation.strip():
        print("Invalid rare location. Please provide a non-empty location name for --rareLocation.")
        raise SystemExit(1)

    return rareLocation.strip()


def parseIfTimeLimitArg(args: list[str]) -> float | None:
    parsed = parseCliArgs(args)
    ifTimeLimit = parsed.ifTimeLimit

    if ifTimeLimit is not None and ifTimeLimit <= 0:
        print("Invalid time limit. Please provide a positive number for --ifTimeLimit.")
        raise SystemExit(1)

    return ifTimeLimit


def _parseConstantInput(rawValue: str) -> object:
    text = rawValue.strip()
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False

    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text




def resolveModelConstants(modelPath: str) -> str:
    with open(modelPath, encoding="utf-8-sig") as file:
        data = json.load(file)

    constants = data.get("constants", [])
    changed = False

    for constant in constants:
        if constant.get("value", None) is not None:
            continue

        prompt = constant.get("name", "constant")
        constantType = constant.get("type")
        if constantType:
            prompt = f"{prompt} ({constantType})"
        constant["value"] = _parseConstantInput(input(f"{prompt}: "))
        changed = True

    # Check if this is a chain template and generate concrete model
    if _isChainTemplate(modelPath):
        print("[MODEL] Detected chain template, generating concrete model...")
        constants_dict = _extractConstantsAsDict(data)
        try:
            builder = ChainModelBuilder(constants_dict)
            concrete_data = builder.buildModel()
            #print(f"[MODEL] Generated chain model with {constants_dict.get('N', '?')} locations")
        except Exception as e:
            print(f"[ERROR] Failed to generate chain model: {e}")
            raise SystemExit(1)

        # Write concrete model to tempfile
        tempDir = tempfile.mkdtemp(prefix="chain-model-")
        tempPath = os.path.join(tempDir, os.path.basename(modelPath))
        with open(tempPath, "w", encoding="utf-8") as file:
            json.dump(concrete_data, file, indent=2)
        #print(f"[MODEL] Wrote concrete chain model to {tempPath}")
        return tempPath

    if not changed:
        return modelPath

    normalizedDir = tempfile.mkdtemp(prefix="normalized-model-")
    normalizedPath = os.path.join(normalizedDir, os.path.basename(modelPath))

    with open(normalizedPath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return normalizedPath


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



import subprocess
import os

# Define your static host paths and image name here or pull from environment/config
HOSTRESULTS = "./results"  # Modify as needed for your server
IMAGE_NAME = "simulation-image:latest"

def runDocker(memory: int, cpuLimit: float | None = None, ifTimeLimit: float | None = None) -> None:
    """Run the self-contained benchmark container with no host-side loops or sweeps.
    
    Args:
        memory (int): Memory limit in MB
        cpuLimit (float | None): Optional Docker CPU limit passed to --cpus
        ifTimeLimit (float | None): Optional Importance Function builder time limit
    """
    # Prepare the host results directory to catch the outputs

    absolute_host_results = os.path.abspath(HOSTRESULTS)
    hostResultsDockerPath = absolute_host_results.replace("\\", "/")
    os.makedirs(absolute_host_results, exist_ok=True)

    # Base docker run command mapping hardware limits and the output directory
    command = [
        "docker", "run",
        "--rm",
        "-m", f"{memory}m",
        "-v", f"{hostResultsDockerPath}:/results", 
        IMAGE_NAME,
        "--memoryMb", str(memory),
        "--resultsDir", "/results"
    ]

    # Dynamically inject the static IF time limit if provided
    if ifTimeLimit is not None:
        command.extend(["--ifTimeLimit", str(ifTimeLimit)])

    # Inject CPU limits early into the docker options block if present
    if cpuLimit is not None:
        command.insert(3, "--cpus")
        command.insert(4, str(cpuLimit))

    # Launch the container and let it do its job
    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(result.returncode)
if __name__ == "__main__":
    main()
