from models.state import State
from models.STA import Model, Distribution, Literal
from .sample_distribution import sample_distribution

def get_initial_state(model: Model) -> State:
    """
    Takes a models, and returns the state of which would be the inital state.
    """
    state: State = State(
        locations={},
        globalVars={},
        autoVars={},
        globalTime=0.0
    )

    # 1. Initialize Automata Locations and Local Variables
    for automaton in model.automata:
        # Assuming the model has only one initial location per automaton
        if automaton.initial_locations:
            state.locations[automaton.name] = automaton.initial_locations[0]
        
        state.autoVars[automaton.name] = {}
        for var in automaton.variables:
            val = var.initial_value
            if isinstance(val, Distribution):
                val = sample_distribution(val, state)

            if isinstance(val, Literal):
                val = val.value
            # Fallback for other uninitialized variables
            elif val is None:
                val = 0.0 
            state.autoVars[automaton.name][var.name] = float(val) if isinstance(val, (int, float)) else val

    # 2. Initialize Global Variables
    if model.variables:
        for var in model.variables:
            val = var.initial_value
            
            if isinstance(val, Distribution):
                val = sample_distribution(val, state)
            if isinstance(val, Literal):
                val = val.value
            elif val is None:
                val = 0.0
            state.globalVars[var.name] = float(val) if isinstance(val, (int, float)) else val

    # 3. Return the fully formed State object

    return state