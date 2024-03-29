'''
Provides the ProblemSolver class, finding the optimal policy for a given ProblemInstance.
'''
import numpy as np
from typing import Generator, List, Union

from ProblemInstance.ProblemInstance import ProblemInstance
from utils.col_aggregator import col_aggregator

class ProblemSolver:
    def __init__(self, prob: ProblemInstance) -> None:
        self.prob = prob

    def _getAllPolicies(self, m, n) -> Generator[np.ndarray, None, None]:
        # exponentially large number of policies...
        for i in range(2 ** (m * n)):
            yield np.array([int(k) for k in '{0:b}'.format(i).zfill(m * n)]).reshape(m, n)

    def _getFeasiblePolicies(self, m, n) -> Generator[np.ndarray, None, None]:
        # turn into a col, make sure sum is >= N

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
        best_rev = -1
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
        m = self.prob.m

        # PROVED: the nurses scheduled in DP1 must be scheduled in optimal
        dyn = self.dynamicColumn(shift).reshape(m)

        # number of nurses we are free to change
        free_nurses = m - dyn.sum()
        if free_nurses == 0: return dyn.reshape((m, 1))

        # setup search
        best_rev = -1
        best_col = dyn
        
        for i in range(2 ** free_nurses):
            # convert i from decimal to numpy array of 0/1s
            y_partial = np.array([[int(k) for k in '{0:b}'.format(i).zfill(free_nurses)]]).reshape(free_nurses)
            y = dyn.copy()
            y[dyn == 0] = y_partial

            if (new_rev := self.prob.expectedRevenueCol(shift, y)) > best_rev:
                best_rev = new_rev
                best_col = y

        if best_col is None:
            raise Exception('ProblemSolver: No feasible policies')

        return best_col.reshape((m, 1))

    def optimalPolicy(self) -> np.ndarray:
        return np.hstack([self.optimalColumn(i) for i in range(self.prob.n)])
    
    def dynamicColumn(self, shift: int, include: Union[List[int], None]=None) -> np.ndarray:
        # include - the nurses we schedule
        m = self.prob.m if include is None else len(include)
        V = self.prob.V if include is None else self.prob.V[include, :]
        P = self.prob.P if include is None else self.prob.P[include, :]
        best = np.zeros((m, 1)) # maps nurse index to the best we can do while scheduling backwards
        best[m - 1] = V[m - 1, shift] # always schedule the last nurse

        policy = np.zeros((m, 1), dtype=np.int64)
        policy[m - 1] = 1 # always schedule the last nurse

        # go backwards from second-to-last nurse
        for i in range(m - 2, -1, -1):
            # we can either skip (put down 0) or schedule (1)
            skip = best[i + 1]
            schedule = V[i, shift] + (1 - P[i, shift]) * best[i + 1]
            if skip >= schedule:
                policy[i] = 0
                best[i] = skip
            else:
                policy[i] = 1
                best[i] = schedule
        return policy
    
    def dynamicColumn2(self, shift: int) -> np.ndarray:
        N_j, m = self.prob.N[shift], self.prob.m
        # memoization table, N_j x m
        memo = np.zeros((N_j, m))
        # policy, only enter for highest N_j
        policy = np.zeros((m, 1), dtype=np.int64)

        # iterate over N_j, increasing from 0 to N_j - 1 inclusive
        for n_j in range(N_j):
            # iterate from last to first
            for i in range(m - 1, -1, -1):
                # f_{i + 1}(n_j - 1)
                rev_if_scheduled = memo[n_j - 1, i + 1] if n_j > 0 and i < m - 1 else 0
                # f_{i + 1}(n_j)
                rev_if_not_scheduled = memo[n_j, i + 1] if n_j >= 0 and i < m - 1 else 0
                # p_{i, j}
                prob_schedule = self.prob.P[i, shift]
                show = self.prob.V[i, shift] + prob_schedule * rev_if_scheduled + (1 - prob_schedule) * rev_if_not_scheduled
                do_not_show = rev_if_not_scheduled
                if show >= do_not_show:
                    memo[n_j, i] = show
                    if n_j == N_j - 1:
                        policy[i] = 1
                else:
                    memo[n_j, i] = do_not_show
                    if n_j == N_j - 1:
                        policy[i] = 0

        return policy
    
    def dynamicPolicy(self) -> np.ndarray:
        # this only works for problem instances with N = 1s
        if np.any(self.prob.N != 1):
            raise Exception('ProblemSolver: can only use dynamic policy on N = 1 for all')

        # use a dynamic programming (DP) approach to solve for the best policy, ONLY for N_j = 1
        return np.hstack([self.dynamicColumn(i) for i in range(self.prob.n)])
    
    def dynamicPolicy2(self) -> np.ndarray:
        # use a trial dynamic programming (DP) approach to solve for the best policy
        return np.hstack([self.dynamicColumn2(i) for i in range(self.prob.n)])
