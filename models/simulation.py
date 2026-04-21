from xml.parsers.expat import model
import sys
from .STA import Model, Edge, Expression, Automaton, Literal, VariableReference, BinaryExpression, Distribution, Destination, UnaryExpression
from .state import State
from typing import Optional
from utilities.intervals_intersection import intervals_intersection
from utilities.intervals_union import intervals_union
from utilities.get_initial_state import get_initial_state
from utilities.intervals_negated import intervals_negated
import random
from models.interval import Interval

from models import state


class STASimulator():
    def __init__(self, model: Model):
        self.model = model

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
        if newState.locations["Idle"] == "loc_17" and 400 < newState.globalVars["uptime"] < 500:
            print(f'19 < x_2 = {newState.autoVars["Idle"]["x_2"]} < 20')
            print(f'x_2 < cx_2 = {newState.autoVars["Idle"]["cx_2"]}')
            print(f'500 < uptime + x_2 = {newState.globalVars["uptime"] + newState.autoVars["Idle"]["x_2"]} < 501\n')
            
        # return the edge, timeUntilValid, and automaton name which requires the least amount of time units to have its guard satisfied.
            # If more edges have the same least time, randomly choose an edge uniformly.
            # should also return the times needed, as we need this to progress clocks .
        nextEdges: list[tuple[Edge, float, str]] = self.getNextValidEdges(newState)

        if nextEdges is None:
            return None

        nextEdge: tuple[Edge, float, str] = random.choice(nextEdges)
        
        # Choose destination based on probabilities if there are multiple.
        nextDestination : Destination = nextEdge[0].pickDestination()
        newState.locations[nextEdge[2]] = nextDestination.location

        # Update Pending assignments + most recent automaton
        newState.setRecentAutomaton(nextEdge[2])
        newState.setPendingAssignments(nextDestination.assignments)

        # Progress clocks.
        newState = self.incrementClocks(newState, nextEdge[1])

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

    def solve_guard(self, expr: 'Expression', state: State, automaton: Automaton) -> Optional[list[Interval]]:
        """Returns the interval of time >= 0 for when the expression will be True, or None if impossible."""
        if isinstance(expr, Literal):
            # If the literal is a boolean True, it's valid immediately (0.0). False is impossible (None).
            return [Interval(0, float("inf"), True, True)] if expr.value else None

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
        Prompts in the terminal for constants in `model` that needs to be set.
        """
        print("Enter values for constants")
        for constant in self.model.constants:
            constant.value = input(f"{constant.name}: ")
            
class RestartSimulation(STASimulator):
           
    def run(self):

        pass        

class SingleSimulation(STASimulator):
    def run(self):
        initialState = get_initial_state(self.model)
        
        self.getConstants()
        initialState.globalVars.update({c.name: c.value for c in self.model.constants})
        print(f"Locations: {initialState.locations}")
        print(f"Auto Variables: {initialState.autoVars}")
        print(f"Global Variables: {initialState.globalVars}")
        print(f"--------------------------------------------")
        i = 0
        newState: State = self.step(initialState)

        
        while True:
            i += 1
            print(i)
            print(f"Locations: {newState.locations}")
            print(f"Auto Variables: {newState.autoVars}")
            print(f"Global Variables: {newState.globalVars}")
            print(f"Pending Assignments: {newState.pendingAssignments}")
            print(f"--------------------------------------------")

            if (newState.locations["Idle"] == "loc_0"):
                print(f"iteration {i}, hit the rare event")
            
            newState = self.step(newState.clone())




            




