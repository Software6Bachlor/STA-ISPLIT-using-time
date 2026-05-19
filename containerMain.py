import argparse
import json, os, sys, time
from datetime import datetime, timezone

from loader import loadData
from models.simulation import MonteCarloSimulation, MonteCarloResult, RestartSimulation
from models.RestartStaSimConfig import RestartSimulationConfig
from parser import parseModel
from importanceFunctionBuilder import ImportanceFunctionBuilder

RESULTS_DIR = "/results" if os.path.isdir("/results") else os.path.join(os.path.dirname(__file__), "results")


def main():
	#print("[START] Container execution started")

	totalStart = time.perf_counter()

	parsedArgs = parseCliArgs(sys.argv)
	memoryMb = parseMemoryArg(parsedArgs)
	modelPath = parseModelPathArg(parsedArgs)
	ifTimeLimit = parseIfTimeLimitArg(parsedArgs)
	schedulerID = getattr(parsedArgs, 'schedulerID', None)
	loadStart = time.perf_counter()
	data = loadData(modelPath)
	loadElapsed = time.perf_counter() - loadStart

	parseStart = time.perf_counter()
	model = parseModel(data)
	parseElapsed = time.perf_counter() - parseStart

	simStart = time.perf_counter()

	if parsedArgs.method == "mc":
		rareLocation = parseRareLocationArg(parsedArgs)
		numTrials = parsedArgs.numTrials
		wallClockLimit = parsedArgs.wallClockLimit
		if numTrials is None and wallClockLimit is None:
			print("--numTrials or --wallClockLimit is required for --method mc")
			raise SystemExit(1)
		mode = f"{wallClockLimit}s wall-clock" if wallClockLimit else f"{numTrials} trials"
		print(f"[SIMULATION] Starting Monte Carlo simulation ({mode})")
		STAsim = MonteCarloSimulation(model, numTrials, rareLocation, wallClockLimit, scheduler_id=schedulerID)
		result: MonteCarloResult = STAsim.run()
		simElapsed = time.perf_counter() - simStart
		result.simElapsed = simElapsed
		print(f"[SIMULATION] Completed in {simElapsed:.3f}s — P̂ = {result.probabilityEstimate:.6g}  ε = {result.halfWidth:.6g}  0? = {'×' if result.ciContainsZero else '✓'}")
		writeResult(modelPath, model, STAsim.max_time, result, method="mc", schedulerID=schedulerID)
	else:
		rareLocation = parseRareLocationArg(parsedArgs)
		rareLocation = validateRareLocation(model, rareLocation)

		IFStart = time.perf_counter()
		if model.automata and model.automata[0].locations:
			builder = ImportanceFunctionBuilder(model.automata[0], rareLocation, mbLimit=memoryMb, modelsVariables=model.variables, exponentialTruncationEpsilon=0.01, timeLimitSeconds=ifTimeLimit)
		else:
			raise ValueError("Model does not contain any automata or locations.")
		IFElapsed = time.perf_counter() - IFStart
		#print(f"[IF] Completed in {IFElapsed:.3f}s")

		#print(f"[CONFIG] Building simulation configuration")
		config = RestartSimulationConfig(model, rareLocation, builder).getConfig()
		#print(f" | Num Retrials: {config.NumRetrials}")
		print(f"[SIMULATION] Starting RESTART simulation")
		STAsim = RestartSimulation(model, rareLocation, thresholds=config.Thresholds, numRetrials=config.NumRetrials, importanceFunctionBuilder=builder, confidence=0.95, relativeError=0.1, scheduler_id=schedulerID)
		restartResult = STAsim.run()
		restartResult.ifElapsed = IFElapsed
		restartResult.simElapsed = time.perf_counter() - simStart
		writeResult(modelPath, model, STAsim.max_time, restartResult, method="restart", schedulerID=schedulerID)
		simElapsed = time.perf_counter() - simStart
		print(f"[SIMULATION] Completed in {simElapsed:.3f}s")

	totalElapsed = time.perf_counter() - totalStart
	print(f"[DONE] Total time {totalElapsed:.3f}s")


