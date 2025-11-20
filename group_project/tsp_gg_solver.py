"""
Gavish-Graves (GG) Formulation for TSP
Single-commodity flow formulation to prevent subtours
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import sys
import time

def load_distance_matrix(filepath):
    """Load distance matrix from CSV file"""
    df = pd.read_csv(filepath, header=None)
    return df.values


def build_gg_model(dist_matrix, relaxation=False):
    """
    Build Gavish-Graves TSP model
    Args:
        dist_matrix: n×n numpy array with distances
        relaxation: if True, solve LP relaxation; if False, solve IP
    Returns:
        model: Gurobi model
        x: edge decision variables
        f: flow variables
    """
    n = len(dist_matrix)
    model = gp.Model("TSP_GG")
    
    # Silent the solver output since it is noisy
    model.Params.OutputFlag = 0

    # Decision variables
    # x[i,j] = 1 if edge (i,j) is in tour
    if relaxation:
        x = model.addVars(n, n, vtype=GRB.CONTINUOUS, lb=0, ub=1, name="x")
    else:
        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # f[i,j] = flow on edge (i,j)
    f = model.addVars(n, n, vtype=GRB.CONTINUOUS, lb=0, name="f")

    # Objective: minimize total distance
    obj = gp.quicksum(dist_matrix[i, j] * x[i, j]
                     for i in range(n) for j in range(n) if i != j)
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraint (1): Each node has exactly one outgoing edge
    for i in range(n):
        model.addConstr( gp.quicksum(x[i, j] for j in range(n) if j != i) == 1, name=f"out_{i}")

    # Constraint (2): Each node has exactly one incoming edge
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1, name=f"in_{j}")

    # Flow constraints (using node 0 as source)
    source = 0

    # Constraint (3): Source sends n-1 units of flow
    model.addConstr(gp.quicksum(f[source, j] for j in range(n) if j != source) == n - 1, name="flow_out_source")

    # Constraint (4): Source receives no flow
    model.addConstr(gp.quicksum(f[i, source] for i in range(n) if i != source) == 0, name="flow_in_source")

    # Constraint (5): Flow conservation for non-source nodes
    # Each non-source node consumes exactly 1 unit of flow
    for i in range(n):
        if i != source:
            model.addConstr( gp.quicksum(f[j, i] for j in range(n) if j != i) - gp.quicksum(f[i, j] for j in range(n) if j != i) == 1, name=f"flow_balance_{i}")

    # Constraint (6): Flow only on selected edges
    for i in range(n):
        for j in range(n):
            if i != j:
                model.addConstr(f[i, j] <= (n - 1) * x[i, j], name=f"flow_capacity_{i}_{j}")
    model.update()
    return model, x, f


def solve_model(model):
    model.optimize()
    if model.status == GRB.OPTIMAL:
        return model.objVal
    else:
        return None

def compute_integrality_gap(ip_obj, lp_obj):
    if ip_obj == 0: return 0
    return ((ip_obj - lp_obj) / ip_obj) * 100


def solve_tsp_gg(dist_matrix, relaxation=False):
    model, x, f = build_gg_model(dist_matrix, relaxation=relaxation)
    obj = solve_model(model)
    return {'objective': obj}

def compute_cv(dist_matrix):
    """Compute coefficient of variation of distance matrix"""
    # Extract non-diagonal elements (actual distances)
    distances = dist_matrix[np.triu_indices_from(dist_matrix, k=1)]
    if len(distances) == 0 or np.mean(distances) == 0:
        return 0
    cv = np.std(distances) / np.mean(distances)
    return cv


def solve_instance(dist_matrix_path):
    # Load distance matrix
    dist_matrix = load_distance_matrix(dist_matrix_path)
    n = len(dist_matrix)

    results = {
        'instance': dist_matrix_path.split('/')[-1],
        'n': n
    }

    # Compute coefficient of variation
    results['cv'] = compute_cv(dist_matrix)

    ip_result = solve_tsp_gg(dist_matrix, relaxation=False)
    results['IP_obj'] = ip_result['objective']

    # Time only the LP relaxation
    lp_start = time.time()
    lp_result = solve_tsp_gg(dist_matrix, relaxation=True)
    results['lp_solve_time'] = time.time() - lp_start

    results['LP_obj'] = lp_result['objective']

    if results['IP_obj'] is not None and results['LP_obj'] is not None:
        results['gap_percent'] = compute_integrality_gap(results['IP_obj'], results['LP_obj'])
        results['gap_absolute'] = results['IP_obj'] - results['LP_obj']
    return results


if __name__ == "__main__":
    filepath = sys.argv[1]
    results = solve_instance(filepath)
