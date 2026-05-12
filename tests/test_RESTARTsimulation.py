from models.simulation import RestartSimulation
from models.STA import Location
from loader import loadData
from parser import parseModel

def test_run():
    pass

def test_newSim():
    pass

def test_handleCrossings():
    pass

def test_detectThresholdCrossings():
    pass

def test_rmCalculator_singleThreshold():
    # Arrange
    from importanceFunctionBuilder import ImportanceFunctionBuilder
    data = loadData("tests/testData/manufacturing-sta.jani")
    model = parseModel(data)
    builder = ImportanceFunctionBuilder(model.automata[0], "loc_17", mbLimit=100, modelsVariables=model.variables)
    simulator = RestartSimulation(model=model, rareEventLocation="loc_17", thresholds=[10], numRetrials=[5], importanceFunctionBuilder=builder)

    # Act
    result = simulator.rmCalculator()

    # Assert
    assert result == 5
    