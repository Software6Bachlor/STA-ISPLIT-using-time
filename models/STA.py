from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Constant:
    name: str
    type: str
    value: Any = None

@dataclass
class VariableType:
    kind: str
    base: str
    lower_bound: int | str
    upper_bound: int | str

@dataclass
class Variable:
    name: str
    type: Any
    initial_value: Optional[Any] = None
    transient: Optional[bool] = False

@dataclass
class Literal:
    value: Any

@dataclass
class VariableReference:
    name: str

@dataclass
class BinaryExpression:
    op: str
    left: Expression
    right: Expression

@dataclass
class IfThenElse:
    condition: Expression
    then: Expression
    else_: Expression

@dataclass
class UnaryExpression:
    op: str
    exp: Expression

Expression = Literal | BinaryExpression | IfThenElse | VariableReference | UnaryExpression

@dataclass
class PropertyExpression:
    op: str
    operands: dict[str, Any]

@dataclass
class Property:
    name: str
    expression: PropertyExpression

@dataclass
class Location:
    name: str
    timeProgress: Optional[Expression] = None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, value):
        if isinstance(value, Location):
            return self.name == value.name
        return False

@dataclass
class Distribution:
    type: str
    args: list[Expression]

@dataclass
class Assignment:
    ref: str 
    value: Expression | Distribution

@dataclass
class Destination:
    location: str
    assignments: list[Assignment]
    probability: Optional[Expression] = None

@dataclass
class Edge:
    from .state import State
    location: str
    guard: Expression
    destinations: list[Destination]

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
    locations: list[Location]
    initial_locations: list[str]
    variables: list[Variable]
    edges: list[Edge]

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

@dataclass
class Element:
    automaton: str

@dataclass
class System:
    elements: list[Element]

@dataclass
class Model:
    jani_version: str
    name: str
    type: str
    features: Optional[list[str]] = None
    constants: Optional[list[Constant]] = None
    variables: Optional[list[Variable]] = None
    properties: Optional[list[Property]] = None
    automata: list[Automaton] | None = None
    system: System | None = None
