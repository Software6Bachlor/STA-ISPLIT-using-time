import json, os, sys, time
from datetime import datetime, timezone

from loader import loadData
from parser import parseModel
from importanceFunctionBuilder import ImportanceFunctionBuilder

RESULTS_DIR = "/results"


def main():
	print("[START] Container execution started")

	# Print memory
	totalStart = time.perf_counter()

	modelPath = parseModelPathArg(sys.argv)

	loadStart = time.perf_counter()
	data = loadData(modelPath)
	loadElapsed = time.perf_counter() - loadStart
	print(f"[LOAD] Completed in {loadElapsed:.3f}s")

	parseStart = time.perf_counter()
	model = parseModel(data)
	parseElapsed = time.perf_counter() - parseStart
	print(f"[PARSE] Completed in {parseElapsed:.3f}s")

	# Build Importance Function
	if model.automata and model.automata[0].locations:
		builder = ImportanceFunctionBuilder(model.automata[0], "loc_0", mbLimit=500)
	else:
		raise ValueError("Model does not contain any automata or locations.")


	writeStart = time.perf_counter()
	writePlaceholderResult(modelPath, model)
	writeElapsed = time.perf_counter() - writeStart
	print(f"[WRITE] Completed in {writeElapsed:.3f}s")

	totalElapsed = time.perf_counter() - totalStart
	print(f"[DONE] Total time {totalElapsed:.3f}s")


def parseModelPathArg(args: list[str]) -> str:
	if len(args) < 2:
		print("Missing selected model argument for containerMain.py")
		raise SystemExit(1)

	modelPath = args[1]
	if not os.path.isfile(modelPath):
		print(f"Selected model path inside container does not exist: {modelPath}")
		raise SystemExit(1)

	return modelPath

def writePlaceholderResult(modelPath: str, model) -> None:
	os.makedirs(RESULTS_DIR, exist_ok=True)
	modelName = getattr(model, "name", None)
	generatedAtUtc = datetime.now(timezone.utc).isoformat()
	generatedAtUtcFile = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
	outputPath = os.path.join(RESULTS_DIR, f"{modelName}_{generatedAtUtcFile}.json")

	payload = {
		"status": "placeholder",
		"selectedModelPath": modelPath,
		"modelName": modelName,
		"generatedAtUtc": generatedAtUtc,
		"notes": "Replace this placeholder payload with real output in a later step."
	}

	with open(outputPath, "w", encoding="utf-8") as file:
		json.dump(payload, file, indent=2)


if __name__ == "__main__":
	main()
