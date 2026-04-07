from models.state import State
from models.STA import Model, Distribution, Literal
from .sample_distribution import sample_distribution

def get_initial_state(model: Model) -> State:
    locations = {}
    globalVars = {}
    autoVars = {}

    # 1. Initialize Automata Locations and Local Variables
    for automaton in model.automata:
        # Assuming the model has only one initial location per automaton
        if automaton.initial_locations:
            locations[automaton.name] = automaton.initial_locations[0]
        
        autoVars[automaton.name] = {}
        for var in automaton.variables:
            val = var.initial_value
            # TODO LASSE NÅET HERTIL, INITIAL VARIABLES BLIVER IKKE SAT TIL Literals OG Distributions MEN BARE DICTS og INTS. OVERVEJ AT OPDATER PARSER. JEG HAR SAT TODO HVOR DET SKAL GØRES.
            if isinstance(val, Distribution):
                val = sample_distribution(val)

            if isinstance(val, Literal):
                val = val.value
            # If it's a clock and has no explicit initial value, default to 0.0
            elif val is None and getattr(var.type, 'kind', '') == 'clock':
                val = 0.0
            # Fallback for other uninitialized variables
            elif val is None:
                val = 0.0 
            autoVars[automaton.name][var.name] = float(val) if isinstance(val, (int, float)) else val

    # 2. Initialize Global Variables
    if model.variables:
        for var in model.variables:
            val = var.initial_value
            
            if isinstance(val, Distribution):
                val = sample_distribution(val)
            if isinstance(val, Literal):
                val = val.value
            elif val is None:
                val = 0.0
                
            globalVars[var.name] = float(val) if isinstance(val, (int, float)) else val

    # 3. Return the fully formed State object

    return State(
        locations=locations,
        globalVars=globalVars,
        autoVars=autoVars,
        globalTime=0.0
    )