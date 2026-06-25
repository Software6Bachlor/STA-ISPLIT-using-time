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

def scalingChain(memoryMb, ifTimeLimit) -> None:
    for N in range(5,6): #[1,2,3, ... ,20]
        constants = {"N": N, "FAIL_W": 10, "PASS_W": 10, "TIME_BOUND": 300}
        wallClockLimit = 1800 
        rareLocation = "loc_failure"
        modelPath = "models/benchmark/jani/chain-sta.jani" 
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
            if method == "restart":
                # cache the restart config and importance function builder since they are the same across schedulers for the same model and rare location
                IFStart = time.perf_counter()
                if model.automata and model.automata[0].locations:
                    builder = ImportanceFunctionBuilder(model.automata[0], rareLocation, mbLimit=memoryMb, modelsVariables=model.variables, exponentialTruncationEpsilon=0.01, timeLimitSeconds=ifTimeLimit)
                    print(f"Time Distances Computed: {len(builder.timeDistanceDict)} locations")
                    print(f"Hop Distances Computed: {len(builder.hopDistanceDict)} locations")
                    print("=====================\n")
                else:
                    raise ValueError("Model does not contain any automata or locations.")
                IFElapsed = time.perf_counter() - IFStart
                input("enter to continue")
                configStart = time.perf_counter()
                config = RestartSimulationConfig(model, rareLocation, builder).getConfig()
                configElapsed = time.perf_counter() - configStart
                print(config)
                input("enter to continue")


                if method == "restart":
                    scheduler_id = scheduler_ids[0]
                    print(f"Running Restart Simulation for N={N}, Scheduler ID={scheduler_id}...")
                    simStart = time.perf_counter()
                    STAsim = RestartSimulation(model, rareLocation, thresholds=config.Thresholds, numRetrials=config.NumRetrials, importanceFunctionBuilder=builder, confidence=0.95, relativeError=0.1, scheduler_id=scheduler_id, wallClockLimit=wallClockLimit)
                    restartResult = STAsim.run()
                    simElapsed = time.perf_counter() - simStart
                    restartResult.ifElapsed = IFElapsed
                    restartResult.simElapsed = time.perf_counter() - simStart
                    writeResult(modelPath, model, STAsim.max_time, restartResult, method="restart", schedulerID=scheduler_id, constants=constants, experimentName="scaling_chain_restart", configElapsed=configElapsed)
