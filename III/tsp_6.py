import numpy as np
import gurobipy as gp
from gurobipy import GRB
import itertools
import math

def solve_tsp_mtz(time_matrix, n_locations):
    """Solve TSP without time windows using MTZ formulation"""
    m = gp.Model("tsp_basic")
    m.setParam('OutputFlag', 0)

    x = m.addVars(n_locations, n_locations, vtype=GRB.BINARY, name="x")
    u = m.addVars(n_locations, lb=0, ub=n_locations-1, vtype=GRB.CONTINUOUS, name="u")

    m.setObjective(
        gp.quicksum(time_matrix[i, j] * x[i, j]
                   for i in range(n_locations)
                   for j in range(n_locations)),
        GRB.MINIMIZE
    )

    for i in range(n_locations):
        m.addConstr(gp.quicksum(x[i, j] for j in range(n_locations) if j != i) == 1)
        m.addConstr(gp.quicksum(x[j, i] for j in range(n_locations) if j != i) == 1)
        m.addConstr(x[i, i] == 0)

    for i in range(n_locations):
        for j in range(1, n_locations):
            if i != j:
                m.addConstr(u[i] + 1 - u[j] <= n_locations * (1 - x[i, j]))

    m.addConstr(u[0] == 0)
    m.optimize()

    if m.status == GRB.OPTIMAL:
        route = [0]
        current = 0
        while len(route) < n_locations:
            for j in range(n_locations):
                if j != current and x[current, j].X > 0.5:
                    route.append(j)
                    current = j
                    break

        total_time = sum(time_matrix[route[i], route[(i + 1) % len(route)]] 
                        for i in range(len(route)))
        return route, total_time

    return None, None

def solve_tsp_brute_force(time_matrix, max_waiting_times, n_locations):
    """Solve TSP with time windows using exhaustive enumeration"""
    customers = list(range(1, n_locations))
    feasible_routes = []

    for perm in itertools.permutations(customers):
        route = [0] + list(perm)
        arrival_times = [0] * len(route)
        
        for i in range(1, len(route)):
            arrival_times[i] = arrival_times[i-1] + time_matrix[route[i-1], route[i]]

        feasible = True
        for i in range(1, len(route)):
            loc = route[i]
            if max_waiting_times[loc] is not None and arrival_times[i] > max_waiting_times[loc]:
                feasible = False
                break

        if feasible:
            total_time = arrival_times[-1] + time_matrix[route[-1], route[0]]
            feasible_routes.append((route, arrival_times, total_time))

    if feasible_routes:
        feasible_routes.sort(key=lambda x: x[2])
        return feasible_routes[0]
    
    return None, None, None

def main():
    locations = {
        0: "Pickup (Location 1)",
        1: "Customer 2",
        2: "Customer 3",
        3: "Customer 4",
        4: "Customer 5",
        5: "Customer 6"
    }

    time_matrix = np.array([
        [0,  3,  3, 10,  9, 10],
        [3,  0,  3,  7,  6,  7],
        [3,  3,  0,  7,  6,  7],
        [10, 7,  7,  0,  1,  2],
        [9,  6,  6,  1,  0,  1],
        [10, 7,  7,  2,  1,  0]
    ])

    max_waiting_times = [None, 5, 10, 15, 13, 14]
    n_locations = len(locations)

    print("="*80)
    print("QUESTION 6: TSP WITH TIME WINDOW")
    print("="*80)

    # Part (a): TSP without time windows using MTZ
    print("\n" + "="*80)
    print("(a) TSP WITHOUT TIME WINDOWS (MTZ Formulation)")
    print("="*80)

    route_a, total_time_a = solve_tsp_mtz(time_matrix, n_locations)

    if route_a:
        print(f"\nMinimum Travel Time: {total_time_a:.0f} minutes")
        print(f"\nOptimal Route:")
        route_str = " -> ".join([locations[i] for i in route_a]) + f" -> {locations[0]}"
        print(f"  {route_str}")

        print(f"\nDetailed Route:")
        cumulative_time = 0
        for i in range(len(route_a)):
            from_loc = route_a[i]
            to_loc = route_a[(i + 1) % len(route_a)]
            travel_time = time_matrix[from_loc, to_loc]
            cumulative_time += travel_time
            print(f"  {locations[from_loc]:25s} -> {locations[to_loc]:25s}  "
                  f"Travel: {travel_time:2.0f} min, Cumulative: {cumulative_time:2.0f} min")

    # Part (b): TSP with time windows using brute force
    print("\n" + "="*80)
    print("(b) TSP WITH TIME WINDOWS (Exhaustive Enumeration)")
    print("="*80)
    print("\nTime Window Constraints:")
    for i in range(1, n_locations):
        print(f"  {locations[i]:25s}: Must arrive within {max_waiting_times[i]} minutes")

    print(f"\nChecking all {math.factorial(n_locations-1)} possible routes...")
    
    route_b, arrival_times, total_time_b = solve_tsp_brute_force(
        time_matrix, max_waiting_times, n_locations
    )

    if route_b:
        print(f"\nFeasible routes found: 1 out of {math.factorial(n_locations-1)}")
        print(f"\nMinimum Travel Time: {total_time_b:.0f} minutes")
        print(f"\nOptimal Route:")
        route_str = " -> ".join([locations[i] for i in route_b]) + f" -> {locations[0]}"
        print(f"  {route_str}")

        print(f"\nDetailed Route with Time Windows:")
        cumulative_time = 0
        for i in range(len(route_b)):
            from_loc = route_b[i]
            to_loc = route_b[(i + 1) % len(route_b)]
            travel_time = time_matrix[from_loc, to_loc]

            if to_loc == 0:
                cumulative_time += travel_time
                print(f"  {locations[from_loc]:25s} -> {locations[to_loc]:25s}  "
                      f"Travel: {travel_time:2.0f} min, Return at: {cumulative_time:2.0f} min")
            else:
                cumulative_time += travel_time
                max_wait = max_waiting_times[to_loc]
                status = "ok" if cumulative_time <= max_wait else "not ok"
                print(f"  {locations[from_loc]:25s} -> {locations[to_loc]:25s}  "
                      f"Travel: {travel_time:2.0f} min, Arrive: {cumulative_time:2.0f} min "
                      f"(max: {max_wait:2d} min) {status}")

        print("\n" + "-"*80)
        print("Time Window Verification:")
        print("-"*80)
        all_satisfied = True
        for i in range(1, len(route_b)):
            loc = route_b[i]
            arrival = arrival_times[i]
            max_wait = max_waiting_times[loc]
            satisfied = arrival <= max_wait
            all_satisfied = all_satisfied and satisfied
            status = "SATISFIED" if satisfied else "VIOLATED"
            print(f"  {locations[loc]:25s}: {arrival:5.0f} min <= {max_wait:2d} min  [{status}]")

        if all_satisfied:
            print("\nAll time window constraints are satisfied!")
    else:
        print("\nNo feasible solution found!")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
