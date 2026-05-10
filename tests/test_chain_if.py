"""Test that generated chain model works with ImportanceFunctionBuilder."""
import json
import tempfile
import os
from chainModelBuilder import ChainModelBuilder
from parser import parseModel
from importanceFunctionBuilder import ImportanceFunctionBuilder

# Generate a small chain model with N=3
constants_dict = {
    "N": 3,
    "FAIL_W": 1,
    "PASS_W": 1,
    "TIME_BOUND": 100.0
}

builder = ChainModelBuilder(constants_dict)
concrete_data = builder.buildModel()

# Write to temp file
tempDir = tempfile.mkdtemp(prefix="chain-if-test-")
tempPath = os.path.join(tempDir, "chain-sta-test.jani")
with open(tempPath, "w", encoding="utf-8") as file:
    json.dump(concrete_data, file, indent=2)

# Load and parse
print("Loading and parsing generated model...")
with open(tempPath, encoding="utf-8-sig") as file:
    loaded_data = json.load(file)

parsed_model = parseModel(loaded_data)
print(f"✓ Model parsed: {parsed_model.name} with {len(parsed_model.automata[0].locations)} locations")

# Test importance function builder
print("\nInitializing ImportanceFunctionBuilder...")
try:
    rare_location = "loc_0"
    builder_if = ImportanceFunctionBuilder(
        parsed_model.automata[0],
        rare_location,
        mbLimit=1024,
        modelsVariables=parsed_model.variables,
        exponentialTruncationEpsilon=0.01,
        timeLimitSeconds=5
    )
    print(f"✓ ImportanceFunctionBuilder initialized for rare location: {rare_location}")
    print(f"  Locations processed: {len(parsed_model.automata[0].locations)}")
    print(f"  Edges processed: {len(parsed_model.automata[0].edges)}")
    print("\n✓ SUCCESS: ImportanceFunctionBuilder test passed")
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
