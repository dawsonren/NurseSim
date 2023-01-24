'''
Provides the ProblemSolver class, finding the optimal policy for a given ProblemInstance.
'''
import numpy as np
from typing import Generator

from ProblemInstance.ProblemInstance import ProblemInstance

class ProblemSolver:
    def __init__(self, prob: ProblemInstance) -> None:
        self.prob = prob

    def _getAllPolicies(self, m, n) -> Generator[np.ndarray, None, None]:
        # exponentially large number of policies...
        for i in range(2 ** (m * n)):
            yield np.array([int(k) for k in '{0:b}'.format(i).zfill(m * n)]).reshape(m, n)

    def _getFeasiblePolicies(self, m, n) -> Generator[np.ndarray, None, None]:
        for i in range(2 ** (m * n)):
            Y = np.array([int(k) for k in '{0:b}'.format(i).zfill(m * n)]).reshape(m, n)

            if m >= n:
                # Y should have at least a 1 in every column
                if (Y.sum(axis=0) >= 0).sum() >= n:
                    yield Y
            else:
                # Y should be scheduling every nurse
                if (Y.sum(axis=1) >= 0).sum() >= m:
                    yield Y

    def bruteForceOptimalPolicy(self, optimize=False) -> np.ndarray:
        best_rev = 0
        best_pol = None
        gen = self._getFeasiblePolicies(self.prob.m, self.prob.n) if optimize else self._getAllPolicies(self.prob.m, self.prob.n)

        for pol in gen:
            if (new_rev := self.prob.expectedRevenue(pol)) > best_rev:
                best_rev = new_rev
                best_pol = pol

        if best_pol is None:
            raise Exception('ProblemSolver: No feasible policies')

        return best_pol

    def optimalColumn(self, shift: int) -> np.ndarray:
        best_rev = 0
        best_col = None
        m, n = self.prob.m, self.prob.n

        # speedup: it's always advantageous to schedule the last nurse, assuming all revenue is non-negative
        # use bitshifting to accomplish this
        for i in range(2 ** (m - 1)):
            # convert i from decimal to numpy array of 0/1s
            y = np.array([[int(k) for k in '{0:b}'.format((i << 1) + 1).zfill(m)]]).reshape((m, ))

            if (new_rev := self.prob.expectedRevenueCol(shift, y)) > best_rev:
                best_rev = new_rev
                best_col = y

        if best_col is None:
            raise Exception('ProblemSolver: No feasible policies')

        return best_col.reshape((m, 1))

    def optimalPolicy(self) -> np.ndarray:
        return np.hstack([self.optimalColumn(i) for i in range(self.prob.n)])
    
    def dynamicColumn(self, shift: int) -> np.ndarray:
        m = self.prob.m
        best = np.zeros((m, 1)) # maps nurse index to the best we can do while scheduling backwards
        best[m - 1] = self.prob.V[m - 1, shift] # always schedule the last nurse

        policy = np.zeros((m, 1), dtype=np.int64)
        policy[m - 1] = 1 # always schedule the last nurse

        # go backwards from second-to-last nurse
        for i in range(m - 2, -1, -1):
            # we can either skip (put down 0) or schedule (1)
            skip = best[i + 1]
            schedule = self.prob.V[i, shift] + (1 - self.prob.P[i, shift]) * best[i + 1]
            if skip >= schedule:
                policy[i] = 0
                best[i] = skip
            else:
                policy[i] = 1
                best[i] = schedule
        return policy
    
    def dynamicPolicy(self) -> np.ndarray:
        # this only works for problem instances with N = 1s
        if np.any(self.prob.N != 1):
            raise Exception('ProblemSolver: can only use dynamic policy on N = 1 for all')

        # use a dynamic programming (DP) approach to solve for the best policy
        return np.hstack([self.dynamicColumn(i) for i in range(self.prob.n)])
