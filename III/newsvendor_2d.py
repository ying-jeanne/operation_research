import numpy as np
import gurobipy as gp
from gurobipy import GRB
from newsvendor_2a import generate_demands

def solve_two_stage_saa(demands, transship_cost, price=100, cost=50, fixed_cost=200):
    """
    Solve the two-stage stochastic optimization problem for optimal inventory placement

    Decision variables:
    - First stage: s_i = inventory to place at location i
    - Second stage: x_ij^k = transshipment from location i to j under scenario k

    Args:
        demands: K x 3 array of demand samples
        transship_cost: 3 x 3 matrix of unit transshipment costs
        price: selling price per unit
        cost: procurement cost per unit
        fixed_cost: one-time fixed cost for transshipment service (sunk cost in this problem)

    Returns:
        optimal inventory positions (s1, s2, s3) and expected profit
    """
    K, n_locations = demands.shape  # K scenarios, n locations

    try:
        m = gp.Model("two_stage_inventory")
        m.setParam('OutputFlag', 1)
        m.setParam('TimeLimit', 300)  # 5 minute time limit

        # First-stage decision variables: inventory positions
        s = m.addVars(n_locations, lb=0, vtype=GRB.CONTINUOUS, name="s")

        # Second-stage decision variables: transshipment for each scenario
        x = m.addVars(n_locations, n_locations, K, lb=0, vtype=GRB.CONTINUOUS, name="x")

        # Auxiliary variables for sales calculation
        # sales_direct[i, k] = min(D_i^k, s_i) - direct sales at location i in scenario k
        sales_direct = m.addVars(n_locations, K, lb=0, vtype=GRB.CONTINUOUS, name="sales_direct")

        # Auxiliary variables to handle min operation
        for k in range(K):
            for i in range(n_locations):
                # sales_direct[i,k] = min(demands[k,i], s[i])
                m.addConstr(sales_direct[i, k] <= demands[k, i], f"sales_ub_demand_{i}_{k}")
                m.addConstr(sales_direct[i, k] <= s[i], f"sales_ub_inventory_{i}_{k}")

        # Objective: maximize expected profit
        # Profit = (Second stage: Revenue - Transship cost) - (First stage: Procurement + Fixed cost)
        # Note: Fixed cost is constant, so excluded from optimization but added back when computing profit

        # First stage costs (procurement)
        procurement_cost = gp.quicksum(cost * s[i] for i in range(n_locations))

        # Second stage revenue (expected sales revenue)
        # sales_k = sum_i sales_direct[i,k] + sum_i sum_j x[i,j,k]
        expected_revenue = (1.0 / K) * gp.quicksum(
            price * (gp.quicksum(sales_direct[i, k] for i in range(n_locations)) +
                    gp.quicksum(x[i, j, k] for i in range(n_locations) for j in range(n_locations)))
            for k in range(K)
        )

        # Second stage costs (expected transshipment cost)
        expected_transship_cost = (1.0 / K) * gp.quicksum(
            transship_cost[i, j] * x[i, j, k]
            for k in range(K)
            for i in range(n_locations)
            for j in range(n_locations)
        )

        # Maximize: (Revenue - Transship cost) - Procurement
        # Equivalently minimize: Procurement - Revenue + Transship cost
        m.setObjective(
            procurement_cost - expected_revenue + expected_transship_cost,
            GRB.MINIMIZE
        )

        # Constraints for each scenario
        for k in range(K):
            D_k = demands[k, :]

            for i in range(n_locations):
                # Supply constraint: transshipment out <= excess inventory
                excess_i = s[i] - sales_direct[i, k]
                m.addConstr(
                    gp.quicksum(x[i, j, k] for j in range(n_locations)) <= excess_i,
                    f"supply_{i}_{k}"
                )

            for j in range(n_locations):
                # Demand constraint: transshipment in <= shortage
                shortage_j = D_k[j] - sales_direct[j, k]
                m.addConstr(
                    gp.quicksum(x[i, j, k] for i in range(n_locations)) <= shortage_j,
                    f"demand_{j}_{k}"
                )

        # Solve
        print("Solving two-stage stochastic optimization...")
        print(f"Number of scenarios: {K}")
        print(f"Number of decision variables: {m.NumVars}")
        print(f"Number of constraints: {m.NumConstrs}")
        print()

        m.optimize()

        if m.status == GRB.OPTIMAL:
            s_opt = np.array([s[i].X for i in range(n_locations)])

            # Calculate expected profit
            # Profit = Revenue - Procurement Cost - Transshipment Cost - Fixed Cost
            expected_profit = -m.objVal - fixed_cost

            # Detailed breakdown
            total_procurement = sum(cost * s[i].X for i in range(n_locations))

            # Calculate expected revenue and transship cost from solution
            total_revenue = 0
            total_transship_cost = 0

            for k in range(K):
                scenario_sales = sum(sales_direct[i, k].X for i in range(n_locations))
                scenario_transship = sum(x[i, j, k].X
                                        for i in range(n_locations)
                                        for j in range(n_locations))
                scenario_revenue = price * (scenario_sales + scenario_transship)

                scenario_transship_cost = sum(transship_cost[i, j] * x[i, j, k].X
                                             for i in range(n_locations)
                                             for j in range(n_locations))

                total_revenue += scenario_revenue
                total_transship_cost += scenario_transship_cost

            avg_revenue = total_revenue / K
            avg_transship_cost = total_transship_cost / K

            print("\n" + "="*80)
            print("OPTIMAL SOLUTION FOUND")
            print("="*80)
            print(f"\nOptimal Inventory Positions:")
            print(f"  Jurong West:    {s_opt[0]:.2f} units")
            print(f"  Orchard:        {s_opt[1]:.2f} units")
            print(f"  Harbour Front:  {s_opt[2]:.2f} units")
            print(f"  Total:          {sum(s_opt):.2f} units")
            print(f"\nExpected Profit: ${expected_profit:,.2f}")
            print(f"\nCost Breakdown:")
            print(f"  Procurement Cost:          ${total_procurement:,.2f}")
            print(f"  Expected Revenue:          ${avg_revenue:,.2f}")
            print(f"  Expected Transship Cost:   ${avg_transship_cost:,.2f}")
            print(f"  Fixed Service Cost:        ${fixed_cost:,.2f}")
            print("="*80)

            return s_opt, expected_profit

        elif m.status == GRB.TIME_LIMIT:
            print("Time limit reached. Returning best solution found.")
            if m.SolCount > 0:
                s_opt = np.array([s[i].X for i in range(n_locations)])
                expected_profit = -m.objVal - fixed_cost
                return s_opt, expected_profit
            else:
                print("No feasible solution found.")
                return None, None
        else:
            print(f"Optimization failed with status {m.status}")
            return None, None

    except Exception as e:
        print(f"Error during optimization: {e}")
        return None, None

def main():
    """
    Solve Question 2(d): Find optimal inventory placement with transshipment
    """
    # Parameters
    locations = ['Jurong West', 'Orchard', 'Harbour Front']
    mean_demands = np.array([300, 500, 500])
    std_demands = np.array([20, 20, 40])
    price, cost = 100, 50

    # Transshipment cost matrix
    transship_cost = np.array([
        [0, 22, 19],
        [22, 0, 7],
        [19, 7, 0]
    ])

    # Generate demand samples
    # Use smaller sample size for computational efficiency (can increase for better accuracy)
    n_simulations = 10000  # Use 10000 scenarios for better accuracy
    print(f"Generating {n_simulations} demand scenarios...")
    demands = generate_demands(mean_demands, std_demands, n_simulations, seed=42)

    # Solve two-stage stochastic optimization
    s_opt, expected_profit = solve_two_stage_saa(
        demands, transship_cost, price, cost, fixed_cost=200
    )

    if s_opt is not None:
        print(f"\nComparison with current policy (300, 500, 500):")
        print(f"  Current inventory: 1300 units")
        print(f"  Optimal inventory: {sum(s_opt):.2f} units")
        print(f"  Difference: {sum(s_opt) - 1300:.2f} units")

if __name__ == "__main__":
    main()
