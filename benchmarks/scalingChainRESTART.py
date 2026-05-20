def scalingChainRESTART(config, ):
    for N in range(1,21): #[1,2,3, ... ,20]
        constants = {"N": N, "FAIL_W": 10, "PASS_W": 10, "TIME_BOUND": 300}
        rareLocation = "loc_failure"
        selectedModelArg = "models/benchmark/jani/chain-sta.jani" 
        wallClockLimit = 1200
        for method in ["restart","mc"]:
            scheduler_ids = random.sample(range(0, 1000000), 5) 
            for scheduler_id in scheduler_ids:
