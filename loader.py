import json

# A JANI file is plain JSON, so loading it is just this:
with open("light_bulb.jani") as f:
    model = json.load(f)

# The top level tells you what kind of model it is
print(model["name"])       # light_bulb
print(model["type"])       # ctmc

# Automata are the components of the model.
# Each automaton has locations (states) and edges (transitions).
bulb = model["automata"][0]
print(bulb["name"])                    # Bulb
print(bulb["initial-locations"])       # ['working']

for location in bulb["locations"]:
    print("location:", location["name"])

for edge in bulb["edges"]:
    rate = edge["rate"]["exp"]         # the exponential rate of this transition
    dest = edge["destinations"][0]["location"]
    print(f"from '{edge['location']}' -> '{dest}'  at rate {rate}")