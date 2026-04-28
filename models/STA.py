from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional


def _to_immutable(value: Any) -> Any:
    if isinstance(value, tuple):
        return tuple(_to_immutable(item) for item in value)
    if isinstance(value, list):
        return tuple(_to_immutable(item) for item in value)
    if isinstance(value, MappingProxyType):
        return MappingProxyType({k: _to_immutable(v) for k, v in value.items()})
    if isinstance(value, dict):
        return MappingProxyType({k: _to_immutable(v) for k, v in value.items()})
    return value


@dataclass(frozen=True, slots=True)
class Constant:
    name: str
    type: str
    value: Any = None

@dataclass(frozen=True, slots=True)
class VariableType:
    kind: str
    base: str
    lower_bound: int | str
    upper_bound: int | str

@dataclass(frozen=True, slots=True)
class Variable:
    name: str
    type: Any
    initial_value: Optional[Any] = None
    transient: Optional[bool] = False
    accumulator: Optional[bool] = False

    def __post_init__(self):
        object.__setattr__(self, "initial_value", _to_immutable(self.initial_value))
        object.__setattr__(self, "type", _to_immutable(self.type))

@dataclass(frozen=True, slots=True)
class Literal:
    value: Any

@dataclass(frozen=True, slots=True)
class VariableReference:
    name: str

@dataclass(frozen=True, slots=True)
class BinaryExpression:
    op: str
    left: Expression
    right: Expression

@dataclass(frozen=True, slots=True)
class IfThenElse:
    condition: Expression
    then: Expression
    else_: Expression

@dataclass(frozen=True, slots=True)
class UnaryExpression:
    op: str
    exp: Expression

Expression = Literal | BinaryExpression | IfThenElse | VariableReference | UnaryExpression

@dataclass(frozen=True, slots=True)
class PropertyExpression:
    op: str
    operands: Mapping[str, Any]

    def __post_init__(self):
        object.__setattr__(self, "operands", _to_immutable(dict(self.operands)))

@dataclass(frozen=True, slots=True)
class Property:
    name: str
    expression: PropertyExpression

@dataclass(frozen=True, slots=True)
class Location:
    name: str
    timeProgress: Optional[Expression] = None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, value):
        if isinstance(value, Location):
            return self.name == value.name
        return False

@dataclass(frozen=True, slots=True)
class Distribution:
    type: str
    args: tuple[Expression, ...]

    def __post_init__(self):
        object.__setattr__(self, "args", tuple(_to_immutable(arg) for arg in self.args))

@dataclass(frozen=True, slots=True)
class Assignment:
    ref: str
    value: Expression | Distribution

    def __post_init__(self):
        object.__setattr__(self, "value", _to_immutable(self.value))

@dataclass(frozen=True, slots=True)
class Destination:
    location: str
    assignments: tuple[Assignment, ...]
    probability: Optional[Expression] = None

    def __post_init__(self):
        object.__setattr__(self, "assignments", tuple(_to_immutable(a) for a in self.assignments))
        object.__setattr__(self, "probability", _to_immutable(self.probability))

@dataclass(frozen=True, slots=True)
class Edge:
    from .state import State
    location: str
    guard: Optional[Expression]
    destinations: tuple[Destination, ...]

    def __post_init__(self):
        object.__setattr__(self, "guard", _to_immutable(self.guard))
        object.__setattr__(self, "destinations", tuple(_to_immutable(d) for d in self.destinations))

    def pickDestination(self):
        """
        Can be used to pick a destination based if multiple destinations are specified for an edge.
        Will use a probability distribution to choose destination.
        """

        #TODO. When implementing prob. distribution for edge destinations, implement this as well.
        ## I.e it should choose destination based on prob instead of always choosing the first entry.

        return self.destinations[0]

@dataclass
class Automaton:
    name: str
    locations: tuple[Location, ...]
    initial_locations: tuple[str, ...]
    variables: tuple[Variable, ...]
    edges: tuple[Edge, ...]

    def __post_init__(self):
        object.__setattr__(self, "locations", tuple(_to_immutable(loc) for loc in self.locations))
        object.__setattr__(self, "initial_locations", tuple(self.initial_locations))
        object.__setattr__(self, "variables", tuple(_to_immutable(var) for var in self.variables))
        object.__setattr__(self, "edges", tuple(_to_immutable(edge) for edge in self.edges))

    def getLocationByName(self, name: str) -> Optional[Location]:
        """
        Takes a `str` of the location name, and returns the `Location`. Returns `None` if not found.
        """
        for location in self.locations:
            if location.name == name:
                return location
        return None

    def getIncomingEdges(self, location: Location) -> list[Edge]:
        """
        Takes a `Location`, and returns a list of the edges which goes into the `Location`
        """
        incomingEdges = []
        for edge in self.edges:
            for destination in edge.destinations:
                if destination.location == location.name:
                    incomingEdges.append(edge)
        return incomingEdges


@dataclass(frozen=True, slots=True)
class Element:
    automaton: str

@dataclass(frozen=True, slots=True)
class System:
    elements: tuple[Element, ...]

    def __post_init__(self):
        object.__setattr__(self, "elements", tuple(_to_immutable(e) for e in self.elements))

@dataclass(frozen=True, slots=True)
class Model:
    jani_version: str
    name: str
    type: str
    features: Optional[tuple[str, ...]] = None
    constants: Optional[tuple[Constant, ...]] = None
    variables: Optional[tuple[Variable, ...]] = None
    properties: Optional[tuple[Property, ...]] = None
    automata: tuple[Automaton, ...] | None = None
    system: System | None = None

    def __post_init__(self):
        object.__setattr__(self, "features", None if self.features is None else tuple(self.features))
        object.__setattr__(self, "constants", None if self.constants is None else tuple(_to_immutable(c) for c in self.constants))
        object.__setattr__(self, "variables", None if self.variables is None else tuple(_to_immutable(v) for v in self.variables))
        object.__setattr__(self, "properties", None if self.properties is None else tuple(_to_immutable(p) for p in self.properties))
        object.__setattr__(self, "automata", None if self.automata is None else tuple(_to_immutable(a) for a in self.automata))
        object.__setattr__(self, "system", _to_immutable(self.system))
