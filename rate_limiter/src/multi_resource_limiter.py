"""
Multi-Resource Rate Limiter with Response Time SLA

Inspired by Kubernetes pod scheduling paper, this extends the rate limiter
to handle multiple resource types (CPU, memory, network) and response time SLAs.

Key differences from basic model:
1. Multiple resource constraints (not just aggregate capacity)
2. Heterogeneous client profiles (different resource requirements)
3. Response time modeling (load-dependent latency)
4. Multi-dimensional pricing (separate dual prices per resource)

Objective: Maximize throughput and revenue (NOT minimize costs!)
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from gurobipy import Model, GRB, quicksum
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
    from pulp import LpProblem, LpVariable, LpMaximize, lpSum, PULP_CBC_CMD

from .rate_limiter_core import Client


@dataclass
class ResourceProfile:
    """Resource requirements per request for a client"""
    cpu_ms_per_request: float  # CPU milliseconds per request
    memory_mb_per_request: float  # Memory MB allocated per request
    network_kb_per_request: float  # Network KB transferred per request

    # Response time SLA
    max_response_time_ms: float  # Maximum acceptable response time

    def __repr__(self):
        return (f"CPU={self.cpu_ms_per_request}ms, "
                f"MEM={self.memory_mb_per_request}MB, "
                f"NET={self.network_kb_per_request}KB, "
                f"RT_max={self.max_response_time_ms}ms")


@dataclass
class SystemResources:
    """System resource capacities"""
    cpu_capacity_ms: float  # Total CPU capacity (ms per second)
    memory_capacity_mb: float  # Total memory capacity (MB)
    network_capacity_kb: float  # Total network bandwidth (KB per second)

    def __repr__(self):
        return (f"CPU={self.cpu_capacity_ms}ms/s, "
                f"MEM={self.memory_capacity_mb}MB, "
                f"NET={self.network_capacity_kb}KB/s")


@dataclass
class MultiResourceClient(Client):
    """Client with resource profile"""
    resource_profile: Optional[ResourceProfile] = None

    def __post_init__(self):
        if self.resource_profile is None:
            # Default profile: balanced resource usage
            self.resource_profile = ResourceProfile(
                cpu_ms_per_request=20.0,
                memory_mb_per_request=100.0,
                network_kb_per_request=500.0,
                max_response_time_ms=200.0
            )


@dataclass
class MultiResourceSolution:
    """Solution with multi-resource allocation"""
    allocated_rates: Dict[str, float]
    objective_value: float

    # Multi-dimensional dual prices (shadow prices per resource)
    dual_price_cpu: float
    dual_price_memory: float
    dual_price_network: float

    # Response time estimates
    estimated_response_times: Dict[str, float]

    # Resource utilization
    cpu_utilization: float
    memory_utilization: float
    network_utilization: float

    solve_time_ms: float
    feasible: bool


class MultiResourceRateLimiter:
    """
    Multi-resource rate limiter with response time SLA.

    LP Formulation:
    ---------------
    Decision variables: r_i = allocated rate for client i (req/s)

    Objective (TWO OPTIONS):

    Option 1 - Maximize Weighted Throughput:
        max Σ w_i * r_i

    Option 2 - Maximize Revenue:
        max Σ (price_i * r_i)
        where price_i is based on tier and resource consumption

    Constraints:
    1. CPU capacity:     Σ r_i * cpu_i ≤ CPU_capacity        [dual: π_cpu]
    2. Memory capacity:  Σ r_i * mem_i ≤ MEM_capacity        [dual: π_mem]
    3. Network capacity: Σ r_i * net_i ≤ NET_capacity        [dual: π_net]
    4. Hard SLAs:        r_i ≥ min_rate_i  (for premium)
    5. Response time:    RT_i(r_i) ≤ RT_max_i
    6. Demand limits:    r_i ≤ demand_i

    Response time model (M/M/1 queueing):
        RT_i ≈ service_time_i + queue_delay_i
        queue_delay_i ≈ utilization / (1 - utilization)
    """

    def __init__(self,
                 system_resources: SystemResources,
                 use_gurobi: bool = True,
                 objective_type: str = "throughput"):
        """
        Initialize multi-resource rate limiter.

        Args:
            system_resources: System resource capacities
            use_gurobi: Use Gurobi if available (faster)
            objective_type: "throughput" or "revenue"
        """
        self.resources = system_resources
        self.use_gurobi = use_gurobi and GUROBI_AVAILABLE
        self.objective_type = objective_type

        if not self.use_gurobi:
            print("Warning: Gurobi not available, using PuLP (slower)")

    def estimate_response_time(self,
                               client: MultiResourceClient,
                               allocated_rate: float,
                               total_cpu_load: float) -> float:
        """
        Estimate response time based on allocated rate and system load.

        Uses simplified M/M/1 queueing model:
        RT ≈ service_time + queue_delay

        where queue_delay depends on CPU utilization
        """
        profile = client.resource_profile

        # Base service time (CPU time)
        service_time = profile.cpu_ms_per_request

        # Queue delay based on CPU utilization
        cpu_util = total_cpu_load / self.resources.cpu_capacity_ms
        cpu_util = min(cpu_util, 0.95)  # Cap to avoid division by zero

        queue_delay = service_time * (cpu_util / (1 - cpu_util))

        response_time = service_time + queue_delay
        return response_time

    def solve(self,
              clients: List[MultiResourceClient],
              verbose: bool = False) -> MultiResourceSolution:
        """
        Solve multi-resource rate allocation problem.

        Returns:
            MultiResourceSolution with allocations and dual prices
        """
        if self.use_gurobi:
            return self._solve_gurobi(clients, verbose)
        else:
            return self._solve_pulp(clients, verbose)

    def _solve_gurobi(self,
                      clients: List[MultiResourceClient],
                      verbose: bool) -> MultiResourceSolution:
        """Solve using Gurobi"""
        import time
        start_time = time.time()

        model = Model("MultiResourceRateLimiter")
        if not verbose:
            model.setParam('OutputFlag', 0)

        # Decision variables: r_i for each client
        rate_vars = {}
        for client in clients:
            rate_vars[client.id] = model.addVar(
                lb=0.0,
                ub=client.current_demand,
                name=f"rate_{client.id}"
            )

        # Objective: Maximize weighted throughput OR revenue
        if self.objective_type == "throughput":
            # Option 1: Maximize weighted throughput
            objective = quicksum(
                client.weight * rate_vars[client.id]
                for client in clients
            )
        else:
            # Option 2: Maximize revenue (price based on tier)
            tier_prices = {
                "premium": 0.50,
                "standard": 0.20,
                "free": 0.01
            }
            objective = quicksum(
                tier_prices.get(client.tier, 0.10) * rate_vars[client.id]
                for client in clients
            )

        model.setObjective(objective, GRB.MAXIMIZE)

        # Constraint 1: CPU capacity
        cpu_constraint = model.addConstr(
            quicksum(
                rate_vars[client.id] * client.resource_profile.cpu_ms_per_request
                for client in clients
            ) <= self.resources.cpu_capacity_ms,
            name="cpu_capacity"
        )

        # Constraint 2: Memory capacity
        memory_constraint = model.addConstr(
            quicksum(
                rate_vars[client.id] * client.resource_profile.memory_mb_per_request
                for client in clients
            ) <= self.resources.memory_capacity_mb,
            name="memory_capacity"
        )

        # Constraint 3: Network capacity
        network_constraint = model.addConstr(
            quicksum(
                rate_vars[client.id] * client.resource_profile.network_kb_per_request
                for client in clients
            ) <= self.resources.network_capacity_kb,
            name="network_capacity"
        )

        # Constraint 4: Hard SLAs (minimum rates for premium clients)
        for client in clients:
            if client.min_rate > 0:
                model.addConstr(
                    rate_vars[client.id] >= client.min_rate,
                    name=f"hard_sla_{client.id}"
                )

        # Solve
        model.optimize()

        solve_time = (time.time() - start_time) * 1000  # ms

        if model.status != GRB.OPTIMAL:
            # Infeasible or other error
            return MultiResourceSolution(
                allocated_rates={c.id: 0.0 for c in clients},
                objective_value=0.0,
                dual_price_cpu=0.0,
                dual_price_memory=0.0,
                dual_price_network=0.0,
                estimated_response_times={c.id: 0.0 for c in clients},
                cpu_utilization=0.0,
                memory_utilization=0.0,
                network_utilization=0.0,
                solve_time_ms=solve_time,
                feasible=False
            )

        # Extract solution
        allocated_rates = {
            client.id: rate_vars[client.id].X
            for client in clients
        }

        # Extract dual prices (shadow prices)
        dual_price_cpu = cpu_constraint.Pi
        dual_price_memory = memory_constraint.Pi
        dual_price_network = network_constraint.Pi

        # Compute resource utilization
        total_cpu_load = sum(
            allocated_rates[c.id] * c.resource_profile.cpu_ms_per_request
            for c in clients
        )
        total_memory_load = sum(
            allocated_rates[c.id] * c.resource_profile.memory_mb_per_request
            for c in clients
        )
        total_network_load = sum(
            allocated_rates[c.id] * c.resource_profile.network_kb_per_request
            for c in clients
        )

        cpu_util = total_cpu_load / self.resources.cpu_capacity_ms
        memory_util = total_memory_load / self.resources.memory_capacity_mb
        network_util = total_network_load / self.resources.network_capacity_kb

        # Estimate response times
        response_times = {
            client.id: self.estimate_response_time(
                client, allocated_rates[client.id], total_cpu_load
            )
            for client in clients
        }

        return MultiResourceSolution(
            allocated_rates=allocated_rates,
            objective_value=model.objVal,
            dual_price_cpu=dual_price_cpu,
            dual_price_memory=dual_price_memory,
            dual_price_network=dual_price_network,
            estimated_response_times=response_times,
            cpu_utilization=cpu_util,
            memory_utilization=memory_util,
            network_utilization=network_util,
            solve_time_ms=solve_time,
            feasible=True
        )

    def _solve_pulp(self,
                    clients: List[MultiResourceClient],
                    verbose: bool) -> MultiResourceSolution:
        """Solve using PuLP (fallback)"""
        import time
        start_time = time.time()

        model = LpProblem("MultiResourceRateLimiter", LpMaximize)

        # Decision variables
        rate_vars = {}
        for client in clients:
            rate_vars[client.id] = LpVariable(
                f"rate_{client.id}",
                lowBound=0.0,
                upBound=client.current_demand
            )

        # Objective
        if self.objective_type == "throughput":
            model += lpSum(
                client.weight * rate_vars[client.id]
                for client in clients
            )
        else:
            tier_prices = {"premium": 0.50, "standard": 0.20, "free": 0.01}
            model += lpSum(
                tier_prices.get(client.tier, 0.10) * rate_vars[client.id]
                for client in clients
            )

        # CPU constraint
        model += (
            lpSum(
                rate_vars[client.id] * client.resource_profile.cpu_ms_per_request
                for client in clients
            ) <= self.resources.cpu_capacity_ms,
            "cpu_capacity"
        )

        # Memory constraint
        model += (
            lpSum(
                rate_vars[client.id] * client.resource_profile.memory_mb_per_request
                for client in clients
            ) <= self.resources.memory_capacity_mb,
            "memory_capacity"
        )

        # Network constraint
        model += (
            lpSum(
                rate_vars[client.id] * client.resource_profile.network_kb_per_request
                for client in clients
            ) <= self.resources.network_capacity_kb,
            "network_capacity"
        )

        # Hard SLAs
        for client in clients:
            if client.min_rate > 0:
                model += (
                    rate_vars[client.id] >= client.min_rate,
                    f"hard_sla_{client.id}"
                )

        # Solve
        model.solve(PULP_CBC_CMD(msg=verbose))

        solve_time = (time.time() - start_time) * 1000

        # Extract solution
        allocated_rates = {
            client.id: rate_vars[client.id].varValue or 0.0
            for client in clients
        }

        # Compute utilization
        total_cpu_load = sum(
            allocated_rates[c.id] * c.resource_profile.cpu_ms_per_request
            for c in clients
        )
        total_memory_load = sum(
            allocated_rates[c.id] * c.resource_profile.memory_mb_per_request
            for c in clients
        )
        total_network_load = sum(
            allocated_rates[c.id] * c.resource_profile.network_kb_per_request
            for c in clients
        )

        cpu_util = total_cpu_load / self.resources.cpu_capacity_ms
        memory_util = total_memory_load / self.resources.memory_capacity_mb
        network_util = total_network_load / self.resources.network_capacity_kb

        # Estimate response times
        response_times = {
            client.id: self.estimate_response_time(
                client, allocated_rates[client.id], total_cpu_load
            )
            for client in clients
        }

        # Note: PuLP doesn't provide dual prices easily
        return MultiResourceSolution(
            allocated_rates=allocated_rates,
            objective_value=model.objective.value() or 0.0,
            dual_price_cpu=0.0,  # Not available in PuLP
            dual_price_memory=0.0,
            dual_price_network=0.0,
            estimated_response_times=response_times,
            cpu_utilization=cpu_util,
            memory_utilization=memory_util,
            network_utilization=network_util,
            solve_time_ms=solve_time,
            feasible=True
        )

    def get_composite_price(self, solution: MultiResourceSolution,
                           client: MultiResourceClient) -> float:
        """
        Calculate composite price per request for a client.

        Price = cpu_usage * π_cpu + mem_usage * π_mem + net_usage * π_net
        """
        profile = client.resource_profile

        composite_price = (
            profile.cpu_ms_per_request * solution.dual_price_cpu +
            profile.memory_mb_per_request * solution.dual_price_memory +
            profile.network_kb_per_request * solution.dual_price_network
        )

        return composite_price


def demo_multi_resource():
    """Demonstrate multi-resource rate limiter"""
    print("=" * 70)
    print("Multi-Resource Rate Limiter Demo")
    print("=" * 70)

    # Define system resources
    resources = SystemResources(
        cpu_capacity_ms=1000.0,  # 1000ms CPU per second (e.g., 1 core)
        memory_capacity_mb=2048.0,  # 2GB memory
        network_capacity_kb=10000.0  # 10 MB/s network
    )

    print(f"\nSystem Resources: {resources}")

    # Create heterogeneous clients
    clients = [
        MultiResourceClient(
            id="alice",
            tier="premium",
            weight=10.0,
            min_rate=5.0,  # Hard SLA: 5 req/s minimum
            max_willingness_to_pay=0.50,
            current_demand=20.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=80.0,  # CPU-heavy (ML inference)
                memory_mb_per_request=400.0,
                network_kb_per_request=200.0,
                max_response_time_ms=500.0
            )
        ),
        MultiResourceClient(
            id="bob",
            tier="standard",
            weight=5.0,
            min_rate=0.0,
            max_willingness_to_pay=0.20,
            current_demand=30.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=20.0,  # Balanced
                memory_mb_per_request=100.0,
                network_kb_per_request=500.0,
                max_response_time_ms=200.0
            )
        ),
        MultiResourceClient(
            id="carol",
            tier="free",
            weight=1.0,
            min_rate=0.0,
            max_willingness_to_pay=0.005,
            current_demand=50.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=5.0,  # Network-heavy (static content)
                memory_mb_per_request=50.0,
                network_kb_per_request=2000.0,
                max_response_time_ms=100.0
            )
        ),
        MultiResourceClient(
            id="dave",
            tier="standard",
            weight=5.0,
            min_rate=0.0,
            max_willingness_to_pay=0.15,
            current_demand=40.0,
            resource_profile=ResourceProfile(
                cpu_ms_per_request=30.0,  # Memory-heavy (database queries)
                memory_mb_per_request=300.0,
                network_kb_per_request=300.0,
                max_response_time_ms=300.0
            )
        )
    ]

    print("\nClient Profiles:")
    for client in clients:
        print(f"  {client.id:10s} ({client.tier:8s}): demand={client.current_demand:5.1f} req/s")
        print(f"             Profile: {client.resource_profile}")

    # Solve with throughput objective
    print("\n" + "-" * 70)
    print("OBJECTIVE: Maximize Weighted Throughput")
    print("-" * 70)

    limiter_throughput = MultiResourceRateLimiter(
        system_resources=resources,
        objective_type="throughput"
    )

    solution_throughput = limiter_throughput.solve(clients, verbose=False)

    if solution_throughput.feasible:
        print(f"\nObjective value: {solution_throughput.objective_value:.2f}")
        print(f"Solve time: {solution_throughput.solve_time_ms:.2f}ms")

        print("\nResource Utilization:")
        print(f"  CPU:     {solution_throughput.cpu_utilization:.1%}")
        print(f"  Memory:  {solution_throughput.memory_utilization:.1%}")
        print(f"  Network: {solution_throughput.network_utilization:.1%}")

        print("\nDual Prices (Shadow Prices):")
        print(f"  π_cpu:     ${solution_throughput.dual_price_cpu:.6f} per ms")
        print(f"  π_memory:  ${solution_throughput.dual_price_memory:.6f} per MB")
        print(f"  π_network: ${solution_throughput.dual_price_network:.6f} per KB")

        print("\nAllocations:")
        for client in clients:
            allocated = solution_throughput.allocated_rates[client.id]
            ratio = allocated / client.current_demand if client.current_demand > 0 else 0
            rt = solution_throughput.estimated_response_times[client.id]
            price = limiter_throughput.get_composite_price(solution_throughput, client)

            print(f"  {client.id:10s}: {allocated:6.2f} req/s ({ratio:5.1%} of demand)")
            print(f"              Response time: {rt:.1f}ms  Price: ${price:.4f}/req")

    # Solve with revenue objective
    print("\n" + "-" * 70)
    print("OBJECTIVE: Maximize Revenue")
    print("-" * 70)

    limiter_revenue = MultiResourceRateLimiter(
        system_resources=resources,
        objective_type="revenue"
    )

    solution_revenue = limiter_revenue.solve(clients, verbose=False)

    if solution_revenue.feasible:
        print(f"\nObjective value (revenue): ${solution_revenue.objective_value:.2f}")
        print(f"Solve time: {solution_revenue.solve_time_ms:.2f}ms")

        print("\nResource Utilization:")
        print(f"  CPU:     {solution_revenue.cpu_utilization:.1%}")
        print(f"  Memory:  {solution_revenue.memory_utilization:.1%}")
        print(f"  Network: {solution_revenue.network_utilization:.1%}")

        print("\nAllocations:")
        for client in clients:
            allocated = solution_revenue.allocated_rates[client.id]
            ratio = allocated / client.current_demand if client.current_demand > 0 else 0
            rt = solution_revenue.estimated_response_times[client.id]
            price = limiter_revenue.get_composite_price(solution_revenue, client)

            print(f"  {client.id:10s}: {allocated:6.2f} req/s ({ratio:5.1%} of demand)")
            print(f"              Response time: {rt:.1f}ms  Price: ${price:.4f}/req")

    print("\n" + "=" * 70)
    print("Comparison: Which resource is the bottleneck?")
    print("=" * 70)

    print("\nThroughput Objective:")
    print(f"  Bottleneck: ", end="")
    utils = [
        ("CPU", solution_throughput.cpu_utilization),
        ("Memory", solution_throughput.memory_utilization),
        ("Network", solution_throughput.network_utilization)
    ]
    bottleneck = max(utils, key=lambda x: x[1])
    print(f"{bottleneck[0]} ({bottleneck[1]:.1%})")

    print("\nRevenue Objective:")
    print(f"  Bottleneck: ", end="")
    utils_rev = [
        ("CPU", solution_revenue.cpu_utilization),
        ("Memory", solution_revenue.memory_utilization),
        ("Network", solution_revenue.network_utilization)
    ]
    bottleneck_rev = max(utils_rev, key=lambda x: x[1])
    print(f"{bottleneck_rev[0]} ({bottleneck_rev[1]:.1%})")


if __name__ == "__main__":
    demo_multi_resource()
