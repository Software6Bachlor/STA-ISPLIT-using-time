"""
ChainModelBuilder: Generates a chain STA model with N concrete locations.

Transforms a symbolic chain template (with N as undefined constant) into
a concrete JANI model where the automaton has N locations (loc_0 through loc_N-1).
"""

import json


class ChainModelBuilder:
    """Builds a chain STA model with N locations based on resolved constants."""

    def __init__(self, constants_dict: dict):
        """
        Initialize builder with resolved constants.

        Args:
            constants_dict: Dictionary {name: value} for N, FAIL_W, PASS_W, TIME_BOUND
        """
        self.N = int(constants_dict.get("N", 1))
        self.FAIL_W = int(constants_dict.get("FAIL_W", 1))
        self.PASS_W = int(constants_dict.get("PASS_W", 1))
        self.TIME_BOUND = float(constants_dict.get("TIME_BOUND", 1000.0))

        if self.N <= 0:
            raise ValueError(f"N must be positive, got {self.N}")
        if self.FAIL_W <= 0 or self.PASS_W <= 0:
            raise ValueError(f"FAIL_W and PASS_W must be positive")
        if self.TIME_BOUND <= 0:
            raise ValueError(f"TIME_BOUND must be positive, got {self.TIME_BOUND}")

    def buildModel(self) -> dict:
        """
        Build and return a complete JANI model with N concrete locations.

        Returns:
            dict: JANI model ready for parsing
        """
        return {
            "jani-version": 1,
            "name": f"chain-sta-n{self.N}",
            "type": "sta",
            "features": ["derived-operators"],
            "constants": self._buildConstants(),
            "variables": self._buildVariables(),
            "properties": self._buildProperties(),
            "automata": [self._buildAutomaton()],
            "system": {"elements": [{"automaton": "Chain"}]},
        }

    def _buildConstants(self) -> list:
        """Build constants list with concrete values."""
        return [
            {"name": "N", "type": "int", "value": self.N},
            {"name": "FAIL_W", "type": "int", "value": self.FAIL_W},
            {"name": "PASS_W", "type": "int", "value": self.PASS_W},
            {"name": "TIME_BOUND", "type": "real", "value": self.TIME_BOUND},
        ]

    def _buildVariables(self) -> list:
        """Build model-level variables (gate, failure)."""
        return [
            {
                "name": "gate",
                "type": {
                    "kind": "bounded",
                    "base": "int",
                    "lower-bound": 0,
                    "upper-bound": self.N - 1,  # Concrete upper bound
                },
                "initial-value": 0,
            },
            {"name": "failure", "type": "bool", "initial-value": False},
        ]

    def _buildProperties(self) -> list:
        """Build reachability property for rare event (loc_0)."""
        return [
            {
                "name": "P_Failure",
                "expression": {
                    "op": "filter",
                    "fun": "max",
                    "values": {
                        "op": "Pmax",
                        "exp": {
                            "op": "F",
                            "exp": "failure",
                            "time-bounds": {"upper": self.TIME_BOUND},
                        },
                    },
                    "states": {"op": "initial"},
                },
            }
        ]

    def _buildAutomaton(self) -> dict:
        """Build automaton with N locations and edges."""
        return {
            "name": "Chain",
            "locations": self._buildLocations(),
            "initial-locations": ["loc_0"],
            "variables": [
                {"name": "cx", "type": "clock", "initial-value": 0},
                {"name": "x", "type": "real", "initial-value": 0},
            ],
            "edges": self._buildEdges(),
        }

    def _buildLocations(self) -> list:
        """Build N locations (loc_0 through loc_N-1)."""
        locations = []
        for i in range(self.N):
            loc_name = f"loc_{i}"
            # Time progress condition: allow time to pass unless in failure state
            # or already at terminal condition
            time_progress = {
                "op": "∧",
                "left": {
                    "op": "¬",
                    "exp": "failure",
                },
                "right": {
                    "op": "≤",
                    "left": "cx",
                    "right": "x",
                },
            }
            locations.append(
                {
                    "name": loc_name,
                    "time-progress": {"exp": time_progress},
                }
            )
        locations.append(
            {
                "name": "loc_failure"
            }
        )
        return locations

    def _buildEdges(self) -> list:
        """Build edges between locations."""
        edges = []

        for i in range(self.N):
            loc_name = f"loc_{i}"

            # From loc_i (i > 0), transitions to next state or back to loc_0
            edges.append(self._buildProgressEdge(loc_name, i))

        return edges

    def _buildFailureLoopEdge(self, loc_name: str) -> dict:
        """Build self-loop for failure location (loc_0)."""
        return {
            "location": loc_name,
            "guard": {
                "exp": {
                    "op": "∧",
                    "left": {
                        "op": "≥",
                        "left": "cx",
                        "right": "x",
                    },
                    "right": {"op": "¬", "exp": "failure"},
                }
            },
            "destinations": [
                {
                    "location": loc_name,
                    "probability": {"exp": 1},
                    "assignments": [
                        {"ref": "cx", "value": 0},
                        {
                            "ref": "x",
                            "value": {
                                "distribution": "Exponential",
                                "args": [1],
                            },
                        },
                    ],
                }
            ],
        }

    def _buildProgressEdge(self, loc_name: str, current_idx: int) -> dict:
        """Build edge from non-final location (probabilistic branching)."""
        next_loc = f"loc_{current_idx + 1}" if current_idx + 1 < self.N else "loc_0"

        # PASS branch: advance to next location
        pass_destination = {
            "location": 'loc_0',
            "probability": {
                "exp": {
                    "op": "/",
                    "left": self.PASS_W,
                    "right": {"op": "+", "left": self.PASS_W, "right": self.FAIL_W},
                }
            },
            "assignments": [
                {"ref": "cx", "value": 0},
                {
                    "ref": "x",
                    "value": {
                        "distribution": "Exponential",
                        "args": [1],
                    },
                },
            ],
        }

        # FAIL branch: jump to loc_failure (failure) or set failure flag
        if current_idx + 1 == self.N:
            # Last location before loop - trigger failure
            fail_destination = {
                "location": "loc_failure",
                "probability": {
                    "exp": {
                        "op": "/",
                        "left": self.FAIL_W,
                        "right": {
                            "op": "+",
                            "left": self.PASS_W,
                            "right": self.FAIL_W,
                        },
                    }
                },
                "assignments": [
                    {"ref": "failure", "value": True},
                    {"ref": "x", "value": 0},
                ],
            }
        else:
            # Intermediate location - reset progression
            fail_destination = {
                "location": next_loc,
                "probability": {
                    "exp": {
                        "op": "/",
                        "left": self.FAIL_W,
                        "right": {
                            "op": "+",
                            "left": self.PASS_W,
                            "right": self.FAIL_W,
                        },
                    }
                },
                "assignments": [
                    {"ref": "cx", "value": 0},
                    {
                        "ref": "x",
                        "value": {
                            "distribution": "Exponential",
                            "args": [1],
                        },
                    },
                ],
            }

        return {
            "location": loc_name,
            "guard": {
                "exp": {
                    "op": "∧",
                    "left": {
                        "op": "≥",
                        "left": "cx",
                        "right": "x",
                    },
                    "right": {"op": "¬", "exp": "failure"},
                }
            },
            "destinations": [pass_destination, fail_destination],
        }


