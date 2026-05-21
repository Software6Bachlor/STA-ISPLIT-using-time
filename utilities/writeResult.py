import os
from datetime import datetime, timezone
import json
RESULTS_DIR = "./results"

# Notice we changed the type hint of 'result' to 'any' and added 'method'
def writeResult(modelPath: str, model, maxTime: float, result: any, method: str, schedulerID: int | None = None, constants: dict | None = None, experimentName: str | None = None, configElapsed: float | None = None) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    modelName = getattr(model, "name", None)
    propertyName = model.properties[0].name if model.properties else None
    generatedAtUtc = datetime.now(timezone.utc).isoformat()
    # Adding seconds (%S) just for extra safety
    generatedAtUtcFile = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")

    sched_suffix = f"_sched{schedulerID}" if schedulerID is not None else ""
    outputPath = os.path.join(RESULTS_DIR, f"{experimentName}_{modelName}_{method}{sched_suffix}_{generatedAtUtcFile}.json")
   
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
		"constants": constants,
		"experimentName": experimentName,
        "halfWidth": getattr(result, "halfWidth", 0.0),
        "ciContainsZero": getattr(result, "ciContainsZero", False),
        "weightedHitsList": getattr(result, "weightedHitsList", []) if method == "restart" else None
    }
	
    if method == "restart":
        payload["ifElapsedSeconds"] = getattr(result, "ifElapsed", 0.0)
        payload["thresholds"] = getattr(result, "thresholds", [])
        payload["numRetrials"] = getattr(result, "numRetrials", 0)
        payload["weightedHits"] = getattr(result, "weightedHits", 0.0)
        payload["trialsWithHitTarget"] = getattr(result, "trialsWithHitTarget", 0)
        payload["configElapsedSeconds"] = configElapsed

    with open(outputPath, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
