import sys
import numpy as np
import pandas as pd
import itertools as it
import statistics as st

def report_stats(mod_name: str, symbol: str, X, conf_name: str):
    print(f"# {mod_name} modularity for {conf_name}:")
    print(f"  min({symbol}) = {min(X):.4g}")
    print(f"  ave({symbol}) = {st.mean(X):.4g}")
    print(f"  med({symbol}) = {st.median(X):.4g}")
    print(f"  max({symbol}) = {max(X):.4g}")
    print()

def check_null_cases(A, d)->bool:
    """ Check for null contingency or community matrices."""
    if not isinstance(A, np.ndarray) or not isinstance(d, np.ndarray):
        return True
    if A.size < 2:
        return True
    if not A.any() or not d.any():
        return True

    # Default non-null case
    return False
    
def newman_girvan(A, d, verb=False)->float:
    # Zero modularity by default for all degenerate cases
    if check_null_cases(A, d):
        return 0.0

    m = np.count_nonzero(A)
    W = np.sum(A)
    if verb:
        print("\n# Adjacency matrix:")
        print(A)
        print("  Number of non-zero weights:", m)
        print("  Sum of weights:", W)

    # In weights
    w_i = A.sum(axis=0)
    if verb:
        print("  Total incoming weights:", np.sum(w_i))

    # Out weights
    w_o = A.sum(axis=1)
    if verb:
        print("  Total outgoing weights:", np.sum(w_o))

    # Compute expected adjacency matrix
    E = np.outer(w_o, w_i) / W
    if verb:
        print("  Expected adjacency matrix:")
        print(pd.DataFrame(E))

    # Compute modularity matrix
    M = A - E
    if verb:
        print("  Modularity matrix:")
        print(pd.DataFrame(M))

    # Modularity
    Q = np.sum(M * d) / W
    if verb:
        print(f"  Newman-Girvan modularity Q={Q:.4g}")
    return Q

def constant_potts_model(A, d, gamma: float, verb=False)->float:
    # Zero CPM by default for all degenerate cases
    if check_null_cases(A, d):
        return 0.0

    # CPM
    H = np.sum((A - gamma) * d)
    if verb:
        print(f"  Constant Potts model modularity H={H:.4g}")
    return H

def rank_cluster(n: int):
    """ Create community sharing matrix without self-loops."""
    d = np.ones((n, n))
    for i in range(n):
       d[i, i] = 0.0
    return d

def rank_modularities(l: list, config_name: str, verb=False):
    """ Compute and report on per-rank modularities."""

    modularity = [newman_girvan(A, d, verb) for (A, d) in l]
    report_stats("Newman-Girvan", 'Q', modularity, config_name)

    gamma = 0.1
    modularity = [constant_potts_model(A, d, gamma, verb) for (A, d) in l]
    report_stats(f"CPM (g={gamma:.4g})", 'H', modularity, config_name)


# Initial partition
n_0 = 4
A_0 = np.zeros((n_0, n_0))
A_0[3, 2] = 1.0
n_1 = 4
A_1 = np.zeros((n_1, n_1))
A_1[3, 2] = 1.0
n_2 = 1
A_2 = np.zeros((n_2, n_2))
print("## Initial partition")

# Whole-rank clusters
rank_modularities(
    [(A_0, rank_cluster(n_0)), (A_1, rank_cluster(n_1)), (A_2, None), (None, None)],
    "initial configuration with whole-rank clusters")

# Clusters of locally-connected objects
d_0 = np.zeros((n_0, n_0))
d_0[2, 3] = d_0[3, 2] = 1.0
d_1 = np.zeros((n_1, n_1))
d_1[2, 3] = d_1[3, 2] = 1.0
rank_modularities(
    [(A_0, d_0), (A_1, d_1), (A_2, None), (None, None)],
    "initial configuration with on-rank communication clusters")

