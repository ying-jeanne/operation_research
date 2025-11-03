"""
Core Rate Limiter Implementation using Linear Programming

This module implements the base LP formulation for dynamic rate limiting:
    max Σ w_i * r_i          (weighted throughput)
    s.t. Σ r_i ≤ C           (capacity constraint)
         r_i ≥ R_i^min       (hard SLA for premium clients)
         r_i ≥ 0

The dual variable (π) from the capacity constraint represents the
shadow price (congestion price) per request.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import time

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
    print("Warning: Gurobi not available. Falling back to PuLP.")
    from pulp import *


@dataclass
class Client:
    """Represents an API client with their configuration"""
    id: str
    tier: str  # 'premium', 'standard', 'free'
    weight: float  # Priority weight in objective (w_i)
    min_rate: float  # Hard SLA guarantee (R_i^min), 0 for non-premium
    max_willingness_to_pay: float  # Maximum price willing to pay per request
    current_demand: float  # Current request rate demand


@dataclass
class RateLimiterSolution:
    """Solution from the LP solver"""
    allocated_rates: Dict[str, float]  # client_id -> r_i*
    dual_price: float  # π (shadow price of capacity)
    objective_value: float  # Optimal weighted throughput
    solve_time: float  # Time to solve LP (seconds)
    solver_status: str  # 'optimal', 'infeasible', etc.
    hard_sla_duals: Dict[str, float]  # client_id -> dual of SLA constraint


class RateLimiterLP:
    """
    Core LP-based rate limiter.

    This class formulates and solves the resource allocation problem
    to determine optimal rate allocations and dual-based pricing.
    """

    def __init__(self, capacity: float, use_gurobi: bool = True):
        """
        Initialize rate limiter.

        Args:
            capacity: Total system capacity (C) in requests/second
            use_gurobi: Whether to use Gurobi (True) or PuLP (False)
        """
        self.capacity = capacity
        self.use_gurobi = use_gurobi and GUROBI_AVAILABLE

        # Cache for warm-starting
        self.previous_solution: Optional[RateLimiterSolution] = None
        self.solve_count = 0

    def solve(self,
              clients: List[Client],
              warm_start: bool = False,
              verbose: bool = False) -> RateLimiterSolution:
        """
        Solve the rate allocation LP problem.

        Args:
            clients: List of clients requesting service
            warm_start: Whether to use previous solution as starting point
            verbose: Whether to print solver output

        Returns:
            RateLimiterSolution with allocations and dual prices
        """
        if self.use_gurobi:
            return self._solve_gurobi(clients, warm_start, verbose)
        else:
            return self._solve_pulp(clients, verbose)

    def _solve_gurobi(self,
                      clients: List[Client],
                      warm_start: bool,
                      verbose: bool) -> RateLimiterSolution:
        """Solve using Gurobi"""
        start_time = time.time()

        # Create model
        model = gp.Model("RateLimiter")
        model.setParam('LogToConsole', 1 if verbose else 0)
        model.setParam('OutputFlag', 1 if verbose else 0)

        # Decision variables: r_i for each client
        r = {}
        for client in clients:
            r[client.id] = model.addVar(
                lb=0.0,
                name=f"r_{client.id}",
                vtype=GRB.CONTINUOUS
            )

        # Warm start if previous solution available
        if warm_start and self.previous_solution is not None:
            for client_id, var in r.items():
                if client_id in self.previous_solution.allocated_rates:
                    var.Start = self.previous_solution.allocated_rates[client_id]

        model.update()

        # Objective: maximize weighted throughput
        objective = gp.quicksum(client.weight * r[client.id] for client in clients)
        model.setObjective(objective, GRB.MAXIMIZE)

        # Capacity constraint (this is where we get dual price π)
        capacity_constr = model.addConstr(
            gp.quicksum(r[client.id] for client in clients) <= self.capacity,
            name="capacity"
        )

        # Hard SLA constraints for premium clients
        sla_constrs = {}
        for client in clients:
            if client.min_rate > 0:  # Has hard SLA
                sla_constrs[client.id] = model.addConstr(
                    r[client.id] >= client.min_rate,
                    name=f"sla_{client.id}"
                )

        # Solve
        model.optimize()

        solve_time = time.time() - start_time
        self.solve_count += 1

        # Extract solution
        if model.status == GRB.OPTIMAL:
            allocated_rates = {client.id: r[client.id].X for client in clients}
            dual_price = capacity_constr.Pi  # Shadow price of capacity
            objective_value = model.objVal

            # Extract SLA constraint duals
            hard_sla_duals = {}
            for client_id, constr in sla_constrs.items():
                hard_sla_duals[client_id] = constr.Pi

            solution = RateLimiterSolution(
                allocated_rates=allocated_rates,
                dual_price=dual_price,
                objective_value=objective_value,
                solve_time=solve_time,
                solver_status='optimal',
                hard_sla_duals=hard_sla_duals
            )

            # Cache for warm-starting
            self.previous_solution = solution

            return solution
        else:
            # Handle infeasible or other status
            return RateLimiterSolution(
                allocated_rates={},
                dual_price=0.0,
                objective_value=0.0,
                solve_time=solve_time,
                solver_status='infeasible' if model.status == GRB.INFEASIBLE else 'error',
                hard_sla_duals={}
            )

    def _solve_pulp(self, clients: List[Client], verbose: bool) -> RateLimiterSolution:
        """Solve using PuLP (open-source alternative)"""
        start_time = time.time()

        # Create problem
        prob = LpProblem("RateLimiter", LpMaximize)

        # Decision variables
        r = {client.id: LpVariable(f"r_{client.id}", lowBound=0)
             for client in clients}

        # Objective
        prob += lpSum([client.weight * r[client.id] for client in clients])

        # Capacity constraint
        prob += lpSum([r[client.id] for client in clients]) <= self.capacity, "capacity"

        # Hard SLA constraints
        for client in clients:
            if client.min_rate > 0:
                prob += r[client.id] >= client.min_rate, f"sla_{client.id}"

        # Solve (uses CBC by default, which is free)
        prob.solve(PULP_CBC_CMD(msg=verbose))

        solve_time = time.time() - start_time
        self.solve_count += 1

        # Extract solution
        if prob.status == LpStatusOptimal:
            allocated_rates = {client_id: var.varValue for client_id, var in r.items()}

            # Extract dual price from capacity constraint
            # Note: PuLP doesn't always provide duals reliably, use approximation
            capacity_constraint = prob.constraints['capacity']
            dual_price = -capacity_constraint.pi if capacity_constraint.pi is not None else 0.0

            # If dual not available, approximate using objective sensitivity
            if dual_price == 0.0:
                # Marginal value approximation
                total_allocated = sum(allocated_rates.values())
                if total_allocated >= self.capacity * 0.99:  # Near capacity
                    # Estimate shadow price from weights
                    dual_price = np.mean([c.weight for c in clients])

            solution = RateLimiterSolution(
                allocated_rates=allocated_rates,
                dual_price=dual_price,
                objective_value=value(prob.objective),
                solve_time=solve_time,
                solver_status='optimal',
                hard_sla_duals={}  # PuLP doesn't reliably provide all duals
            )

            self.previous_solution = solution
            return solution
        else:
            return RateLimiterSolution(
                allocated_rates={},
                dual_price=0.0,
                objective_value=0.0,
                solve_time=solve_time,
                solver_status='infeasible',
                hard_sla_duals={}
            )

    def check_feasibility(self, clients: List[Client]) -> Tuple[bool, Optional[str]]:
        """
        Check if the problem is feasible before solving.

        Returns:
            (is_feasible, error_message)
        """
        # Check if hard SLAs can be satisfied
        total_min_rate = sum(c.min_rate for c in clients)

        if total_min_rate > self.capacity:
            return False, (f"Infeasible: Hard SLA requirements ({total_min_rate:.2f} req/s) "
                          f"exceed capacity ({self.capacity:.2f} req/s)")

        return True, None

    def reset_cache(self):
        """Clear warm-start cache"""
        self.previous_solution = None
        self.solve_count = 0


def create_example_clients() -> List[Client]:
    """Create example clients for testing"""
    clients = [
        Client(
            id="alice",
            tier="premium",
            weight=10.0,
            min_rate=30.0,  # Guaranteed 30 req/s
            max_willingness_to_pay=0.50,
            current_demand=50.0
        ),
        Client(
            id="bob",
            tier="standard",
            weight=5.0,
            min_rate=0.0,  # No guarantee
            max_willingness_to_pay=0.20,
            current_demand=40.0
        ),
        Client(
            id="carol",
            tier="free",
            weight=1.0,
            min_rate=0.0,
            max_willingness_to_pay=0.0,
            current_demand=30.0
        )
    ]
    return clients


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("Dynamic Rate Limiter - Core LP Implementation")
    print("=" * 60)

    # Create rate limiter with 100 req/s capacity
    limiter = RateLimiterLP(capacity=100.0, use_gurobi=True)

    # Scenario 1: Low load
    print("\n--- Scenario 1: Low Load (60 req/s demand) ---")
    clients = create_example_clients()
    for c in clients:
        c.current_demand *= 0.5  # Reduce demand

    feasible, msg = limiter.check_feasibility(clients)
    print(f"Feasibility check: {feasible}")

    solution = limiter.solve(clients, verbose=False)
    print(f"\nStatus: {solution.solver_status}")
    print(f"Dual price (π): ${solution.dual_price:.4f}/request")
    print(f"Objective value: {solution.objective_value:.2f}")
    print(f"Solve time: {solution.solve_time*1000:.2f}ms")
    print("\nAllocated rates:")
    for client_id, rate in solution.allocated_rates.items():
        client = next(c for c in clients if c.id == client_id)
        print(f"  {client_id:10s} ({client.tier:8s}): {rate:6.2f} req/s "
              f"(demand: {client.current_demand:.2f}, min: {client.min_rate:.2f})")

    # Scenario 2: High load
    print("\n--- Scenario 2: High Load (150 req/s demand) ---")
    clients = create_example_clients()
    for c in clients:
        c.current_demand *= 1.25  # Increase demand

    solution = limiter.solve(clients, warm_start=True, verbose=False)
    print(f"\nStatus: {solution.solver_status}")
    print(f"Dual price (π): ${solution.dual_price:.4f}/request")
    print(f"Objective value: {solution.objective_value:.2f}")
    print(f"Solve time: {solution.solve_time*1000:.2f}ms (with warm start)")
    print("\nAllocated rates:")
    total_allocated = 0
    for client_id, rate in solution.allocated_rates.items():
        client = next(c for c in clients if c.id == client_id)
        total_allocated += rate
        accept_decision = "✓ Accept" if client.max_willingness_to_pay >= solution.dual_price else "✗ Reject excess"
        print(f"  {client_id:10s} ({client.tier:8s}): {rate:6.2f} req/s "
              f"(willing to pay: ${client.max_willingness_to_pay:.2f}) {accept_decision}")
    print(f"\nTotal allocated: {total_allocated:.2f}/{limiter.capacity:.2f} req/s "
          f"({total_allocated/limiter.capacity*100:.1f}% utilization)")

    print(f"\nTotal solves: {limiter.solve_count}")
