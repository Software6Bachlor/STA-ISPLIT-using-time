import ast
import json
import os
import sys
import subprocess
import argparse
import tempfile
from loader import retrieveModelNames, selectModels
from chainModelBuilder import ChainModelBuilder

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
    timeBound = parsedArgs.timeBound
    method = parsedArgs.method

    if selectedModelArg is None:
        models = retrieveModelNames()
        userInput = selectModels(models)
        selectedModel = os.path.abspath(str(userInput))
    else:
        selectedModel = os.path.abspath(selectedModelArg)

    selectedModel = resolveModelConstants(selectedModel)

    ensureDockerEngineAvailable()
    runDocker(memory, selectedModel, cpuLimit, rareLocation, ifTimeLimit, numTrials, timeBound, method)


def parseCliArgs(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-m", "--memoryMb", dest="memoryMb", type=int)
    parser.add_argument("--cpus", dest="cpus", type=float)
    parser.add_argument("--model", dest="modelPath", type=str)
    parser.add_argument("--rareLocation", dest="rareLocation", type=str, default="loc_0")
    parser.add_argument("--ifTimeLimit", dest="ifTimeLimit", type=float)
    parser.add_argument("--method", dest="method", choices=["mc", "restart"], default="mc")
    parser.add_argument("--numTrials", dest="numTrials", type=int, default=1000)
    parser.add_argument("--timeBound", dest="timeBound", type=float, default=None)
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


def _isChainTemplate(modelPath: str) -> bool:
    """Check if model is a chain template (filename indicates it)."""
    basename = os.path.basename(modelPath).lower()
    return "chain" in basename and basename.endswith(".jani")


def _extractConstantsAsDict(data: dict) -> dict:
    """Extract constants from JANI data as {name: value}."""
    constants_dict = {}
    for const in data.get("constants", []):
        name = const.get("name")
        value = const.get("value")
        if name is not None and value is not None:
            constants_dict[name] = value
    return constants_dict


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
            print(f"[MODEL] Generated chain model with {constants_dict.get('N', '?')} locations")
        except Exception as e:
            print(f"[ERROR] Failed to generate chain model: {e}")
            raise SystemExit(1)

        # Write concrete model to tempfile
        tempDir = tempfile.mkdtemp(prefix="chain-model-")
        tempPath = os.path.join(tempDir, os.path.basename(modelPath))
        with open(tempPath, "w", encoding="utf-8") as file:
            json.dump(concrete_data, file, indent=2)
        print(f"[MODEL] Wrote concrete chain model to {tempPath}")
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


def runDocker(memory: int, modelPath: str, cpuLimit: float | None = None, rareLocation: str = "loc_0", ifTimeLimit: float | None = None, numTrials: int = 1000, timeBound: float | None = None, method: str = "mc"):
    """Run the builder with the given memory limit
    Args:
        memory (int): Memory limit in MB
        modelPath (str): Absolute host path to the selected model file
        cpuLimit (float | None): Optional Docker CPU limit passed to --cpus
        rareLocation (str): Rare location
        ifTimeLimit (float | None): Optional Importance Function builder time limit
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
        "--memoryMb", str(memory),
        "--rareLocation", rareLocation,
    ]

    if ifTimeLimit is not None:
        command.extend(["--ifTimeLimit", str(ifTimeLimit)])

    command.extend(["--method", method])
    command.extend(["--numTrials", str(numTrials)])
    if timeBound is not None:
        command.extend(["--timeBound", str(timeBound)])
    command.append(containerModelPath)

    if cpuLimit is not None:
        command.insert(3, "--cpus")
        command.insert(4, str(cpuLimit))

    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("[HOST] Container execution completed successfully")


if __name__ == "__main__":
    main()
