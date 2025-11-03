"""
VRP-Inspired Enhancements for Rate Limiter

This module implements techniques borrowed from Vehicle Routing Problem (VRP)
literature to improve the rate limiter's performance and stability:

1. Warm-starting: Re-use previous solutions (faster solving)
2. Rolling horizon: Multi-period lookahead (price stability)
3. Robust optimization: Capacity buffers (demand uncertainty)
4. Smart re-optimization triggers (efficiency)
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque
from dataclasses import dataclass
import time

from .rate_limiter_core import Client, RateLimiterLP, RateLimiterSolution


@dataclass
class RobustConfig:
    """Configuration for robust optimization"""
    enable_buffer: bool = True
    buffer_percentile: float = 0.95  # Reserve capacity for 95th percentile
    lookback_periods: int = 10  # How many past periods to use for statistics
    min_buffer_rate: float = 0.05  # Minimum 5% buffer


@dataclass
class RollingHorizonConfig:
    """Configuration for rolling horizon optimization"""
    enabled: bool = True
    num_periods: int = 3  # Look ahead 3 periods
    discount_factor: float = 0.8  # Decay weight for future periods
    period_length: float = 10.0  # seconds per period


@dataclass
class TriggerConfig:
    """Configuration for re-optimization triggers"""
    time_threshold: float = 10.0  # Re-solve every 10 seconds
    load_change_threshold: float = 0.20  # Re-solve if load changes > 20%
    price_change_threshold: float = 0.30  # Re-solve if price changes > 30%


class VRPEnhancedRateLimiter:
    """
    Rate limiter with VRP-inspired enhancements.

    This class wraps the basic RateLimiterLP and adds:
    - Warm-starting for faster re-solving
    - Rolling horizon for price stability
    - Robust capacity buffers for uncertainty
    - Intelligent re-optimization triggers
    """

    def __init__(self,
                 capacity: float,
                 robust_config: Optional[RobustConfig] = None,
                 rolling_horizon_config: Optional[RollingHorizonConfig] = None,
                 trigger_config: Optional[TriggerConfig] = None,
                 use_gurobi: bool = True):
        """
        Initialize VRP-enhanced rate limiter.

        Args:
            capacity: Total system capacity (C) in requests/second
            robust_config: Configuration for robust optimization
            rolling_horizon_config: Configuration for rolling horizon
            trigger_config: Configuration for re-optimization triggers
            use_gurobi: Whether to use Gurobi or PuLP
        """
        self.base_capacity = capacity
        self.robust_config = robust_config or RobustConfig()
        self.rolling_horizon_config = rolling_horizon_config or RollingHorizonConfig()
        self.trigger_config = trigger_config or TriggerConfig()

        # Core LP solver
        self.solver = RateLimiterLP(capacity=capacity, use_gurobi=use_gurobi)

        # History tracking for robust optimization
        self.demand_history = deque(maxlen=self.robust_config.lookback_periods)
        self.price_history = deque(maxlen=20)  # Track prices for EMA

        # Trigger state
        self.last_solve_time = 0.0
        self.last_total_demand = 0.0
        self.last_dual_price = 0.0

        # Statistics
        self.triggered_by_time = 0
        self.triggered_by_load = 0
        self.triggered_by_price = 0
        self.skipped_solves = 0

        # Smoothed dual price (exponential moving average)
        self.smoothed_dual_price: Optional[float] = None
        self.ema_alpha = 0.3  # Smoothing factor (0 = no smoothing, 1 = no memory)

    def compute_effective_capacity(self) -> float:
        """
        Compute effective capacity with robust buffer.

        VRP Inspiration: Robust vehicle routing reserves capacity for uncertainty.
        Similarly, we reserve buffer capacity for demand spikes.

        Returns:
            Effective capacity after buffer reservation
        """
        if not self.robust_config.enable_buffer or len(self.demand_history) < 2:
            return self.base_capacity

        # Compute statistics from demand history
        recent_demands = np.array(list(self.demand_history))
        mean_demand = np.mean(recent_demands)
        std_demand = np.std(recent_demands)

        # Buffer based on demand volatility
        # Higher std → larger buffer to handle spikes
        buffer_rate = self.robust_config.min_buffer_rate
        if mean_demand > 0:
            cv = std_demand / mean_demand  # Coefficient of variation
            buffer_rate = max(
                self.robust_config.min_buffer_rate,
                min(0.25, cv * 0.5)  # Cap at 25% buffer
            )

        buffer_capacity = self.base_capacity * buffer_rate
        effective_capacity = self.base_capacity - buffer_capacity

        return max(effective_capacity, self.base_capacity * 0.7)  # At least 70% available

    def should_resolve(self, clients: List[Client], current_time: float) -> Tuple[bool, str]:
        """
        Determine if we should re-solve the LP (intelligent triggers).

        VRP Inspiration: Dynamic VRP uses event-based triggers rather than
        constant re-optimization (expensive).

        Returns:
            (should_resolve, reason)
        """
        # First solve
        if self.last_solve_time == 0:
            return True, "initial"

        # Time-based trigger
        time_since_last = current_time - self.last_solve_time
        if time_since_last >= self.trigger_config.time_threshold:
            self.triggered_by_time += 1
            return True, "time"

        # Load change trigger
        current_demand = sum(c.current_demand for c in clients)
        if self.last_total_demand > 0:
            demand_change = abs(current_demand - self.last_total_demand) / self.last_total_demand
            if demand_change >= self.trigger_config.load_change_threshold:
                self.triggered_by_load += 1
                return True, f"load_change_{demand_change:.1%}"

        # Don't re-solve
        self.skipped_solves += 1
        return False, "cached"

    def solve_with_rolling_horizon(self,
                                   clients: List[Client],
                                   current_time: float,
                                   forecast_demands: Optional[List[List[Client]]] = None,
                                   verbose: bool = False) -> RateLimiterSolution:
        """
        Solve with rolling horizon optimization for price stability.

        VRP Inspiration: Rolling horizon planning considers multiple future periods
        to avoid myopic decisions that cause instability.

        Args:
            clients: Current clients and demands
            current_time: Current timestamp
            forecast_demands: Optional forecasted clients for future periods
            verbose: Whether to print debug info

        Returns:
            Solution for current period
        """
        # Update demand history
        total_demand = sum(c.current_demand for c in clients)
        self.demand_history.append(total_demand)

        # Check if we should re-solve
        should_resolve, reason = self.should_resolve(clients, current_time)

        if not should_resolve and self.solver.previous_solution is not None:
            # Use cached solution
            if verbose:
                print(f"Using cached solution (reason: {reason})")
            return self.solver.previous_solution

        if verbose:
            print(f"Re-solving LP (trigger: {reason})")

        # Update effective capacity with robust buffer
        effective_capacity = self.compute_effective_capacity()
        if effective_capacity != self.solver.capacity:
            self.solver.capacity = effective_capacity
            if verbose:
                print(f"Effective capacity: {effective_capacity:.2f} req/s "
                      f"(buffer: {self.base_capacity - effective_capacity:.2f})")

        # Standard single-period solve
        if not self.rolling_horizon_config.enabled or forecast_demands is None:
            solution = self.solver.solve(
                clients=clients,
                warm_start=True,
                verbose=verbose
            )
        else:
            # Multi-period rolling horizon solve
            solution = self._solve_rolling_horizon(
                current_clients=clients,
                forecast_demands=forecast_demands,
                verbose=verbose
            )

        # Update trigger state
        self.last_solve_time = current_time
        self.last_total_demand = total_demand
        self.last_dual_price = solution.dual_price

        # Smooth dual price using EMA (VRP technique for price stability)
        if self.smoothed_dual_price is None:
            self.smoothed_dual_price = solution.dual_price
        else:
            self.smoothed_dual_price = (
                self.ema_alpha * solution.dual_price +
                (1 - self.ema_alpha) * self.smoothed_dual_price
            )

        self.price_history.append(solution.dual_price)

        # Return solution with smoothed price
        from dataclasses import replace
        smoothed_solution = replace(solution, dual_price=self.smoothed_dual_price)

        return smoothed_solution

    def _solve_rolling_horizon(self,
                               current_clients: List[Client],
                               forecast_demands: List[List[Client]],
                               verbose: bool) -> RateLimiterSolution:
        """
        Solve multi-period problem with rolling horizon.

        The objective becomes:
            max Σ_t γ^t * Σ_i w_i * r_i^t

        where γ is the discount factor and t indexes time periods.

        For simplicity, we approximate this by adjusting weights
        based on forecasted future demand pressure.
        """
        # Compute demand pressure for future periods
        future_pressures = []
        for future_clients in forecast_demands[:self.rolling_horizon_config.num_periods]:
            total_future_demand = sum(c.current_demand for c in future_clients)
            pressure = total_future_demand / self.base_capacity
            future_pressures.append(pressure)

        # If future periods show high pressure, increase weights for current period
        # (ensures we don't under-allocate now and face issues later)
        avg_future_pressure = np.mean(future_pressures) if future_pressures else 1.0

        # Adjust current client weights
        adjusted_clients = []
        for client in current_clients:
            adjusted_weight = client.weight * (1.0 + 0.2 * max(0, avg_future_pressure - 1.0))
            from dataclasses import replace
            adjusted_client = replace(client, weight=adjusted_weight)
            adjusted_clients.append(adjusted_client)

        if verbose:
            print(f"Future demand pressure: {avg_future_pressure:.2f}x capacity")

        # Solve with adjusted weights
        solution = self.solver.solve(
            clients=adjusted_clients,
            warm_start=True,
            verbose=verbose
        )

        return solution

    def get_statistics(self) -> Dict:
        """Get statistics about VRP enhancements"""
        total_triggers = self.triggered_by_time + self.triggered_by_load + self.triggered_by_price
        total_decisions = total_triggers + self.skipped_solves

        stats = {
            'total_solves': self.solver.solve_count,
            'total_decisions': total_decisions,
            'skipped_solves': self.skipped_solves,
            'skip_rate': self.skipped_solves / total_decisions if total_decisions > 0 else 0,
            'triggered_by_time': self.triggered_by_time,
            'triggered_by_load': self.triggered_by_load,
            'triggered_by_price': self.triggered_by_price,
            'current_smoothed_price': self.smoothed_dual_price,
            'price_volatility': np.std(list(self.price_history)) if len(self.price_history) > 1 else 0,
            'demand_history_size': len(self.demand_history),
        }

        return stats


def compare_basic_vs_enhanced():
    """Demo: Compare basic LP vs VRP-enhanced version"""
    print("=" * 70)
    print("Comparison: Basic LP vs VRP-Enhanced Rate Limiter")
    print("=" * 70)

    # Create clients
    from .rate_limiter_core import create_example_clients

    # Basic version
    print("\n--- BASIC LP (No VRP Enhancements) ---")
    basic_limiter = RateLimiterLP(capacity=100.0)

    solve_times_basic = []
    for i in range(5):
        clients = create_example_clients()
        # Vary demand
        for c in clients:
            c.current_demand *= (1.0 + 0.1 * i)

        solution = basic_limiter.solve(clients, warm_start=False, verbose=False)
        solve_times_basic.append(solution.solve_time * 1000)  # ms
        print(f"Iteration {i+1}: π=${solution.dual_price:.4f}, "
              f"solve_time={solution.solve_time*1000:.2f}ms")

    # VRP-enhanced version
    print("\n--- VRP-ENHANCED (Warm Start + Robust + Triggers) ---")
    enhanced_limiter = VRPEnhancedRateLimiter(
        capacity=100.0,
        robust_config=RobustConfig(enable_buffer=True),
        rolling_horizon_config=RollingHorizonConfig(enabled=False),  # Disable for simple demo
        trigger_config=TriggerConfig(
            time_threshold=100.0,  # Don't trigger on time for demo
            load_change_threshold=0.15
        )
    )

    solve_times_enhanced = []
    current_time = 0.0
    for i in range(5):
        clients = create_example_clients()
        for c in clients:
            c.current_demand *= (1.0 + 0.1 * i)

        current_time += 1.0  # Advance time
        solution = enhanced_limiter.solve_with_rolling_horizon(
            clients, current_time, verbose=False
        )
        solve_times_enhanced.append(solution.solve_time * 1000)
        print(f"Iteration {i+1}: π=${solution.dual_price:.4f} "
              f"(smoothed: ${enhanced_limiter.smoothed_dual_price:.4f}), "
              f"solve_time={solution.solve_time*1000:.2f}ms")

    # Statistics
    print("\n--- PERFORMANCE COMPARISON ---")
    print(f"Basic LP:")
    print(f"  Avg solve time: {np.mean(solve_times_basic):.2f}ms")
    print(f"  Total solves: {basic_limiter.solve_count}")

    print(f"\nVRP-Enhanced:")
    print(f"  Avg solve time: {np.mean(solve_times_enhanced):.2f}ms")
    print(f"  Total solves: {enhanced_limiter.solver.solve_count}")
    stats = enhanced_limiter.get_statistics()
    print(f"  Skipped solves: {stats['skipped_solves']} ({stats['skip_rate']:.1%})")
    print(f"  Price volatility: ${stats['price_volatility']:.4f}")

    speedup = np.mean(solve_times_basic) / np.mean(solve_times_enhanced)
    print(f"\nSpeedup: {speedup:.2f}x")


if __name__ == "__main__":
    compare_basic_vs_enhanced()
