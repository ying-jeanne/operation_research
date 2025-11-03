"""
Fairness Metrics and Alternative Objectives

VRP Connection: VRP literature extensively studies fairness in route allocation.
We apply similar concepts to rate allocation fairness.

Fairness concepts:
1. Jain's Fairness Index - measures how evenly resources are distributed
2. Proportional Fairness - log utility objective
3. Max-Min Fairness - maximize minimum allocation
"""

import numpy as np
from typing import List, Dict
from dataclasses import dataclass

from .rate_limiter_core import Client


@dataclass
class FairnessMetrics:
    """Collection of fairness measurements"""
    jains_index: float  # 0 to 1 (1 = perfectly fair)
    gini_coefficient: float  # 0 to 1 (0 = perfectly equal)
    min_allocation_ratio: float  # min(r_i / demand_i)
    max_allocation_ratio: float  # max(r_i / demand_i)
    coefficient_of_variation: float  # std / mean of allocations


def compute_jains_fairness_index(allocations: List[float]) -> float:
    """
    Compute Jain's Fairness Index.

    Formula: (Σ x_i)^2 / (n * Σ x_i^2)

    Returns value in [0, 1] where:
    - 1.0 = perfectly fair (all equal)
    - 1/n = perfectly unfair (one gets everything)

    Args:
        allocations: List of allocated rates

    Returns:
        Jain's fairness index (0 to 1)
    """
    if not allocations or len(allocations) == 0:
        return 0.0

    allocations = np.array(allocations)
    n = len(allocations)

    sum_x = np.sum(allocations)
    sum_x_squared = np.sum(allocations ** 2)

    if sum_x_squared == 0:
        return 1.0  # All zeros = fair (edge case)

    jains_index = (sum_x ** 2) / (n * sum_x_squared)
    return jains_index


def compute_gini_coefficient(allocations: List[float]) -> float:
    """
    Compute Gini coefficient (inequality measure from economics).

    Returns value in [0, 1] where:
    - 0 = perfect equality
    - 1 = perfect inequality

    Args:
        allocations: List of allocated rates

    Returns:
        Gini coefficient (0 to 1)
    """
    if not allocations or len(allocations) == 0:
        return 0.0

    allocations = np.array(allocations)
    allocations = np.sort(allocations)
    n = len(allocations)

    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * allocations)) / (n * np.sum(allocations)) - (n + 1) / n

    return max(0.0, gini)  # Ensure non-negative


def compute_allocation_ratios(clients: List[Client],
                              allocations: Dict[str, float]) -> tuple:
    """
    Compute allocation ratios (allocated / demanded) for each client.

    Returns:
        (min_ratio, max_ratio, ratios_dict)
    """
    ratios = {}
    for client in clients:
        allocated = allocations.get(client.id, 0.0)
        if client.current_demand > 0:
            ratio = allocated / client.current_demand
        else:
            ratio = 1.0 if allocated == 0 else float('inf')
        ratios[client.id] = ratio

    if ratios:
        min_ratio = min(ratios.values())
        max_ratio = max(ratios.values())
    else:
        min_ratio = max_ratio = 0.0

    return min_ratio, max_ratio, ratios


def evaluate_fairness(clients: List[Client],
                     allocations: Dict[str, float]) -> FairnessMetrics:
    """
    Compute comprehensive fairness metrics for a solution.

    Args:
        clients: List of clients
        allocations: Dictionary of client_id -> allocated_rate

    Returns:
        FairnessMetrics object
    """
    allocation_values = [allocations.get(c.id, 0.0) for c in clients]

    # Jain's fairness index
    jains = compute_jains_fairness_index(allocation_values)

    # Gini coefficient
    gini = compute_gini_coefficient(allocation_values)

    # Allocation ratios
    min_ratio, max_ratio, _ = compute_allocation_ratios(clients, allocations)

    # Coefficient of variation
    if len(allocation_values) > 0 and np.mean(allocation_values) > 0:
        cv = np.std(allocation_values) / np.mean(allocation_values)
    else:
        cv = 0.0

    return FairnessMetrics(
        jains_index=jains,
        gini_coefficient=gini,
        min_allocation_ratio=min_ratio,
        max_allocation_ratio=max_ratio,
        coefficient_of_variation=cv
    )


