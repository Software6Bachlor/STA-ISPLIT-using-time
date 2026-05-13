import pytest
from importanceFunctionBuilder import ImportanceFunctionBuilder
from pathlib import Path
from models.STA import *
from models.clock import Clock
from models.stateSnapshot import StateSnapShot
from loader import loadData
from models.RestartStaSimConfig import RestartSimulationConfig
from models.simulation import RestartSimulation
from parser import parseModel
from importanceFunctionBuilder import ImportanceFunctionBuilder

LARGE_DISTANCE = int(1e9)

def test_importanceFunctionBuilder_WhenTimeIsOverLimit_LargeDistance():

    modelPath = str(
        Path(__file__).resolve().parents[1]
        / "models"
        / "benchmark"
        / "jani"
        / "manufacturing-sta.jani"
    )
    data = loadData(modelPath)
    model = parseModel(data)
    if not model.automata or not model.automata[0].locations:
        pytest.fail("Model is not valid")

    builder = ImportanceFunctionBuilder(
        model.automata[0],
        "loc_0",
        mbLimit=200,
        modelsVariables=model.variables,
        exponentialTruncationEpsilon=0.01,
        timeLimitSeconds=None)

    imFu = builder.build()
    snapShot = StateSnapShot(
        locationName="loc_17",
        clocks=[Clock(name=name, value=1000 if name == "uptime" else 0)
                for name in builder.getClocksNames()],
    )
    score = imFu(snapShot)
    assert score == LARGE_DISTANCE, f"Expected importance score to be {LARGE_DISTANCE} when time is over limit, but got {score}"
