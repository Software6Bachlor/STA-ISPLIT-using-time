from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Constant:
    name: str
    type: int

@dataclass
class VariableType:
    kind: str
    base: int
    lower_bound: int
    upper_bound: int

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

Expression = Literal | BinaryExpression | IfThenElse | VariableReference

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
    timeProgress: Expression

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
    location: Location
    assignments: list[Assignment]

@dataclass
class Edge:
    location: Location
    guard: Expression
    destinations: list[Destination]

@dataclass
class Automaton:
    name: str
    locations: list[Location]
    initial_locations: list[Location]
    variables: list[Variable]
    edges: list[Edge]

    def getLocationByName(self, name: str) -> Optional[Location]:
        for location in self.locations:
            if location.name == name:
                return location
        return None

    def getIncomingEdges(self, location: Location) -> list[Edge]:
        incomingEdges = []
        for edge in self.edges:
            for destination in edge.destinations:
                if destination.location == location:
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
