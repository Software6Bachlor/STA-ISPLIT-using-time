from importanceFunctionBuilder import ImportanceFunctionBuilder
from models.STA import Model
from simulation import RestartSimulation
from typing import NamedTuple

class SimulatorParameters(NamedTuple):
    Thresholds: list[int]
    NumRetrials: list[int]
    NumTrials: int

class RestartSimulationConfig(RestartSimulation):
    def __init__(self, model: Model ,rareLocation: str, importanceFunctionBuilder: ImportanceFunctionBuilder):
        self.model = model
        self.rareLocation = rareLocation
        self.importanceFunctionBuilder = importanceFunctionBuilder
    
    def getThresholds(self) -> list[int]:
        return [10, 5, 2] #Placeholder, can be made configurable later
    
    def getNumRetrials(self) -> list[int]:
        return [10, 5, 2] #Placeholder, can be made configurable later
    
    def getNumTrials(self) -> int:
        return 1 #Placeholder, can be made configurable later
    
    def getConfig(self) -> SimulatorParameters:
        return SimulatorParameters(
            Thresholds=self.getThresholds(),
            NumRetrials=self.getNumRetrials(),
            NumTrials=self.getNumTrials()
        )