from models.STA import Expression, Model, Constant, Variable, PropertyExpression, Property, Automaton, System, Location, Distribution, Assignment, Destination, Edge

def parse_model(data: dict) -> Model:
    model = Model(
        name=data.get("name", ""),
        jani_version=data.get("jani_version", ""),
        type=data.get("type", ""),
        features=data.get("features", [])
    )
    model.constants = parse_constants(data.get("constants", []))
    model.variables = parse_variables(data.get("variables", []))
    model.properties = parse_properties(data.get("properties", []))
    model.automata = parse_automata(data.get("automata", []))
    model.system = None #tbd
    return model

def parse_constants(data: list[dict]) -> list[Constant]:
    constants = []
    for const in data:
        constants.append(Constant(
            name=const.get("name", ""),
            type=const.get("type", ""),
        ))
    return constants

def parse_variables(data: list[dict]) -> list[Variable]:
    variables = []
    for var in data:
        variables.append(Variable(
            name=var.get("name", ""),
            type=var.get("type", ""),
            initial_value=var.get("initial_value", None),
            transient=var.get("transient", False)
        ))
    return variables

def parse_properties(data: list[dict]) -> list[Property]:
    properties = []
    for prop in data:
        properties.append(Property(
            name=prop.get("name", ""),
            expression=PropertyExpression(
                op=prop.get("expression", "").get("op", ""),
                fun=prop.get("expression", "").get("fun", ""),
                values=prop.get("expression", "").get("values", {}),
                states=prop.get("expression", "").get("states", {})
            )
        ))
    return properties

def parse_automata(data: list[dict]) -> list[Automaton]:
    automata = []
    for auto in data:
        automata.append(Automaton(
            name=auto.get("name", ""),
            locations=parse_locations(auto.get("locations", [])),
            initial_locations=parse_locations(auto.get("initial_locations", [])),
            variables=parse_variables(auto.get("variables", [])),
            edges=parse_edges(auto.get("edges", []))
        ))
    return automata

def parse_locations(data: list[dict]) -> list[Location]:
    locations = []
    for loc in data:
        locations.append(Location(
            name=loc.get("name", ""),
            timeProgress=parse_expression(loc.get("timeProgress", {}))
        ))
    return locations

def parse_expression(data: dict) -> Expression:
    return Expression(
        op=data.get("op") if "op" in data else None,
        left=parse_expression(data.get("left", {})) if "left" in data else None,
        right=parse_expression(data.get("right", {})) if "right" in data else None,
        value=data.get("value") if "value" in data else None
    )

def parse_edges(data: list[dict]) -> list[Edge]:
    edges = []
    for edge in data:
        edges.append(Edge(
            location=parse_locations(edge.get("location", {})),
            guards=[parse_expression(g) for g in edge.get("guards", [])],
            destinations=parse_destinations(edge.get("destinations", []))
        ))
    return edges

def parse_destinations(data: list[dict]) -> list[Destination]:
    destinations = []
    for dest in data:
        destinations.append(Destination(
            location=parse_locations(dest.get("location", {})),
            assignments=parse_assignments(dest.get("assignments", []))
        ))
    return destinations

def parse_assignments(data: list[dict]) -> list[Assignment]:
    assignments = []
    for assign in data:
        value_data = assign.get("value", {})
        if "type" in value_data:  # Distribution
            value = Distribution(
                type=value_data.get("type", ""),
                args=[parse_expression(arg) for arg in value_data.get("args", [])]
            )
        else:  # Expression
            value = parse_expression(value_data)
        
        assignments.append(Assignment(
            ref=assign.get("ref", ""),
            value=value
        ))
    return assignments

def parse_system(data: dict) -> System:
    return System(
        composition=data.get("composition", ""),
        automata=parse_automata(data.get("automata", []))
    )