def parseCliArgs(args: list[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(add_help=True)
	parser.add_argument("--memoryMb", dest="memoryMb", type=int, required=True)
	parser.add_argument("--rareLocation", dest="rareLocation", type=str, default="loc_0")
	parser.add_argument("--ifTimeLimit", dest="ifTimeLimit", type=float)
	parser.add_argument("--method", dest="method", choices=["mc", "restart"], default="mc")
	parser.add_argument("--numTrials", dest="numTrials", type=int, default=None)
	parser.add_argument("--wallClockLimit", dest="wallClockLimit", type=float, default=None)
	parser.add_argument("modelPath", type=str)
	parser.add_argument("--schedulerID", type=int, default=None, help="Optional Random Seed / Scheduler ID for the simulation")
	return parser.parse_args(args[1:])


def parseMemoryArg(parsedArgs: argparse.Namespace) -> int:
	memoryMb = parsedArgs.memoryMb
	if memoryMb <= 0:
		print("Invalid memory argument. Please provide a positive integer in MB.")
		raise SystemExit(1)

	return memoryMb


def parseRareLocationArg(parsedArgs: argparse.Namespace) -> str:
	rareLocation = parsedArgs.rareLocation
	if not isinstance(rareLocation, str) or not rareLocation.strip():
		print("Invalid rare location. Please provide a non-empty location name for --rareLocation.")
		raise SystemExit(1)

	return rareLocation.strip()


def parseIfTimeLimitArg(parsedArgs: argparse.Namespace) -> float | None:
	ifTimeLimit = parsedArgs.ifTimeLimit
	if ifTimeLimit is not None and ifTimeLimit <= 0:
		print("Invalid time limit. Please provide a positive number for --ifTimeLimit.")
		raise SystemExit(1)

	return ifTimeLimit


def parseModelPathArg(parsedArgs: argparse.Namespace) -> str:
	modelPath = parsedArgs.modelPath
	if not modelPath:
		print("Missing selected model argument for containerMain.py")
		raise SystemExit(1)

	if not os.path.isfile(modelPath):
		print(f"Selected model path inside container does not exist: {modelPath}")
		raise SystemExit(1)

	return modelPath


def validateRareLocation(model, rareLocation: str) -> str:
	if not model.automata:
		print("Model does not contain automata to validate rare location.")
		raise SystemExit(1)

	firstAutomaton = model.automata[0]
	locationNames = {location.name for location in firstAutomaton.locations}
	if rareLocation not in locationNames:
		print(
			f"Invalid rare location '{rareLocation}' for automaton '{firstAutomaton.name}'. "
			f"Available locations: {sorted(locationNames)}"
		)
		raise SystemExit(1)

	return rareLocation

# Notice we changed the type hint of 'result' to 'any' and added 'method'
def writeResult(modelPath: str, model, maxTime: float, result: any, method: str, schedulerID: int | None = None) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    modelName = getattr(model, "name", None)
    propertyName = model.properties[0].name if model.properties else None
    generatedAtUtc = datetime.now(timezone.utc).isoformat()
    # Adding seconds (%S) just for extra safety
    generatedAtUtcFile = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    
    # --- FIX: Inject scheduler ID into the filename ---
    sched_suffix = f"_sched{schedulerID}" if schedulerID is not None else ""
    outputPath = os.path.join(RESULTS_DIR, f"{modelName}_{method}{sched_suffix}_{generatedAtUtcFile}.json")

    payload = {
        "modelName": modelName,
        "selectedModelPath": modelPath,
        "property": propertyName,
        "method": method,
		"simElapsedSeconds": getattr(result, "simElapsed", 0.0),
        "schedulerID": schedulerID,
        "maxTime": maxTime,
        "numTrials": getattr(result, "numTrials", 0),
        "numHits": getattr(result, "numHits", 0),
        "probabilityEstimate": getattr(result, "probabilityEstimate", 0.0),
        "generatedAtUtc": generatedAtUtc,
    }
	

    if method == "mc":
        payload["halfWidth"] = getattr(result, "halfWidth", 0.0)
        payload["ciContainsZero"] = getattr(result, "ciContainsZero", False)


    if method == "restart":
        payload["ifElapsedSeconds"] = getattr(result, "ifElapsed", 0.0)
        payload["thresholds"] = getattr(result, "thresholds", [])
        payload["numRetrials"] = getattr(result, "numRetrials", 0)


    with open(outputPath, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

if __name__ == "__main__":
	main()
