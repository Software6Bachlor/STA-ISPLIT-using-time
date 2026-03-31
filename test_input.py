from loader import loadData
from parser import parseModel

files = [
    "../../../03 - Ressources/Tools/Modest/Benchmarks/jani/long-sta.jani",
    "../../../03 - Ressources/Tools/Modest/Benchmarks/jani/manufacturing-sta.jani",
    "../../../03 - Ressources/Tools/Modest/Benchmarks/jani/tandem-queue.jani",
    "../../../03 - Ressources/Tools/Modest/Benchmarks/jani/chain-sta.jani",
]

for path in files:
    model = parseModel(loadData(path))
    print(f"OK  {model.name}  ({len(model.automata)} automata, {len(model.variables)} vars)")
