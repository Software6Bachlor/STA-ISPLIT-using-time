from models.STA import BinaryExpression, Expression, Literal, Model, Constant, Variable, PropertyExpression, Property, Automaton, System, Location, Distribution, Assignment, Destination, Edge, VariableType, VariableReference, IfThenElse, Element, UnaryExpression

def parseModel(data: dict) -> Model:
    model = Model(
        jani_version=data["jani-version"],
        name=data["name"],
        type=data["type"],
        features=data.get("features", [])
    )
    model.constants = parseConstants(data.get("constants", []))
    model.variables = parseVariables(data.get("variables", []))
    model.properties = parseProperties(data.get("properties", []))
    model.automata = parseAutomata(data.get("automata", []))
    model.system = parseSystem(data.get("system", {}))
    return model

def parseConstants(data: list[dict]) -> list[Constant]:
    constants = []
    for const in data:
        constants.append(Constant(
            name=const.get("name", ""),
            type=const.get("type", ""),
        ))
    return constants

def parseVariableType(data: dict) -> VariableType:
    return VariableType(
        kind=data.get("kind", ""),
        base=data.get("base", ""),
        lower_bound=data.get("lower-bound", 0),
        upper_bound=data.get("upper-bound", 0)
    )

def parseVariables(data: list[dict]) -> list[Variable]:
    variables = []
    for var in data:
        initial_data = var.get("initial-value", None)
        if isinstance(initial_data, dict) and "distribution" in initial_data:
            initial_value = Distribution(
                type=initial_data.get("distribution", ""),
                args=[parseExpression(arg) for arg in initial_data.get("args", [])]
            )
        else:
            initial_value = initial_data
        variables.append(Variable(
            name=var.get("name", ""),
            type=var.get("type", "") if not isinstance(var.get("type", ""), dict) else parseVariableType(var.get("type", {})),
            initial_value=initial_value,
            transient=var.get("transient", False)
        ))
    return variables

def parsePropertyExpression(data: dict) -> PropertyExpression:
    propertyOperations = {"filter", "Pmax", "Pmin", "Emin", "Emax", "F", "G", "U", "initial"}

    op = data["op"]
    operands = {}
    for key, value in data.items():
        if key == "op":
            continue
        if isinstance(value, dict) and value.get("op") in propertyOperations:
            operands[key] = parsePropertyExpression(value)
        elif isinstance(value, dict) and "op" in value:
            operands[key] = parseExpression(value)
        elif isinstance(value, dict):
            operands[key] = {k: parseExpression(v) for k, v in value.items()}
        elif isinstance(value, str) and key != "fun":
            operands[key] = parseExpression(value)
        elif isinstance(value, str):
            operands[key] = value  # "fun" is always a keyword string in JANI, not a variable
        else:
            operands[key] = value
    return PropertyExpression(op=op, operands=operands)

def parseProperties(data: list[dict]) -> list[Property]:
    properties = []
    for prop in data:
        properties.append(Property(
            name=prop.get("name", ""),
            expression=parsePropertyExpression(prop.get("expression", {}))
        ))
    return properties

def parseAutomata(data: list[dict]) -> list[Automaton]:
    automata = []
    for auto in data:
        automata.append(Automaton(
            name=auto.get("name", ""),
            locations=parseLocations(auto.get("locations", [])),
            initial_locations=auto.get("initial-locations", []),
            variables=parseVariables(auto.get("variables", [])),
            edges=parseEdges(auto.get("edges", []))
        ))
    return automata

def parseLocations(data: list[dict]) -> list[Location]:
    locations = []
    for loc in data:
        locations.append(Location(
            name=loc.get("name", ""),
            timeProgress = parseExpression(loc.get("time-progress", {}).get("exp", {})
        )))
    return locations

def parseExpression(data: dict | str | int | float | bool) -> Expression | None:
    match data:
        case str():
            return VariableReference(name=data)
        case int() | float() | bool():
            return Literal(value=data)
        case {"op": "ite", "if": if_, "then": then, "else": else_}:
            return IfThenElse(
                condition=parseExpression(if_),
                then=parseExpression(then),
                else_=parseExpression(else_)
            )
        case {"op": op, "exp": exp_}:
            return UnaryExpression(op=op, exp=parseExpression(exp_))
        case {"op": op, "left": left, "right": right}:
            return BinaryExpression(
                op=op,
                left=parseExpression(left),
                right=parseExpression(right)
            )

def parseEdges(data: list[dict]) -> list[Edge]:
    edges = []
    for edge in data:
        edges.append(Edge(
            location=edge.get("location", ""),
            guard=parseExpression(edge.get("guard", {}).get("exp", {})),
            destinations=parseDestinations(edge.get("destinations", []))
        ))
    return edges

def parseDestinations(data: list[dict]) -> list[Destination]:
    destinations = []
    for dest in data:
        prob_data = dest.get("probability")
        probability = parseExpression(prob_data["exp"]) if prob_data else None
        destinations.append(Destination(
            location=dest.get("location", ""),
            assignments=parseAssignments(dest.get("assignments", [])),
            probability=probability
        ))
    return destinations

def parseAssignments(data: list[dict]) -> list[Assignment]:
    assignments = []
    for assign in data:
        value_data = assign.get("value", {})
        if not isinstance(value_data, dict):
            value = parseExpression(value_data)
        elif "distribution" in value_data:  # Distribution
            value = Distribution(
                type=value_data.get("distribution", ""),
                args=[parseExpression(arg) for arg in value_data.get("args", [])]
            )
        else:  # Expression
            value = parseExpression(value_data)
        
        assignments.append(Assignment(
            ref=assign.get("ref", ""),
            value=value
        ))
    return assignments

def parseSystem(data: dict) -> System:
    elements = []
    for elem in data.get("elements", []):
        elements.append(Element(automaton=elem.get("automaton", "")))
    return System(elements=elements)