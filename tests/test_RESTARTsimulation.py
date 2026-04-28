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
    data = loadData("tests/testData/manufacturing-sta.jani")  
    model = parseModel(data)
    simulator = RestartSimulation(model=model, rareEventLocation="loc_17", thresholds=[10], numRetrials=[5], numTrials=1)
    
    # Act
    result = simulator.rmCalculator()

    # Assert
    assert result == 5
    