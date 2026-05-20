from main import benchmarkMain
import random
def runSimulationBenchmark():
    memory = 4000
    ifTimeLimit = 3600
    fixed_time_limit = 360 # 1 hour in seconds
############################################################################################
    # SCALING - CHAIN STA
    for N in range(1,21): #[1,2,3, ... ,20]
        constants = {"N": N, "FAIL_W": 10, "PASS_W": 10, "TIME_BOUND": 300}
        rareLocation = "loc_failure"
        selectedModelArg = "models/benchmark/jani/chain-sta.jani" 
        wallClockLimit = 1200
        for method in ["restart","mc"]:
            scheduler_ids = random.sample(range(0, 1000000), 5) 
            for scheduler_id in scheduler_ids:
                benchmarkMain(memory, ifTimeLimit, rareLocation, selectedModelArg, wallClockLimit, method, constants, None, scheduler_id, experimentName=f"scaling_chain_{N}_{method}")

    # # SCALING - LONG STA
    for i in range(1, 11): 
        current_y = 20 + (i * 10)  # Sweeps: 30, 40, 50, ..., 120

        constants = {
            "RARE_LO": 1.0, 
            "Y_THRESHOLD": current_y, 
            "TIME_BOUND": 100000.0 
        }
        rareLocation = "loc_0"
        selectedModelArg = "models/benchmark/jani/long-sta.jani"
        wallClockLimit = 1200
        for method in ["restart","mc"]:
            scheduler_ids = random.sample(range(0, 1000000), 5)
            for scheduler_id in scheduler_ids:
                benchmarkMain(memory, ifTimeLimit, rareLocation, selectedModelArg, wallClockLimit, method, constants, None, scheduler_id, experimentName=f"scaling_long_{current_y}_{method}")

# ############################################################################################
#    # FIXED TIME - CHAIN STA - 60 minutes
    constants = {"N": 25, "FAIL_W": 10, "PASS_W": 10, "TIME_BOUND": 100000.0}
    rareLocation = "loc_failure"
    selectedModelArg = "models/benchmark/jani/chain-sta.jani" 
    wallClockLimit = fixed_time_limit
    for method in ["restart","mc"]:
        scheduler_ids = random.sample(range(0, 1000000), 10) 
        wallClockLimit = fixed_time_limit/len(scheduler_ids)
        for scheduler_id in scheduler_ids:
            benchmarkMain(memory, ifTimeLimit, rareLocation, selectedModelArg, wallClockLimit, method, constants, None, scheduler_id, experimentName=f"fixed_time_chain")

#   FIXED TIME - LONG STA
    constants = {
        "RARE_LO": 1.0, 
        "Y_THRESHOLD": 200.0, 
        "TIME_BOUND": 100000.0 
    }
    rareLocation = "loc_0"
    selectedModelArg = "models/benchmark/jani/long-sta.jani"
    wallClockLimit = fixed_time_limit
    for method in ["restart","mc"]:
        scheduler_ids = random.sample(range(0, 1000000), 10)
        wallClockLimit = fixed_time_limit/len(scheduler_ids)
        for scheduler_id in scheduler_ids:
            benchmarkMain(memory, ifTimeLimit, rareLocation, selectedModelArg, wallClockLimit, method, constants, None, scheduler_id, experimentName=f"fixed_time_long")

#   FIXED TIME - MANUFACTURING STA
    constants = {
        "FAIL_W": 1.0, 
        "PASS_W": 9.0, 
        "TIME_BOUND": 10000.0
    }
    rareLocation = "loc_0"
    selectedModelArg = "models/benchmark/jani/manufacturing-sta.jani"
    wallClockLimit = fixed_time_limit
    for method in ["restart","mc"]:
        scheduler_ids = random.sample(range(0, 1000000), 10)
        wallClockLimit = fixed_time_limit/len(scheduler_ids)
        for scheduler_id in scheduler_ids:
            benchmarkMain(memory, ifTimeLimit, rareLocation, selectedModelArg, wallClockLimit, method, constants, None, scheduler_id, experimentName=f"fixed_time_manufacturing")

############################################################################################
    # TIME TO DISCOVERY - 








    ## Scaling benchmark.
    ## run chain sta på N = {1,2,3,4,5,6,7,8,9,10} x:axis - n, y axis: estimated probability +- error margin.  fail_w 1, pass_w: 9, time-bound = 100, 
    ## run long-sta with                            x-axis: y_threshold = 100 punkter mellem 0 og 20000, y axis: estimated probability +- error margin.
    ## run manufacturing :

    ## each scaling model will show different things:
        # CHAIN :Here we will make the rare event exponentially rarer, we expect the cmc to just crash at one point.
            # Has no time, so also to see if it it performs better on timeless models.
        # long : bread and butter - we can make the event rarer by increasing a threshold - to show that IF works on time.


    ## run fixed time
        # - real world test. we dont have infinite time, so we want to test the accuary per minute
        # but might make an imbalance bcs overhead of restart
        # will show that restart will run fewer steps, but be more accurate.

    ## run fixed runs
        #- Restart may be better, but how much overhead does it have?
        # Will show that restart has more overhead. but use the other test to show that this is okay.

    ## we might see that restart is heavier to run, but the fixed time shows us that its worth it.


    ## time to discovery
        # practical test. 
        # Which one is faster to hit their amount of rare events.

def runEvalDEL():
    benchmarkMain(memoryMb=4000, ifTimeLimit=3600)

if __name__ == "__main__":
    runEvalDEL()


