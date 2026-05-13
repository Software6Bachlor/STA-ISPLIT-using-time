from importanceFunctionBuilder import ImportanceFunctionBuilder
from models.STA import Model
from models.simulation import PilotSimulation
from typing import NamedTuple

class SimulatorParameters(NamedTuple):
    Thresholds: list[int]
    NumRetrials: list[int]
    NumTrials: int

class RestartSimulationConfig():
    def __init__(self, model: Model, rareLocation: str, importanceFunctionBuilder: ImportanceFunctionBuilder):
        self.model = model
        self.rareLocation = rareLocation
        self.importanceFunctionBuilder = importanceFunctionBuilder
        self.PilotSim = PilotSimulation(model, rareLocation, importanceFunctionBuilder, confidence=0.95, relativeError=0.1)
    
    def getThresholds(self) -> list[int]:
        return self.PilotSim.run()
    
    def getNumRetrials(self, thresholds: list[int]) -> list[int]:
        return [2 for _ in thresholds]
    
    def getNumTrials(self) -> int:
        return 1 #Placeholder, can be made configurable later
    
    def getConfig(self) -> SimulatorParameters:
        thresholds = self.getThresholds()
        return SimulatorParameters(
            Thresholds=thresholds,
            NumRetrials=self.getNumRetrials(thresholds),
            NumTrials=self.getNumTrials()
        )