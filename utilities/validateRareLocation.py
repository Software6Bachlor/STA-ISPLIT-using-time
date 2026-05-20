
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
