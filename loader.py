import json

# Load the JANI file
with open("tests\\testData\\ModestSTA.jani", encoding="utf-8-sig") as f:
    model = json.load(f)

# Display model info
print(f"jani-version: {model['jani-version']}")
print(f"Model: {model['name']}")
print(f"Type: {model['type']}")
print()


# Display features
if "features" in model:
    print("Features:")
    for feature in model["features"]:
        print(f"  - {feature}")
    print()


# Display constants
if "constants" in model:
    print("Constants:")
    for const in model["constants"]:
        print(f"  - {const['name']}: {const['type']}")
    print()

# Display variables
if "variables" in model:
    print("Variables:")
    for var in model["variables"]:
        print(f"  - {var['name']}: {var['type']}")
    print()

# Display properties
if "properties" in model:
    print("Properties:")
    for prop in model["properties"]:
        print(f"  - {prop['name']}")
    print()

# Display automata
print("Automata:")
for automaton in model["automata"]:
    print(f"\n  Name: {automaton['name']}")
    print(f"  Initial locations: {automaton['initial-locations']}")
    
    print(f"  Locations: {[loc['name'] for loc in automaton['locations']]}")
    
    print(f"  Variables:")
    for var in automaton["variables"]:
        print(f"    - {var['name']}: {var['type']}")
    
    print(f"  Edges:")
    for edge in automaton["edges"]:
        src = edge["location"]
        dest = edge["destinations"][0]["location"]
        print(f"    {src} -> {dest}")

# Display system
for element in model["system"]:
    if "automaton" in element:
        print(f"\nSystem automaton: {element['automaton']}")