"""Test that generated chain model can be parsed."""
import json
import tempfile
import os
from chainModelBuilder import ChainModelBuilder
from parser import parseModel

# Generate a chain model with N=5
constants_dict = {
    "N": 5,
    "FAIL_W": 10,
    "PASS_W": 10,
    "TIME_BOUND": 1000.0
}

builder = ChainModelBuilder(constants_dict)
concrete_data = builder.buildModel()

# Write to temp file
tempDir = tempfile.mkdtemp(prefix="chain-parse-test-")
tempPath = os.path.join(tempDir, "chain-sta-test.jani")
with open(tempPath, "w", encoding="utf-8") as file:
    json.dump(concrete_data, file, indent=2)

# Load and parse
print("Loading generated model...")
with open(tempPath, encoding="utf-8-sig") as file:
    loaded_data = json.load(file)

print("Parsing model...")
try:
    parsed_model = parseModel(loaded_data)
    print(f"✓ Model parsed successfully")
    print(f"  Model name: {parsed_model.name}")
    print(f"  Automaton name: {parsed_model.automata[0].name}")
    print(f"  Number of locations: {len(parsed_model.automata[0].locations)}")
    print(f"  Location names: {[loc.name for loc in parsed_model.automata[0].locations]}")
    print(f"  Number of edges: {len(parsed_model.automata[0].edges)}")
    print(f"  Initial locations: {parsed_model.automata[0].initial_locations}")
    print(f"  Number of variables: {len(parsed_model.variables)}")
    print(f"  Automaton variables: {[v.name for v in parsed_model.automata[0].variables]}")
    print("\n✓ SUCCESS: Parser test passed")
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
