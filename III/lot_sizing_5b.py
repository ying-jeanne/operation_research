import numpy as np
import gurobipy as gp
from gurobipy import GRB

def solve_economic_lot_sizing():
    """Economic Lot-Sizing Problem for airplane production"""
    
    # Data
    T = 4
    d = np.array([3, 2, 3, 2])
    K = 2.0  # Setup cost (million $)
    h = 0.2  # Holding cost per airplane per season (million $)

    m = gp.Model("economic_lot_sizing")

    # Decision variables
    x = m.addVars(T, lb=0, vtype=GRB.INTEGER, name="x")  # End inventory
    y = m.addVars(T, lb=0, vtype=GRB.INTEGER, name="y")  # Production
    z = m.addVars(T, vtype=GRB.BINARY, name="z")        # Setup indicator

    # Objective: Minimize setup + holding costs
    m.setObjective(
        gp.quicksum(K * z[t] + h * x[t] for t in range(T)),
        GRB.MINIMIZE
    )

    # Constraints
    x_prev = 0  # Initial inventory
    M = sum(d)  # Big-M for linking constraint

    for t in range(T):
        # Inventory balance: x_{t-1} + y_t = d_t + x_t
        if t == 0:
            m.addConstr(x_prev + y[t] == d[t] + x[t], f"balance_{t}")
        else:
            m.addConstr(x[t-1] + y[t] == d[t] + x[t], f"balance_{t}")
        
        # Setup linking: y_t <= M * z_t
        m.addConstr(y[t] <= M * z[t], f"setup_{t}")

    m.optimize()

    if m.status == GRB.OPTIMAL:
        print("\n" + "="*70)
        print("OPTIMAL SOLUTION FOUND")
        print("="*70)
        print(f"\nMinimum Total Cost: ${m.objVal:.2f} million")
        print("\nProduction Schedule:")
        print(f"{'Season':<10} {'Demand':<10} {'Production':<12} {'Setup?':<10} {'End Inventory':<15}")
        print("-"*70)

        total_setup_cost = 0
        total_holding_cost = 0

        for t in range(T):
            setup = "Yes" if z[t].X > 0.5 else "No"
            total_setup_cost += K * z[t].X
            total_holding_cost += h * x[t].X
            print(f"{t+1:<10} {d[t]:<10} {int(y[t].X):<12} {setup:<10} {int(x[t].X):<15}")

        print("-"*70)
        print(f"\nCost Breakdown:")
        print(f"  Total Setup Cost:   ${total_setup_cost:.2f} million")
        print(f"  Total Holding Cost: ${total_holding_cost:.2f} million")
        print(f"  Total Cost:         ${total_setup_cost + total_holding_cost:.2f} million")
        print("="*70)

        return m.objVal, [(int(y[t].X), int(x[t].X), int(z[t].X)) for t in range(T)]
    else:
        print("No optimal solution found!")
        return None, None

if __name__ == "__main__":
    solve_economic_lot_sizing()