# All objects on same rank
n = 9
A = np.zeros((n, n))
A[0, 5] = 2.0 
A[1, 4] = 1.0
A[3, 2] = 1.0
A[3, 8] = 0.5 
A[4, 1] = 2.0
A[5, 8] = 2.0 
A[7, 6] = 1.0
A[8, 6] = 1.5

# Whole-rank clusters
rank_modularities(
    [(A, rank_cluster(n)), (None, None), (None, None), (None, None)],
    "all objects on same rank with whole-rank clusters")

# Clusters of locally-connected objects
d = np.zeros((n, n))
for (i, j) in it.combinations((0, 2, 3, 5, 6, 7 ,8), 2):
    d[i, j] = d[j, i] = 1.0
for (i, j) in it.combinations((1, 4), 2):
    d[i, j] = d[j, i] = 1.0
rank_modularities(
    [(A, d),
     (None, None),
     (None, None),
     (None, None)],
    "all objects on same rank with on-rank communication clusters")

# Partition in two disjoint connected components
n_0 = 7
A_0 = np.zeros((n_0, n_0))
A_0[3, 2] = 1.0
A_0[0, 3] = 2.0 
A_0[2, 1] = 1.0
A_0[2, 6] = 0.5 
A_0[3, 6] = 2.0 
A_0[5, 4] = 1.0
A_0[6, 4] = 1.5
n_1 = 2
A_1 = np.zeros((n_1, n_1))
A_1[0, 1] = 1.0
A_1[1, 0] = 2.0

# Whole-rank clusters
rank_modularities(
    [(A_0, rank_cluster(n_0)),
     (A_1, rank_cluster(n_1)),
     (None, None),
     (None, None)],
    "2 connected components with whole-rank clusters")

# No clusters
d_0 = np.zeros((n_0, n_0))
d_1 = np.zeros((n_1, n_1))
rank_modularities(
    [(A_0, d_0),
     (A_1, d_1),
     (None, None),
     (None, None)],
    "2 connected components without clusters")

# Clusters of locally-connected objects
for (i, j) in it.combinations(range(n_0), 2):
    d_0[i, j] = d_0[j, i] = 1.0
for (i, j) in it.combinations(range(n_1), 2):
    d_1[i, j] = d_1[j, i] = 1.0
rank_modularities(
    [(A_0, d_0),
     (A_1, d_1),
     (None, None),
     (None, None)],
    "2 connected components with on-rank communication clusters")

# Ad hoc partition
n_0 = 2 # 0, 5
A_0 = np.zeros((n_0, n_0))
A_0[0, 1] = 2.0
n_1 = 2 # 1, 4
A_1 = np.zeros((n_1, n_1))
A_1[0, 1] = 1.0
A_1[1, 0] = 2.0
n_2 = 2 # 2, 3
A_2 = np.zeros((n_2, n_2))
A_2[1, 0] = 1.0
n_3 = 3 # 6, 7, 8
A_3 = np.zeros((n_3, n_3))
A_3[1, 0] = 1.0
A_3[2, 0] = 1.5

# Whole-rank clusters
rank_modularities(
    [(A_0, rank_cluster(n_0)),
     (A_1, rank_cluster(n_1)),
     (A_2, rank_cluster(n_2)),
     (A_3, rank_cluster(n_3))],
    "ad hoc partition with whole-rank clusters")

# Clusters of locally-connected objects
d_0 = np.zeros((n_0, n_0))
d_0[0, 1] = d_0[1, 0] = 1.0
d_1 = np.zeros((n_1, n_1))
d_1[0, 1] = d_1[1, 0] = 1.0
d_2 = np.zeros((n_2, n_2))
d_2[0, 1] = d_2[1, 0] = 1.0
d_3 = np.zeros((n_3, n_3))
d_3[0, 1] = d_3[1, 0] = 1.0
d_3[0, 2] = d_3[2, 0] = 1.0
d_3[1, 2] = d_3[2, 1] = 1.0
rank_modularities(
    [(A_0, d_0),
     (A_1, d_1),
     (A_2, d_2),
     (A_3, d_3)],
    "ad hoc partition with on-rank communication clusters")
