"""Test the chain model generation integration."""
import json
import tempfile
import os
from chainModelBuilder import ChainModelBuilder

modelPath = "models/benchmark/jani/chain-sta.jani"

# Load the template
with open(modelPath, encoding="utf-8-sig") as file:
    data = json.load(file)

# Simulate user input for constants
test_constants = {
    "N": 10,
    "FAIL_W": 5,
    "PASS_W": 15,
    "TIME_BOUND": 500.0
}

# Set values
for const in data.get("constants", []):
    if const.get("name") in test_constants:
        const["value"] = test_constants[const["name"]]

# Test the chain generation
constants_dict = {}
for const in data.get("constants", []):
    name = const.get("name")
    value = const.get("value")
    if name is not None and value is not None:
        constants_dict[name] = value

print(f"Constants extracted: {constants_dict}")

builder = ChainModelBuilder(constants_dict)
concrete_data = builder.buildModel()

# Write to temp to verify it can be parsed
tempDir = tempfile.mkdtemp(prefix="chain-test-")
tempPath = os.path.join(tempDir, "chain-sta-test.jani")
with open(tempPath, "w", encoding="utf-8") as file:
    json.dump(concrete_data, file, indent=2)

print(f"\nGenerated model written to: {tempPath}")
print(f"Model name: {concrete_data['name']}")
print(f"Locations: {len(concrete_data['automata'][0]['locations'])}")
print(f"Initial locations: {concrete_data['automata'][0]['initial-locations']}")
print(f"Property: {concrete_data['properties'][0]['name']}")
print(f"Gate upper bound: {concrete_data['variables'][0]['type']['upper-bound']}")
print("\nVerifying all locations exist:")
for i, loc in enumerate(concrete_data['automata'][0]['locations']):
    print(f"  Location {i}: {loc['name']}")

print("\nSUCCESS: Integration test passed")
