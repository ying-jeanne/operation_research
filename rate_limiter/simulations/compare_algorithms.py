"""
Algorithm Comparison and Benchmarking

Compares different rate limiting approaches:
1. Static Token Bucket (baseline)
2. Basic LP (no VRP enhancements)
3. VRP-Enhanced LP (warm start + robust + triggers)

Evaluation metrics:
- Request acceptance rate
- Fairness (Jain's index)
- SLA compliance
- System utilization
- Revenue
- Price stability
- Solving time
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import time
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rate_limiter_core import Client, RateLimiterLP, RateLimiterSolution
from src.vrp_enhancements import VRPEnhancedRateLimiter, RobustConfig, RollingHorizonConfig, TriggerConfig
from src.fairness_metrics import evaluate_fairness, FairnessMetrics
from src.dynamic_pricing import DynamicPricingController, Request, RequestDecision
from workload_generator import WorkloadGenerator, WorkloadConfig


@dataclass
class AlgorithmResult:
    """Results from running one algorithm on a workload"""
    algorithm_name: str
    acceptance_rate: float
    sla_compliance_rate: float
    avg_utilization: float
    total_revenue: float
    jains_fairness_index: float
    gini_coefficient: float
    price_mean: float
    price_std: float
    avg_solve_time_ms: float
    total_solves: int
    total_skipped: int


class StaticTokenBucket:
    """
    Baseline: Static token bucket rate limiter.

    Each client gets a fixed quota (token bucket). Simple but inflexible.
    """

    def __init__(self, capacity: float):
        self.capacity = capacity
        self.quotas = {}  # client_id -> quota (req/s)

    def allocate_quotas(self, clients: List[Client]):
        """Allocate fixed quotas based on tiers"""
        premium_clients = [c for c in clients if c.tier == "premium"]
        other_clients = [c for c in clients if c.tier != "premium"]

        # Premium gets their min_rate
        remaining_capacity = self.capacity
        for c in premium_clients:
            self.quotas[c.id] = c.min_rate
            remaining_capacity -= c.min_rate

        # Others share remaining capacity equally
        if other_clients and remaining_capacity > 0:
            quota_per_other = remaining_capacity / len(other_clients)
            for c in other_clients:
                self.quotas[c.id] = quota_per_other

    def get_allocation(self, clients: List[Client]) -> Dict[str, float]:
        """Return static allocations"""
        if not self.quotas:
            self.allocate_quotas(clients)
        return self.quotas.copy()


def run_static_token_bucket(workload: Dict[float, List[Client]],
                            capacity: float) -> AlgorithmResult:
    """Run static token bucket algorithm"""
    print("Running: Static Token Bucket...")

    token_bucket = StaticTokenBucket(capacity)
    timestamps = sorted(workload.keys())

    # Initialize on first timestep
    first_clients = workload[timestamps[0]]
    token_bucket.allocate_quotas(first_clients)

    # Track metrics
    acceptance_rates = []
    utilizations = []
    sla_violations = 0
    total_allocated = 0
    total_demanded = 0

    fairness_metrics_list = []

    for ts in timestamps:
        clients = workload[ts]
        allocations = token_bucket.get_allocation(clients)

        # Check acceptance
        for client in clients:
            allocated = allocations.get(client.id, 0)
            accepted = min(allocated, client.current_demand)
            acceptance_rates.append(accepted / client.current_demand if client.current_demand > 0 else 1.0)

            total_allocated += allocated
            total_demanded += client.current_demand

            # Check SLA
            if client.min_rate > 0 and allocated < client.min_rate:
                sla_violations += 1

        # Fairness
        metrics = evaluate_fairness(clients, allocations)
        fairness_metrics_list.append(metrics)

        # Utilization
        utilizations.append(sum(allocations.values()) / capacity)

    # Aggregate results
    return AlgorithmResult(
        algorithm_name="Static Token Bucket",
        acceptance_rate=np.mean(acceptance_rates),
        sla_compliance_rate=1.0 - (sla_violations / (len(timestamps) * len(first_clients))),
        avg_utilization=np.mean(utilizations),
        total_revenue=0.0,  # No dynamic pricing
        jains_fairness_index=np.mean([m.jains_index for m in fairness_metrics_list]),
        gini_coefficient=np.mean([m.gini_coefficient for m in fairness_metrics_list]),
        price_mean=0.0,
        price_std=0.0,
        avg_solve_time_ms=0.0,  # No solving
        total_solves=0,
        total_skipped=0
    )


def run_basic_lp(workload: Dict[float, List[Client]],
                capacity: float) -> AlgorithmResult:
    """Run basic LP (no VRP enhancements)"""
    print("Running: Basic LP...")

    limiter = RateLimiterLP(capacity=capacity, use_gurobi=True)
    timestamps = sorted(workload.keys())

    solve_times = []
    acceptance_rates = []
    utilizations = []
    dual_prices = []
    sla_violations = 0
    total_revenue = 0.0
    fairness_metrics_list = []

    pricing_controller = DynamicPricingController(enable_charging=True)

    for ts in timestamps:
        clients = workload[ts]

        # Solve LP (no warm start)
        solution = limiter.solve(clients, warm_start=False, verbose=False)
        solve_times.append(solution.solve_time)
        dual_prices.append(solution.dual_price)

        # Process requests
        for client in clients:
            allocated = solution.allocated_rates.get(client.id, 0)
            accepted = min(allocated, client.current_demand)
            acceptance_rates.append(accepted / client.current_demand if client.current_demand > 0 else 1.0)

            # Dynamic pricing
            request = Request(
                client_id=client.id,
                timestamp=ts,
                tier=client.tier,
                max_price=client.max_willingness_to_pay
            )
            outcome = pricing_controller.process_request(request, solution.dual_price)
            if outcome.decision == RequestDecision.ACCEPTED_CHARGED:
                total_revenue += outcome.charge

            # Check SLA
            if client.min_rate > 0 and allocated < client.min_rate:
                sla_violations += 1

        # Fairness and utilization
        metrics = evaluate_fairness(clients, solution.allocated_rates)
        fairness_metrics_list.append(metrics)
        utilizations.append(sum(solution.allocated_rates.values()) / capacity)

    return AlgorithmResult(
        algorithm_name="Basic LP",
        acceptance_rate=np.mean(acceptance_rates),
        sla_compliance_rate=1.0 - (sla_violations / (len(timestamps) * len(workload[timestamps[0]]))),
        avg_utilization=np.mean(utilizations),
        total_revenue=total_revenue,
        jains_fairness_index=np.mean([m.jains_index for m in fairness_metrics_list]),
        gini_coefficient=np.mean([m.gini_coefficient for m in fairness_metrics_list]),
        price_mean=np.mean(dual_prices),
        price_std=np.std(dual_prices),
        avg_solve_time_ms=np.mean(solve_times) * 1000,
        total_solves=limiter.solve_count,
        total_skipped=0
    )


def run_vrp_enhanced(workload: Dict[float, List[Client]],
                    capacity: float) -> AlgorithmResult:
    """Run VRP-enhanced LP"""
    print("Running: VRP-Enhanced LP...")

    limiter = VRPEnhancedRateLimiter(
        capacity=capacity,
        robust_config=RobustConfig(enable_buffer=True, buffer_percentile=0.95),
        rolling_horizon_config=RollingHorizonConfig(enabled=True, num_periods=3),
        trigger_config=TriggerConfig(
            time_threshold=30.0,  # Every 30s
            load_change_threshold=0.20,  # 20% load change
            price_change_threshold=0.30  # 30% price change
        ),
        use_gurobi=True
    )

    timestamps = sorted(workload.keys())

    solve_times = []
    acceptance_rates = []
    utilizations = []
    dual_prices = []
    sla_violations = 0
    total_revenue = 0.0
    fairness_metrics_list = []

    pricing_controller = DynamicPricingController(enable_charging=True)

    for i, ts in enumerate(timestamps):
        clients = workload[ts]

        # Solve with VRP enhancements
        solution = limiter.solve_with_rolling_horizon(
            clients=clients,
            current_time=ts,
            forecast_demands=None,  # Could add forecasting
            verbose=False
        )

        solve_times.append(solution.solve_time)
        dual_prices.append(solution.dual_price)  # Smoothed price

        # Process requests
        for client in clients:
            allocated = solution.allocated_rates.get(client.id, 0)
            accepted = min(allocated, client.current_demand)
            acceptance_rates.append(accepted / client.current_demand if client.current_demand > 0 else 1.0)

            # Dynamic pricing
            request = Request(
                client_id=client.id,
                timestamp=ts,
                tier=client.tier,
                max_price=client.max_willingness_to_pay
            )
            outcome = pricing_controller.process_request(request, solution.dual_price)
            if outcome.decision == RequestDecision.ACCEPTED_CHARGED:
                total_revenue += outcome.charge

            # Check SLA
            if client.min_rate > 0 and allocated < client.min_rate:
                sla_violations += 1

        # Fairness and utilization
        metrics = evaluate_fairness(clients, solution.allocated_rates)
        fairness_metrics_list.append(metrics)
        utilizations.append(sum(solution.allocated_rates.values()) / limiter.solver.capacity)

    stats = limiter.get_statistics()

    return AlgorithmResult(
        algorithm_name="VRP-Enhanced LP",
        acceptance_rate=np.mean(acceptance_rates),
        sla_compliance_rate=1.0 - (sla_violations / (len(timestamps) * len(workload[timestamps[0]]))),
        avg_utilization=np.mean(utilizations),
        total_revenue=total_revenue,
        jains_fairness_index=np.mean([m.jains_index for m in fairness_metrics_list]),
        gini_coefficient=np.mean([m.gini_coefficient for m in fairness_metrics_list]),
        price_mean=np.mean(dual_prices),
        price_std=np.std(dual_prices),
        avg_solve_time_ms=np.mean(solve_times) * 1000,
        total_solves=stats['total_solves'],
        total_skipped=stats['skipped_solves']
    )


def print_comparison_table(results: List[AlgorithmResult]):
    """Print formatted comparison table"""
    print("\n" + "=" * 100)
    print("ALGORITHM COMPARISON RESULTS")
    print("=" * 100)

    # Convert to DataFrame for nice formatting
    df = pd.DataFrame([asdict(r) for r in results])

    # Format specific columns
    df['acceptance_rate'] = df['acceptance_rate'].apply(lambda x: f"{x:.2%}")
    df['sla_compliance_rate'] = df['sla_compliance_rate'].apply(lambda x: f"{x:.2%}")
    df['avg_utilization'] = df['avg_utilization'].apply(lambda x: f"{x:.2%}")
    df['total_revenue'] = df['total_revenue'].apply(lambda x: f"${x:.2f}")
    df['jains_fairness_index'] = df['jains_fairness_index'].apply(lambda x: f"{x:.4f}")
    df['price_mean'] = df['price_mean'].apply(lambda x: f"${x:.4f}")
    df['price_std'] = df['price_std'].apply(lambda x: f"${x:.4f}")
    df['avg_solve_time_ms'] = df['avg_solve_time_ms'].apply(lambda x: f"{x:.2f}ms")

    print("\n" + df.to_string(index=False))

    # Print summary insights
    print("\n" + "=" * 100)
    print("KEY INSIGHTS")
    print("=" * 100)

    # Find best in each category
    results_dict = {r.algorithm_name: r for r in results}

    best_acceptance = max(results, key=lambda r: r.acceptance_rate)
    best_sla = max(results, key=lambda r: r.sla_compliance_rate)
    best_revenue = max(results, key=lambda r: r.total_revenue)
    best_fairness = max(results, key=lambda r: r.jains_fairness_index)

    # Handle cases where some algorithms don't have prices or solve times
    price_results = [r for r in results if r.price_std > 0]
    most_stable_price = min(price_results, key=lambda r: r.price_std) if price_results else None

    solve_results = [r for r in results if r.avg_solve_time_ms > 0]
    fastest_solve = min(solve_results, key=lambda r: r.avg_solve_time_ms) if solve_results else None

    print(f"\n✓ Best Acceptance Rate: {best_acceptance.algorithm_name} ({best_acceptance.acceptance_rate:.2%})")
    print(f"✓ Best SLA Compliance: {best_sla.algorithm_name} ({best_sla.sla_compliance_rate:.2%})")
    print(f"✓ Highest Revenue: {best_revenue.algorithm_name} (${best_revenue.total_revenue:.2f})")
    print(f"✓ Most Fair: {best_fairness.algorithm_name} (Jain's: {best_fairness.jains_fairness_index:.4f})")

    if most_stable_price:
        print(f"✓ Most Stable Pricing: {most_stable_price.algorithm_name} (σ=${most_stable_price.price_std:.4f})")

    if fastest_solve:
        print(f"✓ Fastest Solving: {fastest_solve.algorithm_name} ({fastest_solve.avg_solve_time_ms:.2f}ms)")

    # VRP enhancement impact
    if 'Basic LP' in results_dict and 'VRP-Enhanced LP' in results_dict:
        basic = results_dict['Basic LP']
        enhanced = results_dict['VRP-Enhanced LP']

        speedup = basic.avg_solve_time_ms / enhanced.avg_solve_time_ms if enhanced.avg_solve_time_ms > 0 else 0
        price_stability_improvement = (basic.price_std - enhanced.price_std) / basic.price_std if basic.price_std > 0 else 0

        print(f"\nVRP Enhancement Impact:")
        print(f"  Solving speedup: {speedup:.2f}x")
        print(f"  Price volatility reduction: {price_stability_improvement:.1%}")
        print(f"  Solves skipped: {enhanced.total_skipped}/{enhanced.total_solves + enhanced.total_skipped} ({enhanced.total_skipped/(enhanced.total_solves+enhanced.total_skipped):.1%})")


def run_full_comparison(workload_pattern: str = "bursty"):
    """Run full comparison across all algorithms"""
    print("=" * 100)
    print(f"FULL ALGORITHM COMPARISON - Pattern: {workload_pattern.upper()}")
    print("=" * 100)

    # Generate workload
    config = WorkloadConfig(
        duration_seconds=300.0,
        time_step=10.0,
        base_capacity=100.0,
        pattern=workload_pattern,
        noise_level=0.15
    )

    generator = WorkloadGenerator(config)
    workload = generator.generate_client_demands()

    print(f"\nWorkload generated: {len(workload)} timesteps over {config.duration_seconds}s")
    stats = generator.compute_statistics(workload)
    print(f"Average demand: {stats['total_demand_mean']:.2f} req/s ({stats['avg_utilization']:.1%} utilization)")
    print(f"Peak demand: {stats['total_demand_max']:.2f} req/s ({stats['peak_utilization']:.1%} utilization)")

    # Run all algorithms
    results = []

    results.append(run_static_token_bucket(workload, config.base_capacity))
    results.append(run_basic_lp(workload, config.base_capacity))
    results.append(run_vrp_enhanced(workload, config.base_capacity))

    # Print results
    print_comparison_table(results)

    # Save results
    results_dir = "../results/tables"
    os.makedirs(results_dir, exist_ok=True)
    results_file = f"{results_dir}/comparison_{workload_pattern}.json"

    results_dict = {r.algorithm_name: asdict(r) for r in results}
    with open(results_file, 'w') as f:
        json.dump(results_dict, f, indent=2)

    print(f"\nResults saved to: {results_file}")

    return results


if __name__ == "__main__":
    # Run comparison on different workload patterns
    patterns = ["bursty", "ramp", "periodic"]

    for pattern in patterns:
        results = run_full_comparison(workload_pattern=pattern)
        print("\n" + "="*100 + "\n")
