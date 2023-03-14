'''
Utlity to generate a random ProblemInstance

Dawson Ren
2/6/23
'''
import numpy as np

from ProblemInstance.ProblemInstance import ProblemInstance

def generate_random_pi(m: int, n: int, ones=False, cython=True) -> ProblemInstance:
    # generates a random ProblemInstance.
    P = np.random.rand(m, n).round(1)
    Q = np.random.rand(m, n).round(1)
    R = np.random.rand(m, n).round(1) * 10
    N = np.ones(n, dtype=np.int64) if ones else np.random.randint(1, m, size=(n, ), dtype=np.int64)
    return ProblemInstance(P, Q, R, N, cython)