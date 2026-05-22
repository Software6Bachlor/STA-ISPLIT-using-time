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
        "simElapsedSeconds": float(getattr(result, "simElapsed", 0.0)),         # <--- Cast to float
        "schedulerID": schedulerID,
        "maxTime": maxTime,
        "numTrials": int(getattr(result, "numTrials", 0)),                      # <--- Cast to int
        "numHits": int(getattr(result, "numHits", 0)),                          # <--- Cast to int
        "probabilityEstimate": float(getattr(result, "probabilityEstimate", 0.0)), # <--- Cast to float
        "generatedAtUtc": generatedAtUtc,
        "constants": constants,
        "experimentName": experimentName,
        "halfWidth": float(getattr(result, "halfWidth", 0.0)),                  # <--- Cast to float
        
        # --- THE FIX FOR YOUR CRASH ---
        "ciContainsZero": bool(getattr(result, "ciContainsZero", False)),       # <--- Cast to bool
        
        # For a list, we ensure it's a native Python list using list() 
        "weightedHitsList": list(getattr(result, "weightedHitsList", [])) if method == "restart" else None
    }
    
    if method == "restart":
        payload["ifElapsedSeconds"] = float(getattr(result, "ifElapsed", 0.0))
        # Ensure array properties are native Python lists
        payload["thresholds"] = list(getattr(result, "thresholds", []))
        payload["numRetrials"] = list(getattr(result, "numRetrials", [])) if isinstance(getattr(result, "numRetrials", []), (list, tuple)) else getattr(result, "numRetrials", 0)
        payload["weightedHits"] = float(getattr(result, "weightedHits", 0.0))
        payload["trialsWithHitTarget"] = int(getattr(result, "trialsWithHitTarget", 0))
        payload["configElapsedSeconds"] = float(configElapsed) if configElapsed is not None else None

    with open(outputPath, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)