from .STA import Location, Variable, Model, Automaton, Edge
from abc import abstractmethod
import copy
import random

class State:
    def __init__(self):
        self.locations: dict[str, str] = {}                 # e.g., {"Arrivals": "loc_1", "Server": "loc_1"}
        self.globalVars: dict[str, float] = {}             # e.g., {"queue": 0, "served_customer": False}
        self.autoVars: dict[str, dict[str, float]] = {}    # e.g., {"Arrivals": {"c": 0, "x": 1.5}}
        self.globalTime: float = 0.0

    def clone(self) -> 'State':
        newState = State()
        newState.locations = copy.deepcopy(self.locations)
        newState.globalVars = copy.deepcopy(self.globalVars)
        newState.autoVars = copy.deepcopy(self.autoVars)
        newState.globalTime = self.globalTime
        return newState


class STASimulator():
    def __init__(self, model: Model):
        self.model = model

    def restart_transient_variables(self, state: State, model: Model = None):
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

    def _fast_forward_time(self, state: State) -> State:
        # This function finds the next event that will happen from a given state and updates the clocks.
        timeLeaps: list[float] = []
        
        for auto in self.model.automata:
            currentLoc: str = state.locations[auto.name]
            
            for edge in auto.edges:
                # Find the edge we are currently standing at
                if edge.location == currentLoc:
                    
                    # Look at the guard. In your JANI, guards are formatted as: (c >= x) AND (queue < 5)
                    # We ONLY want to check the right side (queue < 5) to see if the door is physically unlocked.
                    discreteGuard = edge.guard["exp"]["right"] 
                    isDiscretelyEnabled = self.evaluate(discreteGuard, state, auto.name)
                    
                    if isDiscretelyEnabled:
                        c: float = state.autoVars[auto.name]["c"]
                        x: float = state.autoVars[auto.name]["x"]
                        timeRemaining: float = max(0.0, x - c)
                        timeLeaps.append(timeRemaining)

        # Safety check: If no doors are unlocked, we are deadlocked. Don't skip time.
        if not timeLeaps:
            return state

        # The shortest time remaining is our next event
        delta_t: float = min(timeLeaps)

        # Advance all clocks and global time by delta_t
        state.globalTime += delta_t
        for auto in self.model.automata:
            if "c" in state.autoVars[auto.name]:
                state.autoVars[auto.name]["c"] += delta_t
                
        return state

    def _find_enabled_edges(self, state) -> list[(str, Edge)]:
        # Return a list of edges that are legal at the moment.
        enabledEdges: list[(str, Edge)] = []
        for auto in self.model.automata:
            currentLoc: Location = state.locations[auto.name]
            for edge in auto.edges:
                if edge.location == currentLoc:
                    if self.evaluate(edge.guard, state, auto.name):
                        enabledEdges.append((auto.name, edge))
        return enabledEdges

    def _execute_transition(self, state, chosenAuto, chosenEdge):
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

    def step(self, state):
        """The master loop: Clone -> Reset Transients -> Time Travel -> Transition."""
        nextState = state.clone()
        
        # Reset transient variables (like served_customer flashing True for only one tick)
        self.restart_transient_variables(nextState)

        # if "served_customer" in next_state.global_vars:
        #     next_state.global_vars["served_customer"] = False

        # 1. Fast forward to the exact millisecond of the next event
        self._fast_forward_time(nextState)
        
        # 2. See what events got triggered by that time jump
        validEdges = self._find_enabled_edges(nextState)
        
        # 3. If events are triggered, pick one and execute the changes
        if validEdges:
            chosenAuto, chosenEdge = random.choice(validEdges)
            self._execute_transition(nextState, chosenAuto, chosenEdge)
            
        return nextState


class RestartSimulation(STASimulator):
           
    def run(self):
        pass        
