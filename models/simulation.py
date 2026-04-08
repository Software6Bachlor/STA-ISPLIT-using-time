from .STA import Location, Variable, Model, Automaton, Edge, Expression, VariableReference, Literal, BinaryExpression
from .state import State
import random


class STASimulator():
    def __init__(self, model: Model):
        self.model = model

    def getNextValidEdges(self, state: State) -> list[tuple[Edge, float]]:
        """
        From a state, this function returns the edges which requires the lest amount of time to pass.
        if multiple states requires the same amount of time, it returns them all.
        It will also return the time it takes for the edge to be true.
        """
        edgeTimes: list[tuple[Edge, float]] = []

        for automaton in self.model.automata:

            currentLocation = state.locations[automaton.name]

            outgoingEdges = [
                edge for edge in automaton.edges
                if edge.location == currentLocation
            ]

            for edge in outgoingEdges:
                time_until_valid = edge.calculateTimeUntilValid(edge.guard, state, automaton)

                if time_until_valid is not None:
                    edgeTimes.append((edge, time_until_valid))

        if not edgeTimes:
            return []
        
        # return edges that share lowest time until valid.
        currentLowestEdges: list[tuple[Edge, float]]  = []
        for edgeTime in edgeTimes:
            edgeTimes.remove(edge)
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
                        state.autoVars[var.name] = var.initial_value

    def getClockNames(self, automaton: Automaton):
        clockNames = []
        
        # 1. Check global variables 
        for var in self.model.variables:
            if getattr(var, 'type', None) == "clock":
                clockNames.append(var.name)
                
        # 2. Check local variables
        for var in automaton.variables:
            if getattr(var, 'type', None) == "clock":
                clockNames.append(var.name)
                
        return clockNames

    def calculateEdgeTimeLeap(self, guard: Expression, state: State, automaton: Automaton) -> float:
        # Get the clocks for this automaton
        clockNames = self.getClockNames(automaton)

        # Create the evaluator with the current context
        evaluator = GuardEvaluator(state, automaton, clockNames)
        return evaluator.evaluate_time_leap(guard)
        
    def evaluate(self, exp, state, autoName):
        """Recursively solves JANI math expressions and draws random distributions."""
        if hasattr(exp, 'value'): return exp.value
        
        if isinstance(exp, str):
            if exp in state.globalVars: return state.globalVars[exp]
            if exp in state.autoVars.get(autoName, {}): return state.autoVars[autoName][exp]

        if isinstance(exp, dict):
            if 'distribution' in exp:
                dist = exp['distribution']
                args = [self.evaluate(a, state, autoName) for a in exp['args']]
                if dist == "Exponential": return random.expovariate(args[0])
                if dist == "Normal": return random.normalvariate(args[0], args[1])

            if 'op' in exp:
                op = exp['op']
                left = self.evaluate(exp.get('left'), state, autoName)
                right = self.evaluate(exp.get('right'), state, autoName)

                if op == '+': return left + right
                if op == '-': return left - right
                if op == '*': return left * right
                if op == '/': return left / right if right != 0 else 0
                if op in ('≥', '>='): return left >= right
                if op in ('≤', '<='): return left <= right
                if op == '<': return left < right
                if op == '>': return left > right
                if op in ('∧', 'and'): return left and right
                if op in ('∨', 'or'): return left or right
                if op == '=': return left == right
                
        return None

    def fastForwardTime(self, state: State) -> State:
        # This function finds the next event that will happen from a given state and updates the clocks.

        timeLeaps: list[float] = []
        
        # This finds the lowest time until next event is taken.
        for auto in self.model.automata:
            currentLoc: str = state.locations[auto.name]
            for edge in auto.edges:
                if edge.location == currentLoc:
                    timeRemaining: float = self.calculateEdgeTimeLeap(edge.guard, state, auto)
                    if timeRemaining is not None:
                            timeLeaps.append(timeRemaining)

        #TODO if no edges, terminate.
        if not timeLeaps:
            return state
        
        lowestTimeToNextEvent: float = min(timeLeaps)

        # Advance all clocks
        # TODO : REDO c TO BE DYNAMICally all clocks.
        state.globalTime += lowestTimeToNextEvent
        for auto in self.model.automata:
            if "c" in state.autoVars[auto.name]:
                state.autoVars[auto.name]["c"] += lowestTimeToNextEvent
                
        return state

    def findEnabledEdges(self, state) -> list[(str, Edge)]:
        # Return a list of edges that are legal at the moment.
        enabledEdges: list[(str, Edge)] = []
        for auto in self.model.automata:
            currentLoc: Location = state.locations[auto.name]
            for edge in auto.edges:
                if edge.location == currentLoc:
                    if self.evaluate(edge.guard, state, auto.name):
                        enabledEdges.append((auto.name, edge))
        return enabledEdges

    def ExecuteTransition(self, state, chosenAuto, chosenEdge):
        """Moves the automaton and applies all variable assignments."""
        destination = chosenEdge.destinations[0] 
        state.locations[chosenAuto] = destination.location

        for assign in destination.assignments:
            ref = assign.ref
            new_val = self.evaluate(assign.value, state, chosenAuto)
            
            if ref in state.globalVars:
                state.globalVars[ref] = new_val
            else:
                state.autoVars[chosenAuto][ref] = new_val

    def step(self, state: State):
        """The master loop: Clone -> Reset Transients -> Time Travel -> Transition."""

        # Reset transient variables
        self.restartTransientVariables(state)

        #take the pending assignments of state and create the values for stochastic variables.
        print(state.pendingAssignments)

        # return the edge which requires the least amount of time units to have its guard satisfied.
            # If more edges have the same least time, randomly choose an edge uniformly.
            # should also return the times needed, as we need this to progress clocks .
        nextEdges: list[Edge] = self.getNextValidEdges(state)

        # Update Pending assignments + most recent automaton
        # Progress clocks.

        # return updated state.





        # 1. Fast forward to the exact millisecond of the next event
        state = self.fastForwardTime(state)
        
        # 2. See what events got triggered by that time jump
        validEdges = self.findEnabledEdges(state)
        
        # 3. If events are triggered, pick one and execute the changes
        if validEdges:
            chosenAuto, chosenEdge = random.choice(validEdges)
            self.ExecuteTransition(state, chosenAuto, chosenEdge)
            
        return state

