from __future__ import annotations
import math
from typing import List
from models.clock import Clock

INF = math.inf

class DBM:
    def __init__(self, clocks: List[str]):
        self.clocks = ["0"] + clocks
        self.n = len(self.clocks)

        self.M = [[INF] * self.n for _ in range(self.n)]

        for i in range(self.n):
            self.M[i][i] = 0

        for i in range(1, self.n):
            self.M[0][i] = 0

    def __eq__(self, other) -> bool:
        if not isinstance(other, DBM):
            raise ValueError("Cannot compare DBM with non-DBM object.")
        if self.clocks != other.clocks:
            return False
        return self.M == other.M

    def __hash__(self) -> int:
        return hash(tuple(tuple(row) for row in self.M))

    def __len__(self) -> int:
        return self.n

    def __repr__(self) -> str:
        return f"DBM(clocks={self.clocks}, {self.n}x{self.n} matrix)"

    def addConstraint(self, clock1: str, clock2: str, bound: float) -> None:
        """
        Adds a constraint of the form clock1 - clock2 <= bound.\n
        E.g. addConstraint("clk1", "clk2", 5) adds the constraint clk1 - clk2 <= 5.\n
        To add the constraint x <= 5, we can add the constraint x - 0 <= 5.
        i.e. addConstraint("x", "0", 5) adds the constraint x - 0 <= 5,
        which is equivalent to x <= 5.\n
        To add the constraint x >= 5, we can add the constraint 0 - x <= -5.
        i.e. addConstraint("0", "x", -5) adds the constraint 0 - x <= -5,
        which is equivalent to x >= 5.
        """
        i = self.clocks.index(clock1)
        j = self.clocks.index(clock2)

        self.M[i][j] = min(self.M[i][j], bound)

    def removeConstrains(self, clock: str) -> None:
        """
        Removes all constraints involving the specified clock.
        """
        idx = self.clocks.index(clock)
        for i in range(self.n):
            self.M[i][idx] = INF
            self.M[idx][i] = INF
        self.M[idx][idx] = 0

        # Enforce x >= 0 after freeing the clock
        self.M[0][idx] = 0

    def normalize(self):
        """
        Applies the Floyd-Warshall algorithm to compute the shortest paths between all pairs of clocks
        """
        for k in range(self.n): # Try using clock k as an intermediate point.
            for i in range(self.n): # Starting from clock i
                for j in range(self.n): # Ending at clock j
                    if self.M[i][j] > self.M[i][k] + self.M[k][j]:
                        self.M[i][j] = self.M[i][k] + self.M[k][j]

    def intersection(self, dmb: DBM) -> DBM:
        """Returns a new DMB that is the intersection of this DMB and the given DMB."""
        if (set(self.clocks) != set(dmb.clocks)):
            raise ValueError("DMBs must have the same clocks to compute intersection.")

        # Map each clock name to its index in the other DMB to align matrix indices.
        dmb_index = {clock: idx for idx, clock in enumerate(dmb.clocks)}
        result = DBM(self.clocks[1:]) # Exclude the "0" clock; preserves this DMB's order
        for i in range(result.n):
            clock_i = result.clocks[i]
            di = dmb_index[clock_i]
            for j in range(result.n):
                clock_j = result.clocks[j]
                dj = dmb_index[clock_j]
                result.M[i][j] = min(self.M[i][j], dmb.M[di][dj])

        result.normalize()
        return result

    def isSubset(self, dmb: DBM) -> bool:
        """Returns True if this DMB is a subset of the given DMB."""
        if (set(self.clocks) != set(dmb.clocks)):
            raise ValueError("DMBs must have the same clocks to compute subset.")
        # Align indices between the two DMBs based on clock names.
        dmb_index = {clock: idx for idx, clock in enumerate(dmb.clocks)}

        for i in range(self.n):
            clock_i = self.clocks[i]
            di = dmb_index[clock_i]
            for j in range(self.n):
                clock_j = self.clocks[j]
                dj = dmb_index[clock_j]
                if self.M[i][j] > dmb.M[di][dj]:
                    return False
        return True

    def isEmpty(self) -> bool:
        for i in range(self.n):
            if self.M[i][i] < 0:
                return True
        return False

    def isSatisfiedBy(self, clocks: List[Clock]) -> bool:
        """Checks if the given clock valuations satisfy the constraints in this DMB."""
        clockDict: dict[str, float] = {}
        for clock in clocks:
            if clock.name in clockDict:
                raise ValueError(f"Duplicate clock valuation provided for '{clock.name}'.")
            clockDict[clock.name] = clock.value

        requiredClocks = {clock for clock in self.clocks if clock != "0"}
        providedClocks = set(clockDict.keys())

        missingClocks = requiredClocks - providedClocks
        if missingClocks:
            missing = ", ".join(sorted(missingClocks))
            raise ValueError(f"Missing clock valuations for: {missing}")

        unknownClocks = providedClocks - requiredClocks
        if unknownClocks:
            unknown = ", ".join(sorted(unknownClocks))
            raise ValueError(f"Unknown clock valuations provided: {unknown}")

        for i in range(self.n):
            for j in range(self.n):
                if self.M[i][j] < INF:
                    clock1 = self.clocks[i]
                    clock2 = self.clocks[j]
                    val1 = 0 if clock1 == "0" else clockDict[clock1]
                    val2 = 0 if clock2 == "0" else clockDict[clock2]
                    if val1 - val2 > self.M[i][j]:
                        return False
        return True

    def removeLowerBounds(self) -> None:
        """Removes the lower bound constraints for all clocks specified."""
        for clock in self.clocks[1:]: # Exclude the "0" clock
            self.M[self.clocks.index("0")][self.clocks.index(clock)] = 0
