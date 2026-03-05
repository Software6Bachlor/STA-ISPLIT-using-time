from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Constant:
    name: str
    type: int

@dataclass
class Variable:
    name: str
    type: Any
    initial_value: Optional[Any] = None
    transient: bool = False

@dataclass
class Expression:
    op: str
    operands: dict[str, any]

@dataclass
class Property:
    name: str
    expression: Expression

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
    guards: list[Expression]
    destinations: list[Destination]

@dataclass
class Automaton:
    name: str
    locations: list[Location]
    initial_locations: list[Location]
    variables: list[Variable]
    edges: list[Edge]

@dataclass
class System:
    elements: list[str]

@dataclass
class Model:
    jani_version: str
    name: str
    type: str
    features: Optional[list[str]] = None
    constants: Optional[list[Constant]] = None
    variables: Optional[list[Variable]] = None
    properties: Optional[list[Property]] = None
    automata: list[Automaton] = None
    system: System = None
