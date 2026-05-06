from xml.parsers.expat import model
from scipy import stats
import sys
from .STA import Model, Edge, Expression, Automaton, Literal, VariableReference, BinaryExpression, Distribution, Destination, UnaryExpression, Location
from .state import State
from typing import Callable, Optional
from utilities.intervals_intersection import intervals_intersection
from utilities.intervals_union import intervals_union
from utilities.get_initial_state import get_initial_state
from utilities.intervals_negated import intervals_negated
import time
import sys
from utilities.sample_delay import sample_delay
from importanceFunctionBuilder import ImportanceFunctionBuilder
import random
from models.interval import Interval
from models.clock import Clock

from models import state
import hashlib 
import time
from .stateSnapshot import StateSnapShot


class STASimulator():
    def __init__(self, model: Model, scheduler_id: int):
        self.model = model
        self.location_lookup = {}
        self.scheduler_id = scheduler_id
        
        for auto in self.model.automata:
            self.location_lookup[auto.name] = {loc.name: loc for loc in auto.locations} # Example {"IdleProcess": {"loc_1": LocationObject, "loc_2": LocationObject}}


    def getEdgesIntervals(self, state: State) -> list[tuple[Edge, list[Interval], str]]:

        edgesIntervals: list[tuple[Edge, list[Interval], str]] = []

        for automaton in self.model.automata:

            currentLocation = state.locations[automaton.name]

            outgoingEdges = [
                edge for edge in automaton.edges
                if edge.location == currentLocation
            ]

            for edge in outgoingEdges:
                edgeInterval = self.solve_guard(edge.guard, state, automaton)
                edgesIntervals.append((edge, edgeInterval, automaton.name))

        return edgesIntervals
        

    def getNextValidEdges(self, state: State) -> list[tuple[Edge, float, str]]:
        """
        From a state, this function returns the edges which requires the lest amount of time to pass.
        if multiple states requires the same amount of time, it returns them all.
        It will also return the time it takes for the edge to be true.
        """
        edgeTimes: list[tuple[Edge, float, str]] = []

        for automaton in self.model.automata:

            currentLocation = state.locations[automaton.name]

            outgoingEdges = [
                edge for edge in automaton.edges
                if edge.location == currentLocation
            ]

            for edge in outgoingEdges:
                time_until_valid = self.calculateTimeUntilEdgeBecomesValid(edge.guard, state, automaton)

                if time_until_valid is not None:
                    edgeTimes.append((edge, time_until_valid, automaton.name))

        if not edgeTimes:
            return []

        # return edges that share lowest time until valid.
        currentLowestEdges: list[tuple[Edge, float, str]]  = []
        for edgeTime in edgeTimes:
            edgeTimes.remove(edgeTime)
            if edgeTime[1] is not None:
                currentLowestEdges.append(edgeTime)
                break

        for edgeTime in edgeTimes[1:]:
            if edgeTime[1] is None:
                continue
            if edgeTime[1] < currentLowestEdges[0][1]:
                currentLowestEdges = [edgeTime]
            elif edgeTime[1] == currentLowestEdges[0]:
                currentLowestEdges.append(edgeTime)

        return currentLowestEdges

    def restartTransientVariables(self, state: State, model: Model = None):
        """
        Updates all transient variables in a state to their initial value.
        """
        if model is None:
            model = self.model

        # Global transient variables reset
        for var in model.variables:
            if(var.transient == True):
                if var.name in state.globalVars:
                    state.globalVars[var.name] = var.initial_value

        # Local transient variables reset
        for automaton in model.automata:
            for var in automaton.variables:
                if(var.transient == True):
                    if automaton.name in state.autoVars and var.name in state.autoVars[automaton.name]:
                        state.autoVars[automaton.name][var.name] = var.initial_value

    def step(self, oldState: State):
        """The master loop: Reset Transients -> Time Travel -> Transition."""
        
        newState: State = oldState.clone()

        # Reset transient variables
        self.restartTransientVariables(newState)


        #take the pending assignments of state and create the values for stochastic variables.
        self.handlePendingAssignments(oldState, newState)


        # find out how long we can stay in location
        invariantInterval: list[Interval] = self.getInvariantInterval(newState) # eg 0, 10
        # all edges with their interval in current state, as well as their automaton
        edgeIntervals: list[tuple[Edge, list[Interval], str]] = self.getEdgesIntervals(newState)
        valid_edge_intervals = [edgeInterval[1] for edgeInterval in edgeIntervals if edgeInterval[1] is not None]

        if not valid_edge_intervals:
            raise RuntimeError(f"Deadlock Detected: No outgoing edges are ever valid from state '{oldState}'.")

        edgesIntervalUnion: list[Interval] = intervals_union(*valid_edge_intervals)


        # If the invariant doesn't even allow t=0, the system is stuck.
        if not invariantInterval or (not invariantInterval[0].include_lower and invariantInterval[0].lower == 0.0):
             raise RuntimeError(f"Timelock Detected: Invariants violated at t=0 in state '{oldState}'.")
        
        
        unconstrained_delay = sample_delay(edgesIntervalUnion)
        invariant_max_time = invariantInterval[-1].upper if invariantInterval else float("inf")
        delay = min(unconstrained_delay, invariant_max_time)


     

        newState = self.incrementClocks(newState, delay)


        #Get valid edges after delay.
            # str here is auto_name
        valid_edges_after_delay: list[tuple[Edge, str]] = []
        for edge, interval_list, auto_name in edgeIntervals:
            is_edge_valid = False

            #If interval is none, edge is never valid
            if interval_list is None:
                continue
            # Check if the sampled delay falls inside this edge's intervals
            for interval in interval_list:
                if interval.include_lower:
                    lower_ok = delay >= interval.lower
                else:
                    lower_ok = delay > interval.lower
                    
                if interval.include_upper:
                    upper_ok = delay <= interval.upper
                else:
                    upper_ok = delay < interval.upper
                    
                if lower_ok and upper_ok:
                    is_edge_valid = True
                    break # The delay is valid for this edge, no need to check its other intervals

            if is_edge_valid:
                valid_edges_after_delay.append((edge, auto_name))

        if not valid_edges_after_delay:
            raise RuntimeError(f"No edges valid at sampled delay {delay}.")

       # use lss scheduler to resolve action non-determinism.
        chosen_edge = None

        if len(valid_edges_after_delay) == 1:
            chosen_edge = valid_edges_after_delay[0]

        else:
            # LSS Hash Logic
            state_signature = newState.get_signature()
            
            # Using hashlib for cross-process stability 
            stable_hash = int(hashlib.md5(state_signature.encode('utf-8')).hexdigest(), 16)
            
            # Combine the state hash with the Master Node's Scheduler ID
            combined_seed = stable_hash ^ self.scheduler_id 
            
            lss_rng = random.Random(combined_seed)
            chosen_edge = lss_rng.choice(valid_edges_after_delay)

        destinations = chosen_edge[0].destinations
        weights = []
        
        for dest in destinations:
            if dest.probability is None:
                prob_value = 1.0
            else:
                prob_value = newState.evaluateExpression(dest.probability)

            weights.append(prob_value)
            
        winning_dest = random.choices(destinations, weights=weights, k=1)[0]

        # Update new state
        newState.locations[chosen_edge[1]] = winning_dest.location
        newState.setRecentAutomaton(chosen_edge[1])
        newState.setPendingAssignments(winning_dest.assignments)

        return newState

    def handlePendingAssignments(self, oldState: State, newState: State):
        """
        Performs the assignments located in the pending assignments list of a state.
        """
        from utilities.sample_distribution import sample_distribution

        for assignment in oldState.pendingAssignments:
            value: float
            if isinstance(assignment.value, Distribution):
                value = sample_distribution(assignment.value, oldState)
            elif isinstance(assignment.value, Expression):
                value = oldState.evaluateExpression(assignment.value)
            newState.setVariable(assignment.ref, value)

    def incrementClocks(self, state: State, time: float):
        """
        Loops through all clocks of `state` and increments them all with  `time`
        """

        state.globalTime += time

        for var in self.model.variables:
            if getattr(var, 'type', '') == "clock":
                    state.globalVars[var.name] += time

        for automaton in self.model.automata:
            for var in automaton.variables:
                if getattr(var, 'type', '') == "clock":
                    state.autoVars[automaton.name][var.name] += time

        return state
    
    def calculateTimeUntilEdgeBecomesValid(self, guard: Expression, state: State, automaton: Automaton) -> Optional[float]:
        """
        Calculates based on clocks in `guard` the amount of time it will take until an `Edge` becomes valid.
        `None` means it will never become valid in the current `State`
        """
        if not guard:
            return 0.0
            
        interval = self.solve_guard(guard, state, automaton)
        if interval is None:
            return None
        else:
            # interval will always be sorted.
            return interval[0].lower

    def solve_guard(self, expr: 'Expression', state: State, automaton: Automaton | str) -> Optional[list[Interval]]:
        if isinstance(automaton, str):
            for a in self.model.automata:
                if a.name == automaton:
                    automaton = a
            

        """Returns the interval of time >= 0 for when the expression will be True, or None if impossible."""
        if isinstance(expr, VariableReference):
            val = state.getVariable(expr.name)
            if val is None:
                raise ValueError(f"Variable {expr.name} not found in state.")
            return [Interval(0.0, float("inf"), True, True)] if val else None

        if isinstance(expr, Literal):
            # If the literal is a boolean True, it's valid immediately (0.0). False is impossible (None).
            return [Interval(0, float("inf"), True, True)] if expr.value else None
        if isinstance(expr, VariableReference):
            value = state.getVariable(expr.name)
            if value == True:
                return [Interval(0, float("inf"), True, True)]
            elif value == False:
                return None
        if isinstance(expr, UnaryExpression):
            op = expr.op
            if op == "¬":
                t = self.solve_guard(expr.exp, state, automaton)
                return intervals_negated(t)

        if isinstance(expr, BinaryExpression):
            op = expr.op
            # --- LOGICAL OPERATORS ---
            if op == '∧':  # AND
                t_left = self.solve_guard(expr.left, state, automaton)
                t_right = self.solve_guard(expr.right, state, automaton)
                if t_left is None or t_right is None:
                    return None
                return intervals_intersection(t_left, t_right)
                
            if op == '∨':  # OR
                t_left = self.solve_guard(expr.left, state, automaton) # [(0,1)]
                t_right = self.solve_guard(expr.right, state, automaton) # [(2, inf)]
                if t_left is None: return t_right
                if t_right is None: return t_left
                return intervals_union(t_left, t_right)

            # --- RELATIONAL OPERATORS ---
            l_val, l_rate = self.evaluate_term(expr.left, state, automaton)
            r_val, r_rate = self.evaluate_term(expr.right, state, automaton)

            # Calculate required change (V) and combined rate of change (R)
            R = l_rate - r_rate
            V = r_val - l_val
            # c1 < 5
            # V = 5
            # R = 1
            # V/R = 5 - mængde af tidsenheder vi mangler før expression bliver true.
            
            # c1 < 5 + c2
            # V = 5
            # R = 0
            # V/R = 5/0 = inf.

            
            # Når R>0 - rate af venstre side er højere.
                # hvis V/R er negativ betyder det af expression er true lige nu.
                # hvis V/R er positiv vil den blive true om V/R tidsenheder.
            if op in ('≥'):
                if R > 0 and V/R > 0: return [Interval(V/R, float("inf"), True, True)]
                if R > 0 and V/R <= 0: return [Interval(0.0, float("inf"), True, True)]
                if R < 0 and V/R >= 0: return [Interval(0.0, V/R, True, True)]
                if R < 0 and V/R < 0: return None
                if R == 0:
                    if V <= 0: return [Interval(0.0, float("inf"), True, True)]
                    if V > 0: return None

            if op in ('>'):
                if R > 0 and V/R > 0: return [Interval(V/R, float("inf"), False, True)]
                if R > 0 and V/R <= 0: return [Interval(0.0, float("inf"), True, True)]
                if R < 0 and V/R >= 0: return [Interval(0.0, V/R, True, False)]
                if R < 0 and V/R < 0: return None
                if R == 0:
                    if V < 0: return [Interval(0.0, float("inf"), True, True)]
                    if V >= 0: return None
                    
            # R positiv betyder at rate of change på venstre side er størst.
            # altså vil expression være true fra
            if op in ('≤'):
                if R > 0 and V/R >= 0: return [Interval(0.0, V/R, True, True)]
                if R > 0 and V/R < 0: return None
                if R < 0 and V/R > 0: return [Interval(V/R, float("inf"), True, True)]
                if R < 0 and V/R <= 0: return [Interval(0.0, float("inf"), True, True)]
                if R == 0:
                    if V >= 0: return [Interval(0.0, float("inf"), True, True)]
                    if V < 0: return None

            if op in ('<'):
                if R > 0 and V/R >= 0: return [Interval(0.0, V/R, True, False)]
                if R > 0 and V/R < 0: return None
                if R < 0 and V/R > 0: return [Interval(V/R, float("inf"), False, True)]
                if R < 0 and V/R <= 0: return [Interval(0.0, float("inf"), True, True)]
                if R == 0:
                    if V > 0: return [Interval(0.0, float("inf"), True, True)]
                    if V <= 0: return None
                
            if op in ('=', '=='):
                if R != 0:
                    return [Interval(V/R, V/R, True, True)] if V/R >= 0 else None
                if R == 0: return [Interval(0.0, float("inf"), True, True)] if 0 == V else None

        raise ValueError(f"Unsupported guard expression: {expr}")

    def evaluate_term(self, expr: 'Expression',state: State, automaton: Automaton) -> tuple[float, float]:
        """Returns (current_value, rate_of_change) for a mathematical expression."""
        if isinstance(expr, Literal):
            return float(expr.value), 0.0
        if isinstance(expr, VariableReference):
            var_name = expr.name
            # 1. Check if it's a global variable (rate is 0.0)
            if var_name in state.globalVars:
                return float(state.globalVars[var_name]), 0.0
                
            # 2. Check if it's an automaton variable
            if var_name in state.autoVars[automaton.name]:
                val = float(state.autoVars[automaton.name][var_name])
                # Determine if it's a clock to set the rate of change
                is_clock = False
                for v in automaton.variables:
                    if v.name == var_name and getattr(v, 'type', '') == "clock":
                        is_clock = True
                        break
                return val, 1.0 if is_clock else 0.0
                
        if isinstance(expr, BinaryExpression):
            l_val, l_rate = self.evaluate_term(expr.left, state, automaton)
            r_val, r_rate = self.evaluate_term(expr.right, state, automaton)
            
            if expr.op == '+': return l_val + r_val, l_rate + r_rate
            if expr.op == '-': return l_val - r_val, l_rate - r_rate

            
        raise ValueError(f"Unsupported term for evaluation: {expr}")

    def getConstants(self):
        """
        Prompts in the terminal for constants and casts them to the correct type.
        """
        print("--- Setting Model Constants ---")
        for constant in self.model.constants:
            raw_value = input(f"{constant.name} ({constant.type}): ")
            
            try:
                if constant.type == "real":
                    constant.value = float(raw_value)
                elif constant.type == "int":
                    constant.value = int(raw_value)
                elif constant.type == "bool":
                    # Handles 'true', 'True', '1' as True; others as False
                    constant.value = raw_value.lower() in ("true", "1", "t", "yes")
                else:
                    # Fallback to strings
                    constant.value = raw_value
            except ValueError:
                print(f"Error: Could not convert '{raw_value}' to {constant.type}. Using 0.0 as fallback.")
                constant.value = 0.0


    def getInvariantInterval(self, state: State) -> list[Interval]:
        currentInvariants: list[tuple[str, Expression, str]] = [] #[(ex: loc_1, cx <= 10, Idle)]
        
        currentCeiling: list[Interval]= [Interval(0,float("inf"), True, True)]
        #loop through the location of each automaton to find the invariant.
        for auto_name, loc_name in state.locations.items():
            current_loc = self.location_lookup[auto_name][loc_name]
            if current_loc.timeProgress is not None:
                currentInvariants.append((current_loc.name, current_loc.timeProgress, auto_name))

        # Find the interval of how long we can stay according to the invariant.


        for loc_name, expr, auto_name in currentInvariants:
            inv_interval = self.solve_guard(expr, state, auto_name)
            if inv_interval is None:
                return []
            currentCeiling = intervals_intersection(currentCeiling, inv_interval)

        return currentCeiling

        
            

            
