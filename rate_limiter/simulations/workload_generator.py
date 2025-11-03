"""
Workload Generator for Rate Limiter Simulations

Generates realistic API request patterns:
1. Steady load
2. Bursty traffic (sudden spikes)
3. Gradual ramp-up
4. Periodic patterns (daily cycles)
5. Random walk
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rate_limiter_core import Client


@dataclass
class WorkloadConfig:
    """Configuration for workload generation"""
    duration_seconds: float = 300.0  # 5 minutes
    time_step: float = 10.0  # Solve every 10 seconds
    base_capacity: float = 100.0  # System capacity
    pattern: str = "steady"  # 'steady', 'bursty', 'ramp', 'periodic', 'random_walk'
    noise_level: float = 0.1  # Random noise (0 to 1)


class WorkloadGenerator:
    """
    Generate synthetic workloads for testing rate limiters.

    VRP Connection: Similar to generating customer arrival patterns
    for dynamic vehicle routing simulations.
    """

    def __init__(self, config: WorkloadConfig):
        self.config = config
        self.num_steps = int(config.duration_seconds / config.time_step)
        np.random.seed(42)  # Reproducible

    def generate_client_demands(self) -> Dict[str, List[Client]]:
        """
        Generate time series of client demands.

        Returns:
            Dictionary mapping time_step -> List[Client]
        """
        # Define client templates
        client_templates = [
            {
                "id": "alice",
                "tier": "premium",
                "weight": 10.0,
                "min_rate": 30.0,
                "max_willingness_to_pay": 0.50  # Premium tier - willing to pay high
            },
            {
                "id": "bob",
                "tier": "standard",
                "weight": 5.0,
                "min_rate": 0.0,
                "max_willingness_to_pay": 0.20  # Standard tier - moderate
            },
            {
                "id": "carol",
                "tier": "free",
                "weight": 1.0,
                "min_rate": 0.0,
                "max_willingness_to_pay": 0.005  # Free tier - below min price threshold
            },
            {
                "id": "dave",
                "tier": "standard",
                "weight": 5.0,
                "min_rate": 0.0,
                "max_willingness_to_pay": 0.15  # Standard tier - moderate
            }
        ]

        # Generate demand patterns based on config
        if self.config.pattern == "steady":
            demand_multipliers = self._generate_steady()
        elif self.config.pattern == "bursty":
            demand_multipliers = self._generate_bursty()
        elif self.config.pattern == "ramp":
            demand_multipliers = self._generate_ramp()
        elif self.config.pattern == "periodic":
            demand_multipliers = self._generate_periodic()
        elif self.config.pattern == "random_walk":
            demand_multipliers = self._generate_random_walk()
        else:
            raise ValueError(f"Unknown pattern: {self.config.pattern}")

        # Create client objects for each time step
        workload = {}
        for step in range(self.num_steps):
            timestamp = step * self.config.time_step
            clients = []

            for template in client_templates:
                # Base demand (different for each client)
                # Increased to create congestion: total = 180 req/s vs 100 capacity
                if template["id"] == "alice":
                    base_demand = 55.0  # Was 40.0
                elif template["id"] == "bob":
                    base_demand = 45.0  # Was 30.0
                elif template["id"] == "carol":
                    base_demand = 40.0  # Was 20.0
                else:  # dave
                    base_demand = 40.0  # Was 25.0

                # Apply pattern multiplier
                demand = base_demand * demand_multipliers[step]

                # Add noise
                noise = 1.0 + np.random.normal(0, self.config.noise_level)
                demand *= max(0.1, noise)  # Ensure positive

                client = Client(
                    id=template["id"],
                    tier=template["tier"],
                    weight=template["weight"],
                    min_rate=template["min_rate"],
                    max_willingness_to_pay=template["max_willingness_to_pay"],
                    current_demand=demand
                )
                clients.append(client)

            workload[timestamp] = clients

        return workload

    def _generate_steady(self) -> np.ndarray:
        """Steady load at 80% capacity"""
        return np.ones(self.num_steps) * 0.8

    def _generate_bursty(self) -> np.ndarray:
        """Bursty traffic with sudden spikes"""
        multipliers = np.ones(self.num_steps) * 0.5  # Base load

        # Add 3-5 random spikes
        num_spikes = np.random.randint(3, 6)
        spike_positions = np.random.choice(self.num_steps, num_spikes, replace=False)

        for pos in spike_positions:
            # Spike lasting 2-4 steps
            spike_duration = np.random.randint(2, 5)
            spike_magnitude = np.random.uniform(1.5, 2.5)

            for i in range(spike_duration):
                if pos + i < self.num_steps:
                    multipliers[pos + i] = spike_magnitude

        return multipliers

    def _generate_ramp(self) -> np.ndarray:
        """Gradual ramp-up from low to high load"""
        return np.linspace(0.3, 1.8, self.num_steps)

    def _generate_periodic(self) -> np.ndarray:
        """Periodic pattern (simulating daily cycles)"""
        t = np.linspace(0, 2 * np.pi, self.num_steps)
        # Sine wave: 0.5 to 1.5 multiplier
        return 1.0 + 0.5 * np.sin(t)

    def _generate_random_walk(self) -> np.ndarray:
        """Random walk demand pattern"""
        multipliers = np.zeros(self.num_steps)
        multipliers[0] = 1.0

        for i in range(1, self.num_steps):
            change = np.random.normal(0, 0.1)
            multipliers[i] = np.clip(multipliers[i-1] + change, 0.2, 2.0)

        return multipliers

    def compute_statistics(self, workload: Dict[str, List[Client]]) -> Dict:
        """Compute statistics about the generated workload"""
        total_demands = []
        premium_demands = []

        for clients in workload.values():
            total_demand = sum(c.current_demand for c in clients)
            premium_demand = sum(c.current_demand for c in clients if c.tier == "premium")
            total_demands.append(total_demand)
            premium_demands.append(premium_demand)

        total_demands = np.array(total_demands)
        premium_demands = np.array(premium_demands)

        return {
            'num_steps': len(workload),
            'duration': self.config.duration_seconds,
            'pattern': self.config.pattern,
            'total_demand_mean': np.mean(total_demands),
            'total_demand_std': np.std(total_demands),
            'total_demand_min': np.min(total_demands),
            'total_demand_max': np.max(total_demands),
            'capacity': self.config.base_capacity,
            'avg_utilization': np.mean(total_demands) / self.config.base_capacity,
            'peak_utilization': np.max(total_demands) / self.config.base_capacity,
            'premium_demand_mean': np.mean(premium_demands),
            'hard_sla_feasible': np.min(premium_demands) <= self.config.base_capacity
        }


def visualize_workload(workload: Dict[str, List[Client]], config: WorkloadConfig):
    """Visualize the generated workload (requires matplotlib)"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available for visualization")
        return

    timestamps = sorted(workload.keys())
    total_demands = []
    client_demands = {client.id: [] for client in workload[timestamps[0]]}

    for ts in timestamps:
        clients = workload[ts]
        total_demands.append(sum(c.current_demand for c in clients))
        for client in clients:
            client_demands[client.id].append(client.current_demand)

    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Total demand
    ax1.plot(timestamps, total_demands, 'b-', linewidth=2, label='Total Demand')
    ax1.axhline(y=config.base_capacity, color='r', linestyle='--', label='Capacity')
    ax1.fill_between(timestamps, 0, total_demands, alpha=0.3)
    ax1.set_ylabel('Demand (req/s)', fontsize=12)
    ax1.set_title(f'Workload Pattern: {config.pattern.upper()}', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Per-client demands
    for client_id, demands in client_demands.items():
        ax2.plot(timestamps, demands, marker='o', markersize=3, label=client_id)

    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_ylabel('Demand (req/s)', fontsize=12)
    ax2.set_title('Per-Client Demand', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'../results/figures/workload_{config.pattern}.png', dpi=150)
    print(f"Saved figure to results/figures/workload_{config.pattern}.png")
    plt.show()


if __name__ == "__main__":
    print("=" * 70)
    print("Workload Generator Demo")
    print("=" * 70)

    # Test all patterns
    patterns = ["steady", "bursty", "ramp", "periodic", "random_walk"]

    for pattern in patterns:
        print(f"\n--- Pattern: {pattern.upper()} ---")

        config = WorkloadConfig(
            duration_seconds=300.0,
            time_step=10.0,
            base_capacity=100.0,
            pattern=pattern,
            noise_level=0.1
        )

        generator = WorkloadGenerator(config)
        workload = generator.generate_client_demands()

        # Print statistics
        stats = generator.compute_statistics(workload)
        print(f"Number of steps: {stats['num_steps']}")
        print(f"Average total demand: {stats['total_demand_mean']:.2f} req/s")
        print(f"Demand range: [{stats['total_demand_min']:.2f}, {stats['total_demand_max']:.2f}]")
        print(f"Average utilization: {stats['avg_utilization']:.1%}")
        print(f"Peak utilization: {stats['peak_utilization']:.1%}")
        print(f"Hard SLA feasible: {stats['hard_sla_feasible']}")

        # Show first 3 time steps
        print("\nFirst 3 time steps:")
        for i, (ts, clients) in enumerate(list(workload.items())[:3]):
            print(f"  t={ts:6.1f}s: ", end="")
            for c in clients:
                print(f"{c.id}={c.current_demand:5.1f} ", end="")
            print()

        # Visualize (comment out if matplotlib not available)
        # visualize_workload(workload, config)

    print("\nWorkload generation complete!")
