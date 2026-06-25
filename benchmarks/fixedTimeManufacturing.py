
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


def fixedTimeManufacturing(memoryMb, ifTimeLimit):
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
    print("Model parsed and loaded")
    print(f"Rare location found to be {rareLocation}")
    print(f"Constants: {constants}")
    input("enter to continue")
    for method in ["restart"]:
        scheduler_ids = random.sample(range(0, 1000000), 5) 
        wallClockLimit = FIXED_TIME_LIMIT/len(scheduler_ids) # divide the total time limit by the number of schedulers to get the time limit for each individual simulation

        if method == "restart":
            # cache the restart config and importance function builder since they are the same across schedulers for the same model and rare location
            IFStart = time.perf_counter()
            if model.automata and model.automata[0].locations:
                builder = ImportanceFunctionBuilder(model.automata[0], rareLocation, mbLimit=memoryMb, modelsVariables=model.variables, exponentialTruncationEpsilon=0.01, timeLimitSeconds=ifTimeLimit)
                print(f"Time Distances Computed: {len(builder.timeDistanceDict)} locations")
                print(f"Hop Distances Computed: {len(builder.hopDistanceDict)} locations")
                print("=====================\n")
                input("enter to continue")
            else:
                raise ValueError("Model does not contain any automata or locations.")
            IFElapsed = time.perf_counter() - IFStart
            
            configStart = time.perf_counter()
            config = RestartSimulationConfig(model, rareLocation, builder).getConfig()
            configElapsed = time.perf_counter() - configStart
            print(config)
            input("enter to continue")
            
            scheduler_id = scheduler_ids[0]            
            if method == "restart":
                print(f"Running Restart Simulation for Manufacturing, Scheduler ID={scheduler_id}...")
                simStart = time.perf_counter()
                STAsim = RestartSimulation(model, rareLocation, thresholds=config.Thresholds, numRetrials=config.NumRetrials, importanceFunctionBuilder=builder, confidence=0.95, relativeError=0.1, scheduler_id=scheduler_id, wallClockLimit=wallClockLimit)
                restartResult = STAsim.run()
                simElapsed = time.perf_counter() - simStart
                restartResult.ifElapsed = IFElapsed
                restartResult.simElapsed = time.perf_counter() - simStart
                writeResult(modelPath, model, STAsim.max_time, restartResult, method="restart", schedulerID=scheduler_id, constants=constants, experimentName="fixed_time_manufacturing_restart", configElapsed=configElapsed)





    