class RestartSimulation(STASimulator):
        def __init__(self, model: Model, rareEventLocation: str, thresholds: list[int], numRetrials: list[int], importanceFunctionBuilder: ImportanceFunctionBuilder, confidence: float = 0.95, relativeError: float = 0.1):
            super().__init__(model)
            # Find the automaton that has the location of the rare event.
            self.automaton = next((automaton for automaton in self.model.automata
                                   if any(loc.name == rareEventLocation for loc in automaton.locations)), None)
            self.importanceFunctionBuilder = importanceFunctionBuilder
            self.importanceFunction = importanceFunctionBuilder.build()
            self.thresholds = thresholds
            self.numRetrials = numRetrials
            self.rareEvents = 0
            self.numTrials = 0
            z = stats.norm.ppf(1 - (1 - confidence) / 2)
            self.numHits = int((z / relativeError) ** 2)


        def run(self):
            while self.rareEvents < self.numHits:
                self.numTrials += 1
                initialState = get_initial_state(self.model)
                initialState.globalVars.update({c.name: c.value for c in self.model.constants})
                self.newSim(initialState, None)
            print(f"Simulation concluded.")
            r_m = self.rmCalculator()
            totalRareEventProbability = self.rareEvents / (self.numTrials * r_m)
            print(f"Estimated Probability of Rare Event: {totalRareEventProbability}\nTotal Trials:{self.numTrials}\nRetrial Factor:{r_m}.")

        def newSim(self, state: State, startZone: Optional[int]):
            score = self.calculateScore(state)
            currentZone = startZone if startZone is not None else self.getThreshold(score)
            deepestZone = currentZone

            currentZone, deepestZone = self.handleCrossings(currentZone, startZone, score, state, deepestZone)
            if currentZone == "kill":
                return
            
            while True:
                nextState = self.step(state.clone())
                if nextState is None:
                    # Deadlock reached, stop this simulation.
                    return
                
                score = self.calculateScore(nextState)
                if score == 0:
                    self.rareEvents += 1
                    print(f"Rare events: {self.rareEvents} out of {self.numHits}.")
                    return
                
                currentZone, deepestZone = self.handleCrossings(currentZone, startZone, score, nextState, deepestZone)
                if currentZone == "kill":
                    return
                state = nextState

        def handleCrossings(self, currentZone: int, startZone: int, score: int, state: State, deepestZone: int) -> tuple[int, int]:
            crossing = self.detectThresholdCrossings(currentZone, score)
            if crossing == "down":
                currentZone += 1
                if currentZone > deepestZone:
                    deepestZone = currentZone
                    for _ in range(self.numRetrials[currentZone - 1] - 1):
                        self.newSim(state.clone(), currentZone)
            elif crossing == "up":
                if currentZone == startZone:
                    return "kill", deepestZone
                currentZone -= 1
            return currentZone, deepestZone

        def detectThresholdCrossings(self, currentZone: int, score: int) -> Optional[str]:
            if currentZone < len(self.thresholds) and score <= self.thresholds[currentZone]:
                return "down"
            elif currentZone > 0 and score > self.thresholds[currentZone-1]:
                return "up"
            else:
                return None
            
        def rmCalculator(self) -> int:
            r_m = 1
            for retrials in self.numRetrials:
                r_m *= retrials
            return r_m
        
        def calculateScore(self, state: State) -> int:
            snapshot = state._createSnapshot(self.automaton.name, self.importanceFunctionBuilder.getClocksNames())
            return self.importanceFunction(snapshot)
        
        def getThreshold(self, score: int) -> int:
            if score is None:
                return 0
            for i, threshold in enumerate(self.thresholds):
                if score > threshold:
                    return i
            return 0


