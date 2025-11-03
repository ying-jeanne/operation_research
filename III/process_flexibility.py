import numpy as np
import gurobipy as gp
from gurobipy import GRB
from scipy.stats import truncnorm
import matplotlib.pyplot as plt

def generate_truncated_normal_demand(mean=100, std=30, n_models=6, n_simulations=10000):
    """
    Generate truncated normal demand (truncated at 0)
    For N(mean, std^2) truncated at 0, the standardized lower bound is (0-mean)/std = -mean/std
    """
    lower_bound = -mean / std  # Standardized lower bound: (0 - mean) / std
    upper_bound = np.inf  # No upper bound
    demands = truncnorm.rvs(lower_bound, upper_bound, loc=mean, scale=std,
                           size=(n_simulations, n_models))
    return demands

def solve_allocation(capacity, demand, flexibility_matrix):
    """
    Solve the allocation problem given capacity, demand, and flexibility matrix
    flexibility_matrix[i,j] = 1 if plant i can produce model j

    Returns: total sales (satisfied demand)
    """
    n_plants = len(capacity)
    n_models = len(demand)

    try:
        m = gp.Model("production_allocation")
        m.setParam('OutputFlag', 0)
        m.setParam('LogToConsole', 0)

        x = m.addVars(n_plants, n_models, lb=0, name="x")
        sales = m.addVars(n_models, lb=0, name="sales")
        for j in range(n_models):
            m.addConstr(sales[j] <= demand[j], f"demand_{j}")
            m.addConstr(sales[j] <= gp.quicksum(x[i,j] for i in range(n_plants)), f"production_{j}")

        m.setObjective(gp.quicksum(sales[j] for j in range(n_models)), GRB.MAXIMIZE)

        # Capacity constraints
        for i in range(n_plants):
            m.addConstr(gp.quicksum(x[i,j] for j in range(n_models)) <= capacity[i], f"capacity_{i}")

        # Flexibility constraints
        for i in range(n_plants):
            for j in range(n_models):
                if flexibility_matrix[i, j] == 0:
                    m.addConstr(x[i,j] == 0, f"flex_{i}_{j}")
    
        m.optimize()

        if m.status == GRB.OPTIMAL:
            return m.objVal
        else:
            return 0
    except:
        return 0

def create_open_chain_design(n=6):
    """
    Open Chain Design
    Interpretation: Each plant can produce its own model and one adjacent model
    Pattern: 
    Plant 0: models 0, 1
    Plant 1: models 1, 2
    Plant 2: models 2, 3
    Plant 3: models 3, 4
    Plant 4: models 4, 5
    Plant 5: models 5
    """
    flex = np.zeros((n, n))
    for i in range(n):
        flex[i, i] = 1  # Each plant produces its own model
        if i < n-1:
            flex[i, i+1] = 1  # Can produce next model
    return flex

def create_long_chain_design(n=6):
    """
    Long Chain Design: On top of open chain, the last plant can also produce the first model
    Pattern: 
    Plant 0: models 0, 1
    Plant 1: models 1, 2
    Plant 2: models 2, 3
    Plant 3: models 3, 4
    Plant 4: models 4, 5
    Plant 5: model 5, 0 (to complete the chain)
    """
    flex = np.zeros((n, n))
    for i in range(n):
        flex[i, i] = 1  # Each plant produces its own model
        if i < n-1:
            flex[i, i+1] = 1  # Can produce next model in chain
        else:
            flex[i, 0] = 1  # Last plant can produce first model to complete the chain
    return flex

def simulate_design(flexibility_matrix, n_simulations=10000, capacity_per_plant=100,
                   mean_demand=100, std_demand=30, n_plants=6, n_models=6):
    """
    Simulate a production design and return average sales

    Uses multivariate normal with
    np.maximum for truncation at 0 (approximation of true truncated normal).
    """
    # For independent demands: diagonal covariance matrix
    mean_vector = np.full(n_models, mean_demand)
    cov_matrix = np.eye(n_models) * (std_demand ** 2)

    # Sample from multivariate normal and truncate at 0
    # Note: This creates a censored distribution (not true truncated normal)
    # but is the standard approach taught in class
    demands = np.maximum(np.random.multivariate_normal(mean_vector, cov_matrix, size=n_simulations), 0)

    # Alternative: Use scipy's truncnorm for mathematically exact truncated normal
    # demands = generate_truncated_normal_demand(mean_demand, std_demand, n_models, n_simulations)

    # Capacity vector
    capacity = np.array([capacity_per_plant] * n_plants)

    # Simulate
    sales = np.zeros(n_simulations)
    for sim in range(n_simulations):
        demand = demands[sim, :]
        sales[sim] = solve_allocation(capacity, demand, flexibility_matrix)

    return sales

def main():
    n_plants = 6
    n_models = 6
    capacity = 100
    n_simulations = 10000
    dedicated_avg = 525  # Given in question
    full_flex_avg = 570  # Given in question

    # Create and simulate designs
    open_chain_sales = simulate_design(create_open_chain_design(n_plants), n_simulations, capacity)
    long_chain_sales = simulate_design(create_long_chain_design(n_plants), n_simulations, capacity)

    # Calculate results
    open_chain_avg = np.mean(open_chain_sales)
    long_chain_avg = np.mean(long_chain_sales)
    total_benefit = full_flex_avg - dedicated_avg

    # Calculate number of arcs for each design
    n_conn_dedicated = n_plants  # Each plant produces only 1 model
    n_conn_open = int(np.sum(create_open_chain_design(n_plants)))
    n_conn_long = int(np.sum(create_long_chain_design(n_plants)))
    n_conn_full = n_plants * n_models  # Every plant can produce every model

    print(f"\n{'Design':<21} {'Avg Sales':>11} {'% of Full Flex':>15} {'arcs':>18}")
    print("-" * 72)
    print(f"{'Dedicated (given)':<21} {dedicated_avg:>11.2f} {dedicated_avg/full_flex_avg*100:>14.1f}% {n_conn_dedicated:>18}")
    print(f"{'(a) Open Chain':<21} {open_chain_avg:>11.2f} {open_chain_avg/full_flex_avg*100:>14.1f}% {n_conn_open:>18}")
    print(f"{'(b) Long Chain':<21} {long_chain_avg:>11.2f} {long_chain_avg/full_flex_avg*100:>14.1f}% {n_conn_long:>18}")
    print(f"{'Full Flexible (given)':<21} {full_flex_avg:>11.2f} {100:>14.1f}% {n_conn_full:>18}")
    print("=" * 72)

    # Visualize the sales distributions side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot Open Chain distribution
    ax1.hist(open_chain_sales, bins=60, range=(0, 600), edgecolor='black', alpha=0.7, color='steelblue')
    ax1.set_xlabel('Sales', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('(a) Open Chain Design', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.axvline(open_chain_avg, color='red', linestyle='--', linewidth=2, label=f'Mean: {open_chain_avg:.2f}')
    ax1.legend()

    # Plot Long Chain distribution
    ax2.hist(long_chain_sales, bins=60, range=(0, 600), edgecolor='black', alpha=0.7, color='coral')
    ax2.set_xlabel('Sales', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('(b) Long Chain Design', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    ax2.axvline(long_chain_avg, color='red', linestyle='--', linewidth=2, label=f'Mean: {long_chain_avg:.2f}')
    ax2.legend()

    plt.tight_layout()
    plt.savefig('chain_designs_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    main()