class RestartSimulation(STASimulator):
           
    def run(self):
        pass        

class GuardEvaluator:
    def __init__(self, state, automaton, clock_names: list[str]):
        self.state = state
        self.automaton = automaton
        self.clock_names = clock_names

    def get_value(self, expr: Expression) -> float:
        """
        Extracts the current numerical value of variables or literals.
        """
        if isinstance(expr, Literal):
            return float(expr.value)
        
        if isinstance(expr, VariableReference):
            # If it's a clock, grab it from the automaton's local variables
            if expr.name in self.clock_names:
                return float(self.state.autoVars.get(self.automaton.name, {}).get(expr.name, 0.0))
            
            # Otherwise, assume it's a global variable (like an integer)
            return float(self.state.globalVars.get(expr.name, 0.0)) 
            
        raise ValueError(f"Unsupported expression for value extraction: {expr}")

    def evaluate_time_leap(self, expr: Expression) -> float:
        """
        Recursively calculates the minimum time leap to satisfy the expression.
        """
        if isinstance(expr, Literal):
            return 0.0 if expr.value else float('inf')

        if isinstance(expr, BinaryExpression):
            return self._evaluate_binary(expr)

        # Fallback for unexpected expression types
        return 0.0 

    def _evaluate_binary(self, expr: BinaryExpression) -> float:
        """
        Handles the logic for Binary Expressions specifically.
        """
        op = expr.op
        
        # --- Logical Operators ---
        if op in ("&&", "and", "∧"):
            return max(self.evaluate_time_leap(expr.left), self.evaluate_time_leap(expr.right))
        
        if op in ("||", "or", "∨"):
            return min(self.evaluate_time_leap(expr.left), self.evaluate_time_leap(expr.right))

        # --- Relational Operators ---
        left_is_clock = isinstance(expr.left, VariableReference) and expr.left.name in self.clock_names
        right_is_clock = isinstance(expr.right, VariableReference) and expr.right.name in self.clock_names
        
        # Case A: Clock is on the Left (e.g., clock >= 5)
        if left_is_clock and not right_is_clock:
            return self._evaluate_left_clock(op, self.get_value(expr.left), self.get_value(expr.right))
                
        # Case B: Clock is on the Right (e.g., 5 <= clock)
        elif right_is_clock and not left_is_clock:
            return self._evaluate_right_clock(op, self.get_value(expr.left), self.get_value(expr.right))
        
        # Case C: No clocks involved (Integers/Booleans evaluated instantly)
        else:
            return self._evaluate_static(op, self.get_value(expr.left), self.get_value(expr.right))

    # --- Helper Methods for Relational Logic ---

    def _evaluate_left_clock(self, op: str, clock_val: float, bound_val: float) -> float:
        if op in (">=", ">"):
            return max(0.0, bound_val - clock_val)
        elif op == "==":
            return bound_val - clock_val if bound_val >= clock_val else float('inf')
        elif op in ("<=", "<"):
            return 0.0 if clock_val <= bound_val else float('inf')
        return float('inf')

    def _evaluate_right_clock(self, op: str, bound_val: float, clock_val: float) -> float:
        if op in ("<=", "<"):  # 5 <= clock is the same as clock >= 5
            return max(0.0, bound_val - clock_val)
        elif op == "==":
            return bound_val - clock_val if bound_val >= clock_val else float('inf')
        elif op in (">=", ">"):  # 5 >= clock is the same as clock <= 5
            return 0.0 if clock_val <= bound_val else float('inf')
        return float('inf')

    def _evaluate_static(self, op: str, l_val: float, r_val: float) -> float:
        is_valid = False
        if op == "<": is_valid = l_val < r_val
        elif op == "<=": is_valid = l_val <= r_val
        elif op == ">": is_valid = l_val > r_val
        elif op == ">=": is_valid = l_val >= r_val
        elif op == "==": is_valid = l_val == r_val
        
        return 0.0 if is_valid else float('inf')