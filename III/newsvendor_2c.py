import numpy as np
import gurobipy as gp
from gurobipy import GRB
from newsvendor_2a import generate_demands, compute_profit_no_transshipment

def solve_transshipment(demand, inventory, transship_cost):
    n_locations = len(demand)
    shortage = np.maximum(demand - inventory, 0)
    excess = np.maximum(inventory - demand, 0)

    if np.sum(shortage) == 0 or np.sum(excess) == 0:
        sales = np.minimum(demand, inventory)
        return np.sum(sales), 0

    try:
        m = gp.Model("transshipment")
        m.setParam('OutputFlag', 0)
        m.setParam('LogToConsole', 0)

        x = m.addVars(n_locations, n_locations, lb=0, name="x")

        # Maximize net benefit: revenue (100 per unit) - transshipment cost
        m.setObjective(
            gp.quicksum((100 - transship_cost[i, j]) * x[i, j]
                       for i in range(n_locations)
                       for j in range(n_locations)),
            GRB.MAXIMIZE
        )

        for i in range(n_locations):
            m.addConstr(
                gp.quicksum(x[i, j] for j in range(n_locations)) <= excess[i],
                f"supply_{i}"
            )

        for j in range(n_locations):
            m.addConstr(
                gp.quicksum(x[i, j] for i in range(n_locations)) <= shortage[j],
                f"demand_{j}"
            )

        m.optimize()

        if m.status == GRB.OPTIMAL:
            transship_amount = sum(x[i, j].X for i in range(n_locations)
                                  for j in range(n_locations))
            # Calculate actual transshipment cost from the solution
            variable_cost = sum(transship_cost[i, j] * x[i, j].X
                               for i in range(n_locations)
                               for j in range(n_locations))
            sales_base = np.minimum(demand, inventory)
            total_sales = np.sum(sales_base) + transship_amount
            return total_sales, variable_cost
        else:
            sales = np.minimum(demand, inventory)
            return np.sum(sales), 0
    except:
        sales = np.minimum(demand, inventory)
        return np.sum(sales), 0

def compute_profit_with_transshipment(demands, inventory, transship_cost, price=100, cost=50, fixed_cost=200):
    n_simulations = demands.shape[0]
    total_sales = 0
    total_variable_cost = 0
    transship_count = 0

    for k in range(n_simulations):
        sales, variable_cost = solve_transshipment(demands[k, :], inventory, transship_cost)
        total_sales += sales
        if variable_cost > 0:
            total_variable_cost += variable_cost
            transship_count += 1

    expected_revenue = price * (total_sales / n_simulations)
    expected_variable_cost = total_variable_cost / n_simulations
    procurement_cost = cost * np.sum(inventory)
    expected_profit = expected_revenue - procurement_cost - fixed_cost - expected_variable_cost

    return expected_profit, transship_count, expected_variable_cost

def main():
    locations = ['Jurong West', 'Orchard', 'Harbour Front']
    mean_demands = np.array([300, 500, 500])
    std_demands = np.array([20, 20, 40])
    inventory = np.array([300, 500, 500])
    price, cost, n_simulations = 100, 50, 100000

    transship_cost = np.array([
        [0, 22, 19],
        [22, 0, 7],
        [19, 7, 0]
    ])

    demands = generate_demands(mean_demands, std_demands, n_simulations, seed=42)

    expected_profit_no_trans, expected_sales_no_trans, _ = compute_profit_no_transshipment(
        demands, inventory, price, cost
    )

    expected_profit_with_trans, transship_count, expected_variable_cost = compute_profit_with_transshipment(
        demands, inventory, transship_cost, price, cost, fixed_cost=200
    )

    benefit = expected_profit_with_trans - expected_profit_no_trans
    transship_freq = transship_count / n_simulations * 100

    print(f"\n{'Scenario':<35} {'Expected Profit':>20}")
    print("-" * 60)
    print(f"{'(a) No Transshipment':<35} ${expected_profit_no_trans:>18,.2f}")
    print(f"{'(c) With Transshipment Service':<35} ${expected_profit_with_trans:>18,.2f}")
    print("=" * 60)
    print(f"{'Expected Benefit':<35} ${benefit:>18,.2f}")
    print(f"{'Transshipment Frequency':<35} {transship_freq:>18.2f}%")
    print(f"{'Expected Variable Transship Cost':<35} ${expected_variable_cost:>18,.2f}")
    print(f"{'Fixed Service Cost (one-time)':<35} ${200.0:>18,.2f}")

if __name__ == "__main__":
    main()
