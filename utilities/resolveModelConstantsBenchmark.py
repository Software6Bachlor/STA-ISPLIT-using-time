import os
import json
import tempfile
from chainModelBuilder import ChainModelBuilder

def resolveModelConstantsBenchmark(modelPath: str, newConstants: dict) -> str:
    with open(modelPath, encoding="utf-8-sig") as file:
        data = json.load(file)

    constants = data.get("constants", [])
    changed = False

    for constant in constants:
        if constant.get("value", None) is not None:
            continue
        elif newConstants is not None and constant.get("name") in newConstants:
            constant["value"] = newConstants[constant.get("name")]
            changed = True
            continue

    if _isChainTemplate(modelPath):
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
