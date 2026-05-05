import argparse
import json, os, sys, time
from datetime import datetime, timezone

from loader import loadData
from models.simulation import MonteCarloSimulation, MonteCarloResult
from parser import parseModel
from importanceFunctionBuilder import ImportanceFunctionBuilder

RESULTS_DIR = "/results" if os.path.isdir("/results") else os.path.join(os.path.dirname(__file__), "results")


def main():
	print("[START] Container execution started")

	# Print memory
	totalStart = time.perf_counter()

	parsedArgs = parseCliArgs(sys.argv)
	memoryMb = parseMemoryArg(parsedArgs)
	rareLocation = parseRareLocationArg(parsedArgs)
	modelPath = parseModelPathArg(parsedArgs)
	ifTimeLimit = parseIfTimeLimitArg(parsedArgs)
	numTrials = parsedArgs.numTrials
	timeBound = parsedArgs.timeBound

	loadStart = time.perf_counter()
	data = loadData(modelPath)
	loadElapsed = time.perf_counter() - loadStart
	print(f"[LOAD] Completed in {loadElapsed:.3f}s")

	parseStart = time.perf_counter()
	model = parseModel(data)
	parseElapsed = time.perf_counter() - parseStart
	print(f"[PARSE] Completed in {parseElapsed:.3f}s")

	# Build Importance Function
	IFStart = time.perf_counter()
	if model.automata and model.automata[0].locations:
		builder = ImportanceFunctionBuilder(model.automata[0], rareLocation, mbLimit=memoryMb, modelsVariables=model.variables, exponentialTruncationEpsilon=0.01, timeLimitSeconds=ifTimeLimit)
	else:
		raise ValueError("Model does not contain any automata or locations.")
	IFElapsed = time.perf_counter() - IFStart
	print(f"[IF] Completed in {IFElapsed:.3f}s")


	# Simulate
	print(f"[SIMULATION] Starting Monte Carlo simulation ({numTrials} trials)")
	simStart = time.perf_counter()

	STAsim = MonteCarloSimulation(model, numTrials, timeBound)
	result: MonteCarloResult = STAsim.run()

	simElapsed = time.perf_counter() - simStart
	print(f"[SIMULATION] Completed in {simElapsed:.3f}s — P̂ = {result.probabilityEstimate:.6g}  ε = {result.halfWidth:.6g}  0? = {'×' if result.ciContainsZero else '✓'}")


	writeStart = time.perf_counter()
	writeResult(modelPath, model, timeBound, result)
	writeElapsed = time.perf_counter() - writeStart
	print(f"[WRITE] Completed in {writeElapsed:.3f}s")

	totalElapsed = time.perf_counter() - totalStart
	print(f"[DONE] Total time {totalElapsed:.3f}s")


def parseCliArgs(args: list[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(add_help=True)
	parser.add_argument("--memoryMb", dest="memoryMb", type=int, required=True)
	parser.add_argument("--rareLocation", dest="rareLocation", type=str, default="loc_0")
	parser.add_argument("--ifTimeLimit", dest="ifTimeLimit", type=float)
	parser.add_argument("--numTrials", dest="numTrials", type=int, default=1000)
	parser.add_argument("--timeBound", dest="timeBound", type=float, required=True)
	parser.add_argument("modelPath", type=str)
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

def writeResult(modelPath: str, model, timeBound: float, result: MonteCarloResult) -> None:
	os.makedirs(RESULTS_DIR, exist_ok=True)
	modelName = getattr(model, "name", None)
	propertyName = model.properties[0].name if model.properties else None
	generatedAtUtc = datetime.now(timezone.utc).isoformat()
	generatedAtUtcFile = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
	outputPath = os.path.join(RESULTS_DIR, f"{modelName}_{generatedAtUtcFile}.json")

	payload = {
		"modelName": modelName,
		"selectedModelPath": modelPath,
		"property": propertyName,
		"method": "CMC",
		"timeBound": timeBound,
		"numTrials": result.numTrials,
		"numHits": result.numHits,
		"probabilityEstimate": result.probabilityEstimate,
		"halfWidth": result.halfWidth,
		"ciContainsZero": result.ciContainsZero,
		"generatedAtUtc": generatedAtUtc,
	}

	with open(outputPath, "w", encoding="utf-8") as file:
		json.dump(payload, file, indent=2)


if __name__ == "__main__":
	main()
