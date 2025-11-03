"""
Compare basic rate limiter vs multi-resource rate limiter.

This demonstrates why multi-resource modeling is important:
1. Basic model may allocate rates that violate CPU/memory/network limits
2. Multi-resource model correctly accounts for all bottlenecks
3. Different objectives (throughput vs revenue) produce different allocations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rate_limiter_core import Client, RateLimiterLP
from src.multi_resource_limiter import (
    MultiResourceClient,
    MultiResourceRateLimiter,
    ResourceProfile,
    SystemResources
)


def create_test_scenario():
    """
    Create a test scenario where basic model fails.

    Scenario: System with limited CPU and memory
    - Alice: CPU-heavy (ML inference)
    - Bob: Memory-heavy (caching)
    - Carol: Network-heavy (streaming)

    Basic model only sees aggregate capacity (100 req/s)
    Multi-resource model sees CPU, memory, network separately
    """

    # System resources
    resources = SystemResources(
        cpu_capacity_ms=1000.0,  # 1 second of CPU per second
        memory_capacity_mb=2048.0,  # 2GB memory
        network_capacity_kb=10000.0  # 10 MB/s network
    )

    # Clients with heterogeneous resource profiles
    multi_clients = [
        MultiResourceClient(
            id="alice",
            tier="premium",
            weight=10.0,
            min_rate=5.0,
            max_willingness_to_pay=0.50,
            current_demand=30.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=80.0,  # Very CPU-heavy!
                memory_mb_per_request=200.0,
                network_kb_per_request=100.0,
                max_response_time_ms=500.0
            )
        ),
        MultiResourceClient(
            id="bob",
            tier="standard",
            weight=5.0,
            min_rate=0.0,
            max_willingness_to_pay=0.20,
            current_demand=40.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=20.0,
                memory_mb_per_request=400.0,  # Very memory-heavy!
                network_kb_per_request=200.0,
                max_response_time_ms=200.0
            )
        ),
        MultiResourceClient(
            id="carol",
            tier="free",
            weight=1.0,
            min_rate=0.0,
            max_willingness_to_pay=0.005,
            current_demand=60.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=5.0,
                memory_mb_per_request=50.0,
                network_kb_per_request=2000.0,  # Very network-heavy!
                max_response_time_ms=100.0
            )
        ),
        MultiResourceClient(
            id="dave",
            tier="standard",
            weight=5.0,
            min_rate=0.0,
            max_willingness_to_pay=0.15,
            current_demand=50.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=30.0,
                memory_mb_per_request=150.0,
                network_kb_per_request=500.0,
                max_response_time_ms=300.0
            )
        )
    ]

    # Basic clients (same weights/demands, no resource info)
    basic_clients = [
        Client(
            id=c.id,
            tier=c.tier,
            weight=c.weight,
            min_rate=c.min_rate,
            max_willingness_to_pay=c.max_willingness_to_pay,
            current_demand=c.current_demand
        )
        for c in multi_clients
    ]

    return resources, basic_clients, multi_clients


def check_resource_violations(clients, allocations, resources):
    """
    Check if allocations violate any resource constraints.

    Returns: (violations_dict, total_usage_dict)
    """
    total_cpu = 0.0
    total_memory = 0.0
    total_network = 0.0

    for client in clients:
        rate = allocations.get(client.id, 0.0)
        total_cpu += rate * client.resource_profile.cpu_ms_per_request
        total_memory += rate * client.resource_profile.memory_mb_per_request
        total_network += rate * client.resource_profile.network_kb_per_request

    violations = {}
    if total_cpu > resources.cpu_capacity_ms:
        violations['cpu'] = (total_cpu - resources.cpu_capacity_ms) / resources.cpu_capacity_ms
    if total_memory > resources.memory_capacity_mb:
        violations['memory'] = (total_memory - resources.memory_capacity_mb) / resources.memory_capacity_mb
    if total_network > resources.network_capacity_kb:
        violations['network'] = (total_network - resources.network_capacity_kb) / resources.network_capacity_kb

    usage = {
        'cpu': total_cpu / resources.cpu_capacity_ms,
        'memory': total_memory / resources.memory_capacity_mb,
        'network': total_network / resources.network_capacity_kb
    }

    return violations, usage


def main():
    print("=" * 80)
    print("COMPARISON: Basic Rate Limiter vs Multi-Resource Rate Limiter")
    print("=" * 80)

    resources, basic_clients, multi_clients = create_test_scenario()

    print("\nSystem Resources:")
    print(f"  {resources}")

    print("\nClient Demands:")
    total_demand = sum(c.current_demand for c in multi_clients)
    print(f"  Total: {total_demand:.1f} req/s")
    for client in multi_clients:
        print(f"    {client.id:10s}: {client.current_demand:5.1f} req/s  "
              f"Profile: {client.resource_profile}")

    # Solve with basic model
    print("\n" + "=" * 80)
    print("APPROACH 1: Basic Rate Limiter (Single Capacity Constraint)")
    print("=" * 80)

    # Assume aggregate capacity = 100 req/s
    basic_limiter = RateLimiterLP(capacity=100.0, use_gurobi=True)
    basic_solution = basic_limiter.solve(basic_clients, verbose=False)

    print(f"\nObjective value: {basic_solution.objective_value:.2f}")
    print(f"Dual price (π): ${basic_solution.dual_price:.4f}/req")
    print(f"Solve time: {basic_solution.solve_time_ms:.2f}ms")

    print("\nAllocations:")
    total_allocated_basic = 0.0
    for client in basic_clients:
        allocated = basic_solution.allocated_rates[client.id]
        ratio = allocated / client.current_demand if client.current_demand > 0 else 0
        print(f"  {client.id:10s}: {allocated:6.2f} req/s ({ratio:5.1%} of demand)")
        total_allocated_basic += allocated

    print(f"\n  Total allocated: {total_allocated_basic:.2f} req/s")

    # Check if this violates resource constraints
    print("\nResource Constraint Check:")
    violations, usage = check_resource_violations(multi_clients, basic_solution.allocated_rates, resources)

    for resource, util in usage.items():
        status = "✓ OK" if resource not in violations else f"✗ VIOLATED by {violations[resource]:.1%}"
        print(f"  {resource.upper():8s}: {util:6.1%} utilization  {status}")

    if violations:
        print("\n⚠️  WARNING: Basic model violates resource constraints!")
        print("    The allocated rates would crash the system!")

    # Solve with multi-resource model (throughput objective)
    print("\n" + "=" * 80)
    print("APPROACH 2: Multi-Resource Rate Limiter (Throughput Objective)")
    print("=" * 80)

    multi_limiter_throughput = MultiResourceRateLimiter(
        system_resources=resources,
        objective_type="throughput"
    )

    multi_solution_throughput = multi_limiter_throughput.solve(multi_clients, verbose=False)

    print(f"\nObjective value: {multi_solution_throughput.objective_value:.2f}")
    print(f"Solve time: {multi_solution_throughput.solve_time_ms:.2f}ms")

    print("\nDual Prices (per resource):")
    print(f"  π_cpu:     ${multi_solution_throughput.dual_price_cpu:.6f} per ms")
    print(f"  π_memory:  ${multi_solution_throughput.dual_price_memory:.6f} per MB")
    print(f"  π_network: ${multi_solution_throughput.dual_price_network:.6f} per KB")

    print("\nResource Utilization:")
    print(f"  CPU:     {multi_solution_throughput.cpu_utilization:6.1%}")
    print(f"  Memory:  {multi_solution_throughput.memory_utilization:6.1%}")
    print(f"  Network: {multi_solution_throughput.network_utilization:6.1%}")

    print("\nAllocations:")
    total_allocated_multi = 0.0
    for client in multi_clients:
        allocated = multi_solution_throughput.allocated_rates[client.id]
        ratio = allocated / client.current_demand if client.current_demand > 0 else 0
        rt = multi_solution_throughput.estimated_response_times[client.id]
        price = multi_limiter_throughput.get_composite_price(multi_solution_throughput, client)

        print(f"  {client.id:10s}: {allocated:6.2f} req/s ({ratio:5.1%} of demand)")
        print(f"              RT: {rt:5.1f}ms  Price: ${price:.4f}/req")
        total_allocated_multi += allocated

    print(f"\n  Total allocated: {total_allocated_multi:.2f} req/s")

    # Solve with multi-resource model (revenue objective)
    print("\n" + "=" * 80)
    print("APPROACH 3: Multi-Resource Rate Limiter (Revenue Objective)")
    print("=" * 80)

    multi_limiter_revenue = MultiResourceRateLimiter(
        system_resources=resources,
        objective_type="revenue"
    )

    multi_solution_revenue = multi_limiter_revenue.solve(multi_clients, verbose=False)

    print(f"\nObjective value (revenue): ${multi_solution_revenue.objective_value:.2f}")
    print(f"Solve time: {multi_solution_revenue.solve_time_ms:.2f}ms")

    print("\nResource Utilization:")
    print(f"  CPU:     {multi_solution_revenue.cpu_utilization:6.1%}")
    print(f"  Memory:  {multi_solution_revenue.memory_utilization:6.1%}")
    print(f"  Network: {multi_solution_revenue.network_utilization:6.1%}")

    print("\nAllocations:")
    total_allocated_revenue = 0.0
    for client in multi_clients:
        allocated = multi_solution_revenue.allocated_rates[client.id]
        ratio = allocated / client.current_demand if client.current_demand > 0 else 0
        rt = multi_solution_revenue.estimated_response_times[client.id]
        price = multi_limiter_revenue.get_composite_price(multi_solution_revenue, client)

        print(f"  {client.id:10s}: {allocated:6.2f} req/s ({ratio:5.1%} of demand)")
        print(f"              RT: {rt:5.1f}ms  Price: ${price:.4f}/req")
        total_allocated_revenue += allocated

    print(f"\n  Total allocated: {total_allocated_revenue:.2f} req/s")

    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY: Why Multi-Resource Modeling Matters")
    print("=" * 80)

    print(f"\n1. Total Throughput:")
    print(f"   Basic model:              {total_allocated_basic:.2f} req/s")
    print(f"   Multi-resource (throughput): {total_allocated_multi:.2f} req/s")
    print(f"   Multi-resource (revenue):    {total_allocated_revenue:.2f} req/s")

    print(f"\n2. Resource Violations:")
    if violations:
        print(f"   Basic model: VIOLATES constraints ({len(violations)} violations)")
        for resource, pct in violations.items():
            print(f"     - {resource.upper()}: over by {pct:.1%}")
    else:
        print(f"   Basic model: No violations (got lucky!)")
    print(f"   Multi-resource model: Always respects all constraints")

    print(f"\n3. Bottleneck Identification:")
    bottleneck_throughput = max(
        [("CPU", multi_solution_throughput.cpu_utilization),
         ("Memory", multi_solution_throughput.memory_utilization),
         ("Network", multi_solution_throughput.network_utilization)],
        key=lambda x: x[1]
    )
    bottleneck_revenue = max(
        [("CPU", multi_solution_revenue.cpu_utilization),
         ("Memory", multi_solution_revenue.memory_utilization),
         ("Network", multi_solution_revenue.network_utilization)],
        key=lambda x: x[1]
    )
    print(f"   Throughput objective: {bottleneck_throughput[0]} is bottleneck ({bottleneck_throughput[1]:.1%})")
    print(f"   Revenue objective:    {bottleneck_revenue[0]} is bottleneck ({bottleneck_revenue[1]:.1%})")

    print(f"\n4. Pricing Insights:")
    print(f"   Basic model: Single price π = ${basic_solution.dual_price:.4f}/req")
    print(f"   Multi-resource model: Composite prices based on resource usage")
    print(f"     Example (Alice): ${multi_limiter_throughput.get_composite_price(multi_solution_throughput, multi_clients[0]):.4f}/req")
    print(f"       (Reflects high CPU usage)")

    print(f"\n5. Objective Comparison:")
    print(f"   Throughput objective: Favors high-weight clients")
    print(f"   Revenue objective:    Favors high-tier clients (premium > standard > free)")

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
Multi-resource modeling is essential for realistic rate limiting because:

1. Systems have multiple bottlenecks (CPU, memory, network)
2. Different clients have different resource profiles
3. Single aggregate capacity constraint is too simplistic
4. Multi-dimensional pricing reveals true resource costs
5. Can optimize for throughput OR revenue (different trade-offs)

The VRP connection becomes even clearer:
- VRP: Route feasibility depends on time windows, capacity, driver hours
- Rate Limiter: Request feasibility depends on CPU, memory, network, SLAs

Both require multi-resource optimization!
""")


if __name__ == "__main__":
    main()
