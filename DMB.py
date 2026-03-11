import math
from typing import List

INF = math.inf

class DMB:
    def __init__(self, clocks: List[str]):
        self.clocks = ["0"] + clocks
        self.n = len(self.clocks)

        self.M = [[INF] * self.n for _ in range(self.n)]

        for i in range(self.n):
            self.M[i][i] = 0

    def addConstraint(self, clock1: str, clock2: str, bound: int):
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

    def removeConstrains(self, clock: str):
        """
        Removes all constraints involving the specified clock.
        """
        idx = self.clocks.index(clock)
        for i in range(self.n):
            self.M[i][idx] = INF
            self.M[idx][i] = INF
        self.M[idx][idx] = 0

    def normalize(self):
        """
        Applies the Floyd-Warshall algorithm to compute the shortest paths between all pairs of clocks
        """
        for k in range(self.n): # Try using clock k as an intermediate point.
            for i in range(self.n): # Starting from clock i
                for j in range(self.n): # Ending at clock j
                    if self.M[i][j] > self.M[i][k] + self.M[k][j]:
                        self.M[i][j] = self.M[i][k] + self.M[k][j]