class SingleSimulation(STASimulator):
    def __init__(self, model, scheduler_id: int):
        super().__init__(model, scheduler_id)

    def run_single_trace(
        self, 
        current_state, 
        target_automaton: str, 
        target_location: str, 
        max_time: float,
    ):
        """
        Runs one simulation path until it hits the target location, times out, or deadlocks.
        """
        seen_states = set()

        while True:
            try:
                previous_time = current_state.globalTime

                current_state = self.step(current_state)
                
                if current_state.globalTime > max_time:
                    return current_state, "timeout"

                if current_state.locations.get(target_automaton) == target_location:
                    return current_state, "success"

                time_passed = current_state.globalTime - previous_time
                state_sig = current_state.get_signature()

                if time_passed == 0.0:
                    if state_sig in seen_states:
                        return current_state, "deadlock" 
                    seen_states.add(state_sig)
                else:
                    seen_states.clear()
                    
            except RuntimeError:
                return current_state, "deadlock"
            

class MonteCarloSimulation(SingleSimulation):
    
    def run(
        self, 
        target_automaton: str, 
        target_location: str, 
        iterations: int = 100000
    ):
        """
        Runs multiple traces from the INITIAL state.
        """
        outcomes = {"success": 0, "timeout": 0, "deadlock": 0}
        
        # Safely get the TIME_BOUND constant, default to infinity if missing
        time_bound_const = next((c for c in self.model.constants if c.name == "TIME_BOUND"), None)
        max_time = time_bound_const.value if time_bound_const else float("inf")
        
        print(f"\nStarting Standard Monte Carlo ({iterations} runs)...")
        print(f"Target: Automaton '{target_automaton}' reaching '{target_location}' within {max_time} time units")
        start_time = time.time()

        for i in range(1, iterations + 1):
            current_state = get_initial_state(self.model)
            current_state.globalVars.update({c.name: c.value for c in self.model.constants})
            
            _, reason = self.run_single_trace(current_state, target_automaton, target_location, max_time)
            outcomes[reason] += 1

            # 3. Terminal UI
            elapsed = time.time() - start_time
            sps = i / elapsed if elapsed > 0 else 0
            percent = (i / iterations) * 100
            
            sys.stdout.write(
                f"\r[{i}/{iterations}] {percent:>3.0f}% | "
                f"Found ({target_location}): {outcomes['success']} | "
                f"SPS: {sps:>6.2f} | "
                f"Deadlocks: {outcomes['deadlock']}"
            )
            sys.stdout.flush()

        total_time = time.time() - start_time
        print(f"\n\n✅ Monte Carlo Complete in {total_time:.2f}s")
        print(f"Final Success Rate: {(outcomes['success']/iterations)*100:.2f}%")
        
        return outcomes

