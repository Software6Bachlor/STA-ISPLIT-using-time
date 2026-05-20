


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
from constants import FIXED_RUNS_LIMIT


def fixedRunsChain(memoryMb, ifTimeLimit):
    constants = {"N": 25, "FAIL_W": 10, "PASS_W": 10, "TIME_BOUND": 300}
    runs = FIXED_RUNS_LIMIT 
    rareLocation = "loc_failure"
    modelPath = "models/benchmark/jani/chain-sta.jani" 
    modelPath = resolveModelConstantsBenchmark(modelPath, constants)
    data = loadData(modelPath)
    model = parseModel(data)
    rareLocation = validateRareLocation(model, rareLocation)

    for method in ["restart","mc"]:
        scheduler_ids = random.sample(range(0, 1000000), 5) 
        runs = runs/len(scheduler_ids) # divide the total time limit by the number of schedulers to get the time limit for each individual simulation

        if method == "restart":
            # cache the restart config and importance function builder since they are the same across schedulers for the same model and rare location
            IFStart = time.perf_counter()
            if model.automata and model.automata[0].locations:
                builder = ImportanceFunctionBuilder(model.automata[0], rareLocation, mbLimit=memoryMb, modelsVariables=model.variables, exponentialTruncationEpsilon=0.01, timeLimitSeconds=ifTimeLimit)
            else:
                raise ValueError("Model does not contain any automata or locations.")
            IFElapsed = time.perf_counter() - IFStart
            
            configStart = time.perf_counter()
            config = RestartSimulationConfig(model, rareLocation, builder).getConfig()
            configElapsed = time.perf_counter() - configStart
            
        for scheduler_id in scheduler_ids:
            if method == "mc":
                print(f"Running Monte Carlo Simulation for N={constants['N']}, Scheduler ID={scheduler_id}...")
                simStart = time.perf_counter()
                STAsim = MonteCarloSimulation(model, runs, rareLocation, None, scheduler_id=scheduler_id)
                result: MonteCarloResult = STAsim.run()
                simElapsed = time.perf_counter() - simStart
                result.simElapsed = simElapsed
                writeResult(modelPath, model, STAsim.max_time, result, method="mc", schedulerID=scheduler_id, constants=constants, experimentName="fixed_runs_chain_mc")
            elif method == "restart":
                print(f"Running Restart Simulation for N={constants['N']}, Scheduler ID={scheduler_id}...")
                simStart = time.perf_counter()
                STAsim = RestartSimulation(model, rareLocation, thresholds=config.Thresholds, numRetrials=config.NumRetrials, importanceFunctionBuilder=builder, confidence=0.95, relativeError=0.1, scheduler_id=scheduler_id,  branchLimit=runs)
                restartResult = STAsim.run()
                simElapsed = time.perf_counter() - simStart
                restartResult.ifElapsed = IFElapsed
                restartResult.simElapsed = time.perf_counter() - simStart
                writeResult(modelPath, model, STAsim.max_time, restartResult, method="restart", schedulerID=scheduler_id, constants=constants, experimentName="fixed_runs_chain_restart", configElapsed=configElapsed)


    