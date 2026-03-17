from .STA import Location, Variable, Model, Automaton, Edge, Expression
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

    def calculateEdgeTimeLeap(self, guard: Expression, state:State, automaton: Automaton) -> float:
        clockNames = self.getClockNames(automaton)
        


        
     
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

        if not timeLeaps:
            return state
        
        lowestTimeToNextEvent: float = min(timeLeaps)

        # Advance all clocks
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

    def step(self, state):
        """The master loop: Clone -> Reset Transients -> Time Travel -> Transition."""
        nextState = state.clone()
        
        # Reset transient variables
        self.restartTransientVariables(nextState)

        # 1. Fast forward to the exact millisecond of the next event
        self.fastForwardTime(nextState)
        
        # 2. See what events got triggered by that time jump
        validEdges = self.findEnabledEdges(nextState)
        
        # 3. If events are triggered, pick one and execute the changes
        if validEdges:
            chosenAuto, chosenEdge = random.choice(validEdges)
            self.ExecuteTransition(nextState, chosenAuto, chosenEdge)
            
        return nextState


class RestartSimulation(STASimulator):
           
    def run(self):
        pass        