def compare_fairness_objectives():
    """
    Demonstrate different fairness-focused objective functions.

    Standard objective:     max Σ w_i * r_i
    Proportional fairness:  max Σ w_i * log(r_i)  (favors balanced allocation)
    Max-min fairness:       max min{r_i}          (help smallest clients)
    """
    from .rate_limiter_core import create_example_clients, RateLimiterLP

    print("=" * 70)
    print("Fairness Comparison: Different Objective Functions")
    print("=" * 70)

    clients = create_example_clients()

    # High load scenario
    for c in clients:
        c.current_demand *= 1.5

    print("\nClient configurations:")
    for c in clients:
        print(f"  {c.id:10s}: weight={c.weight:5.1f}, demand={c.current_demand:5.1f}, "
              f"min_rate={c.min_rate:5.1f}")

    # Objective 1: Standard weighted throughput
    print("\n--- Objective 1: Weighted Throughput (max Σ w_i * r_i) ---")
    limiter1 = RateLimiterLP(capacity=100.0)
    solution1 = limiter1.solve(clients, verbose=False)

    print(f"Objective value: {solution1.objective_value:.2f}")
    print(f"Dual price: ${solution1.dual_price:.4f}")
    print("\nAllocations:")
    for client_id, rate in solution1.allocated_rates.items():
        client = next(c for c in clients if c.id == client_id)
        ratio = rate / client.current_demand if client.current_demand > 0 else 0
        print(f"  {client_id:10s}: {rate:6.2f} req/s ({ratio:5.1%} of demand)")

    metrics1 = evaluate_fairness(clients, solution1.allocated_rates)
    print(f"\nFairness metrics:")
    print(f"  Jain's index: {metrics1.jains_index:.4f}")
    print(f"  Gini coefficient: {metrics1.gini_coefficient:.4f}")
    print(f"  Min/Max allocation ratio: {metrics1.min_allocation_ratio:.2f} / {metrics1.max_allocation_ratio:.2f}")

    # Objective 2: Equal weights (fairness-focused)
    print("\n--- Objective 2: Equal Weights (Fair Throughput) ---")
    equal_weight_clients = []
    for c in clients:
        from dataclasses import replace
        c_equal = replace(c, weight=1.0)  # Equal weights
        equal_weight_clients.append(c_equal)

    limiter2 = RateLimiterLP(capacity=100.0)
    solution2 = limiter2.solve(equal_weight_clients, verbose=False)

    print(f"Objective value: {solution2.objective_value:.2f}")
    print(f"Dual price: ${solution2.dual_price:.4f}")
    print("\nAllocations:")
    for client_id, rate in solution2.allocated_rates.items():
        client = next(c for c in clients if c.id == client_id)
        ratio = rate / client.current_demand if client.current_demand > 0 else 0
        print(f"  {client_id:10s}: {rate:6.2f} req/s ({ratio:5.1%} of demand)")

    metrics2 = evaluate_fairness(clients, solution2.allocated_rates)
    print(f"\nFairness metrics:")
    print(f"  Jain's index: {metrics2.jains_index:.4f}")
    print(f"  Gini coefficient: {metrics2.gini_coefficient:.4f}")
    print(f"  Min/Max allocation ratio: {metrics2.min_allocation_ratio:.2f} / {metrics2.max_allocation_ratio:.2f}")

    # Comparison
    print("\n--- FAIRNESS COMPARISON ---")
    print(f"{'Metric':<30} {'Weighted':>12} {'Equal Weights':>15}")
    print("-" * 60)
    print(f"{'Jain\'s Index (higher=fairer)':<30} {metrics1.jains_index:>12.4f} {metrics2.jains_index:>15.4f}")
    print(f"{'Gini Coefficient (lower=fairer)':<30} {metrics1.gini_coefficient:>12.4f} {metrics2.gini_coefficient:>15.4f}")
    print(f"{'Objective Value':<30} {solution1.objective_value:>12.2f} {solution2.objective_value:>15.2f}")

    print("\nConclusion:")
    print("  - Weighted throughput maximizes value but may be less fair")
    print("  - Equal weights improve fairness but reduce total value")
    print("  - Trade-off between efficiency (value) and fairness")


if __name__ == "__main__":
    compare_fairness_objectives()
