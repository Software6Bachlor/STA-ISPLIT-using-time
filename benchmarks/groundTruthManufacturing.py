
from random import random
import time
import random
from importanceFunctionBuilder import ImportanceFunctionBuilder
from models.RestartStaSimConfig import RestartSimulationConfig
from utilities.validateRareLocation import validateRareLocation
from loader import loadData
from models.simulation import MonteCarloResult, MonteCarloSimulation
from parser import parseModel
from utilities.resolveModelConstantsBenchmark import resolveModelConstantsBenchmark
from utilities.writeResult import writeResult
from models.simulation import RestartSimulation
from constants import FIXED_TIME_LIMIT


def groundTruthManufacturing(memoryMb, ifTimeLimit):
    constants = {
        "FAIL_W": 1.0, 
        "PASS_W": 9.0, 
        "TIME_BOUND": 10000.0
    }
    rareLocation = "loc_0"
    modelPath = "models/benchmark/jani/manufacturing-sta.jani"
    modelPath = resolveModelConstantsBenchmark(modelPath, constants)
    data = loadData(modelPath)
    model = parseModel(data)
    rareLocation = validateRareLocation(model, rareLocation)

    for method in ["mc"]:
        scheduler_ids = random.sample(range(0, 1000000), 48) 
        wallClockLimit = 86400/len(scheduler_ids) # divide the total time limit by the number of schedulers to get the time limit for each individual simulation
        
        for scheduler_id in scheduler_ids:
            if method == "mc":
                print(f"Running Monte Carlo Simulation for Manufacturing, Scheduler ID={scheduler_id}...")
                simStart = time.perf_counter()
                STAsim = MonteCarloSimulation(model, None, rareLocation, wallClockLimit, scheduler_id=scheduler_id, targetRelativeError=0.0000001)
                result: MonteCarloResult = STAsim.run()
                simElapsed = time.perf_counter() - simStart
                result.simElapsed = simElapsed
                writeResult(modelPath, model, STAsim.max_time, result, method="mc", schedulerID=scheduler_id, constants=constants, experimentName="fixed_time_manufacturing_mc")
           




    