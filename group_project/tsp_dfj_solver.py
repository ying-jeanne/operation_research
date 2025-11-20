"""
Dantzig-Fulkerson-Johnson (DFJ) Formulation for TSP
Uses subtour elimination constraints with lazy callback

References:
- Held-Karp relaxation (Subtour Elimination Problem - SEP)
- arXiv:2507.07003 - The Integrality Gap of the TSP
- Standard formulation for studying DFJ integrality gap
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


def find_subtours(n, x_vals):
    """
    Find all subtours in current solution using DFS
    Args:
        n: number of nodes
        x_vals: dictionary of edge variables and their values {(i,j): value}
    Returns:
        List of subtours, where each subtour is a list of nodes
    """
    # Build adjacency list from edges with value close to 1, this is the graph algorithm in order to know the entire network is connected or not
    edges = [(i, j) for (i, j), val in x_vals.items() if val > 0.5]
    adj = {i: [] for i in range(n)}
    for i, j in edges:
        adj[i].append(j)

    visited = [False] * n
    subtours = []

    for start in range(n):
        if visited[start]:
            continue
        # Follow the tour from this node
        tour = []
        curr = start
        while not visited[curr]:
            visited[curr] = True
            tour.append(curr)
            # Find next node
            if adj[curr]:
                curr = adj[curr][0]
            else:
                break
        if len(tour) > 0:
            subtours.append(tour)

    return subtours


def build_dfj_model(dist_matrix, relaxation=False, subtour_constraints=None):
    """
    Build Dantzig-Fulkerson-Johnson TSP model

    Args:
        dist_matrix: n×n numpy array with distances
        relaxation: if True, solve LP relaxation; if False, solve IP
        subtour_constraints: List of subtour constraint sets to add (for LP)
    Returns:
        model: Gurobi model
        x: edge decision variables
        subtour_list: list to store subtour constraints (for IP only)
    """
    n = len(dist_matrix)
    model = gp.Model("TSP_DFJ")

    # Silent the solver output
    model.Params.OutputFlag = 0

    # Disable presolve reductions for lazy constraints
    if not relaxation:
        model.Params.LazyConstraints = 1

    # Decision variables: x[i,j] = 1 if edge (i,j) is in tour
    if relaxation:
        x = model.addVars(n, n, vtype=GRB.CONTINUOUS, lb=0, ub=1, name="x")
    else:
        x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # Objective: minimize total distance
    obj = gp.quicksum(dist_matrix[i, j] * x[i, j]
                     for i in range(n) for j in range(n) if i != j)
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraint (1): Each node has exactly one outgoing edge
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if j != i) == 1,
            name=f"out_{i}"
        )

    # Constraint (2): Each node has exactly one incoming edge
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[j, i] for j in range(n) if j != i) == 1,
            name=f"in_{i}"
        )

    # For LP: Add subtour elimination constraints from IP solve
    if relaxation and subtour_constraints:
        for idx, subtour in enumerate(subtour_constraints):
            model.addConstr(
                gp.quicksum(x[i, j] for i in subtour for j in subtour if i != j) <= len(subtour) - 1,
                name=f"subtour_lp_{idx}"
            )

    # For IP: Will use lazy callback (constraints added during solve)
    subtour_list = [] if not relaxation else None

    model.update()
    return model, x, subtour_list


def subtour_callback(model, where, x, n, subtour_list):
    """
    Gurobi callback function to add lazy subtour elimination constraints
    Args:
        model: Gurobi model
        where: callback location
        x: decision variables
        n: number of nodes
        subtour_list: list to store added subtour constraints
    """
    if where == GRB.Callback.MIPSOL:
        # Get current solution
        x_vals = model.cbGetSolution(x)

        # Find subtours in current solution
        subtours = find_subtours(n, x_vals)

        # If more than one subtour, add lazy constraints
        if len(subtours) > 1:
            for subtour in subtours:
                if len(subtour) < n:  # Don't add constraint for full tour
                    # Add lazy constraint: sum of edges in subtour <= |subtour| - 1
                    model.cbLazy(
                        gp.quicksum(x[i, j] for i in subtour for j in subtour if i != j)
                        <= len(subtour) - 1
                    )
                    # Store the subtour for LP reuse
                    subtour_list.append(subtour)

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

    # ========== Step 1: Solve IP with lazy constraints ==========
    # Time the IP solve (constraint generation phase)
    ip_start = time.time()
    model_ip, x_ip, subtour_list = build_dfj_model(dist_matrix, relaxation=False)

    # Set callback for lazy constraint generation
    model_ip.optimize(
        lambda model, where: subtour_callback(model, where, x_ip, n, subtour_list)
    )
    results['ip_solve_time'] = time.time() - ip_start

    if model_ip.status == GRB.OPTIMAL:
        results['IP_obj'] = model_ip.objVal
    else:
        results['IP_obj'] = None

    # ========== Step 2: Solve LP with same subtour constraints ==========
    # Time the LP relaxation (Held-Karp bound)
    lp_start = time.time()
    model_lp, x_lp, _ = build_dfj_model(dist_matrix, relaxation=True, subtour_constraints=subtour_list)
    model_lp.optimize()
    results['lp_solve_time'] = time.time() - lp_start

    if model_lp.status == GRB.OPTIMAL:
        results['LP_obj'] = model_lp.objVal
    else:
        results['LP_obj'] = None

    # Total time = constraint generation (IP) + LP solve
    results['total_solve_time'] = results['ip_solve_time'] + results['lp_solve_time']

    # ========== Step 3: Compute integrality gap ==========
    if results['IP_obj'] is not None and results['LP_obj'] is not None:
        results['gap_percent'] = ((results['IP_obj'] - results['LP_obj']) / results['IP_obj']) * 100
        results['gap_absolute'] = results['IP_obj'] - results['LP_obj']

    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        results = solve_instance(filepath)
