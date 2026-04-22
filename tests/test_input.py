from loader import loadData
from parser import parseModel

files = [
    "models/benchmark/jani/long-sta.jani",
    "models/benchmark/jani/chain-sta.jani",
    "models/benchmark/jani/tandem-queue.jani",
    "models/benchmark/jani/manufacturing-sta.jani",
]

for path in files:
    model = parseModel(loadData(path))
    print(f"OK  {model.name}  ({len(model.automata)} automata, {len(model.variables)} vars)")