class PilotSimulation(RestartSimulation):
    def __init__(self, model: Model, rareEventLocation: str, importanceFunctionBuilder: ImportanceFunctionBuilder, confidence: float, relativeError: float):
        super().__init__(
            model=model,
            rareEventLocation=rareEventLocation,
            thresholds=[],
            numRetrials=[],
            importanceFunctionBuilder=importanceFunctionBuilder,
            confidence=confidence,
            relativeError=relativeError
            )
        self.confidence = confidence
        self.relativeError = relativeError
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        self.minCrossings = int((z / relativeError) ** 2)
        self.minLocationChanges = 1000

    def run(self) -> list [int]:
        """
        Adaptively place thresholds stage by stage.
        Stage 1: crude simulation to place T1
        Stage N: RESTART with existing thresholds to place T_{N+1}
        """

        # Stage 1: crude simulation to place T1
        print("Stage 1: crude pilot to find T1")
        initialState = get_initial_state(self.model)
        initialState.globalVars.update({c.name: c.value for c in self.model.constants})
        observedScores = self.runTrial(
            state=initialState,
            startZone=None
        )

        if not observedScores:
            raise ValueError("No scores observed in pilot simulation. Cannot place thresholds.")    
        T1 = self.computeMedian(observedScores)
        self.thresholds.append(T1)
        print(f"Placed T1 at: {T1}")
        observedScores.clear()

        # Stage N: RESTART with existing thresholds to place T_{N+1}
        stage = 2
        while True:
            print(f"Stage {stage}:")
            while len(observedScores) < self.minCrossings:
                initialState = get_initial_state(self.model)
                initialState.globalVars.update({c.name: c.value for c in self.model.constants})
                observedScores = self.runTrial(
                    state=initialState,
                    startZone=None
                )

            nextThreshold = self.computeMedian(observedScores)
            if nextThreshold <= 0:
                # Threshold placed at rare event boundary, stop placing thresholds, rare event is reachable from here.
                break

            if nextThreshold >= self.thresholds[-1]:
                # Threshold did not get placed closer to the rare event, stop placing thresholds, rare event is reachable from here.
                break
            self.thresholds.append(nextThreshold)
            print(f"Placed T{stage} at: {nextThreshold}")
            stage += 1
            observedScores.clear()
        return self.thresholds


    def runTrial(self, state: State, startZone: int, observedScores: list[int] = []) -> list[int]:
        """
        Run a short simulation using the current thresholds (All thresholds gets two retrials, R=2). Return all scores observed below the last threshold. If no thresholds, return all scores, since we are in the initial stage.
        """

        score = self.calculateScore(state)
        currentZone = startZone if startZone is not None else self.getThreshold(score)
        deepestZone = currentZone

        while len(observedScores) < self.minCrossings:
            nextState = self.step(state.clone())

            if nextState is None:
                # Deadlock reached, start fresh trial.
                state = get_initial_state(self.model)
                state.globalVars.update({c.name: c.value for c in self.model.constants})
                continue

            score = self.calculateScore(nextState)

            if score == 1000000000:
                #rare event is unreachable from this state, stop trial and start a new one.
                state = get_initial_state(self.model)
                state.globalVars.update({c.name: c.value for c in self.model.constants})
                continue

            if len(self.thresholds) == 0 or score < self.thresholds[-1]:
                observedScores.append(score)
                if len(observedScores) >= self.minCrossings:
                    # Enough crossings observed to place next threshold, stop simulation for this stage.
                    break
            
            if len(self.thresholds) > 0:
                currentZone, deepestZone = self.handleCrossings(currentZone, startZone, score, nextState, observedScores, deepestZone)
                if currentZone == "kill" or len(observedScores) >= self.minCrossings:
                    break

            state = nextState
        return observedScores
    
    def handleCrossings(self, currentZone: int, startZone: int, score: int, state: State, observedScores: list[int], deepestZone: int) -> tuple[int, int]:
        """
        Overrides the handleCrossings function from RestartSimulation to also keep track of observed scores when crossings happens during the pilot simulation.
        """
        crossing = self.detectThresholdCrossings(currentZone, score)
        if crossing == "down":
            currentZone += 1
            if currentZone > deepestZone:
                deepestZone = currentZone
                for _ in range(2 - 1): # R=2 for pilot simulation
                    self.runTrial(state.clone(), currentZone, observedScores)
        elif crossing == "up":
            if currentZone == startZone:
                return "kill", deepestZone
            currentZone -= 1
        return currentZone, deepestZone

    def computeMedian(self, scores: list[int]) -> int:
        """
        Compute the median of a list of scores. If even amount of scores, it returns the lower median, since we want to place the threshold as close to the rare event as possible.
        """
        sortedScores = sorted(scores)
        n = len(sortedScores)
        if n == 0:
            return 0
        if n % 2 == 1:
            return sortedScores[n // 2]
        else:
            return sortedScores[(n // 2) - 1]