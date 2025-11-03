import numpy as np

def generate_demands(mean_demands, std_demands, n_simulations=100000, seed=None):
    if seed is not None:
        np.random.seed(seed)
    mean_vector = np.array(mean_demands)
    cov_matrix = np.diag(np.array(std_demands) ** 2)
    demands = np.maximum(
        np.random.multivariate_normal(mean_vector, cov_matrix, size=n_simulations),
        0
    )
    return demands

def compute_profit_no_transshipment(demands, inventory, price=100, cost=50):
    n_simulations = demands.shape[0]
    sales_by_location = np.zeros((n_simulations, len(inventory)))
    for k in range(n_simulations):
        sales_by_location[k, :] = np.minimum(demands[k, :], inventory)
    expected_sales_per_location = np.mean(sales_by_location, axis=0)
    expected_total_sales = np.sum(expected_sales_per_location)
    total_procurement_cost = cost * np.sum(inventory)
    expected_profit = price * expected_total_sales - total_procurement_cost
    return expected_profit, expected_total_sales, expected_sales_per_location

def main():
    locations = ['Jurong West', 'Orchard', 'Harbour Front']
    mean_demands = np.array([300, 500, 500])
    std_demands = np.array([20, 20, 40])
    inventory = np.array([300, 500, 500])
    price, cost, n_simulations = 100, 50, 100000

    demands = generate_demands(mean_demands, std_demands, n_simulations, seed=42)
    expected_profit, expected_sales, expected_sales_per_loc = compute_profit_no_transshipment(
        demands, inventory, price, cost
    )

    print(f"{'Location':<20} {'Mean':>8} {'Std Dev':>10} {'Inventory':>10} {'Exp. Sales':>12}")
    print("-" * 70)
    for i, loc in enumerate(locations):
        print(f"{loc:<20} {mean_demands[i]:>8} {std_demands[i]:>10} {inventory[i]:>10} {expected_sales_per_loc[i]:>12.2f}")
    print("-" * 70)
    print(f"{'Total':<20} {np.sum(mean_demands):>8} {'-':>10} {np.sum(inventory):>10} {expected_sales:>12.2f}")
    print(f"\nExpected total profit: ${expected_profit:,.2f}")

if __name__ == "__main__":
    main()
