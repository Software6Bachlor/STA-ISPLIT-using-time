from models.STA import Distribution, Literal
import random

def sample_distribution(dist: Distribution) -> float:
    """Samples a random number based on the JANI/Modest distribution type."""
    # Assumes args are literals.
    args = []
    for arg in dist.args:
        if isinstance(arg, Literal):
            args.append(arg.value)
        else:
            raise ValueError(f"Expected Literal argument in initial distribution, got {type(arg)}")

    dist_type = dist.type.lower()
    
    # Map the AST string to standard Python random functions
    # (Adjust the string names based on exactly what your parser spits out)
    if dist_type in ('uniform', 'continuousuniform'):
        return random.uniform(args[0], args[1])
        
    elif dist_type == 'discreteuniform':
        # randint is inclusive of both bounds in Python
        return float(random.randint(int(args[0]), int(args[1])))
        
    elif dist_type in ('exponential', 'exp'):
        # args[0] is typically the rate (lambda) in JANI
        return random.expovariate(args[0])
        
    elif dist_type == 'normal':
        # args[0] = mean, args[1] = standard deviation
        return random.gauss(args[0], args[1])
        
    else:
        raise ValueError(f"Unsupported distribution type for initial state: {dist.type}")