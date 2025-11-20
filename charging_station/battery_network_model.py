"""
Battery Swapping Network Optimization Model
Based on the paper: "Swap-locally, Charge-centrally" framework

This model optimizes:
1. Total battery stock levels
2. Charging capacity at central hub
3. Replenishment policy for swapping stations
4. Cost minimization vs service level
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SwappingStation:
    """Represents a battery swapping station"""
    station_id: int
    demand_rate: float  # swaps per hour (μi)
    demand_std: float   # standard deviation of demand (σi)
    transport_time: float  # hours from central hub to station (TTi)


@dataclass
class SystemParameters:
    """Central hub and system-wide parameters"""
    charging_time: float  # hours (TC)
    battery_cost: float  # USD per battery
    charging_port_cost: float  # USD per charging port
    electricity_cost: float  # USD per kWh
    battery_capacity: float  # kWh
    charging_power: float  # kW per port
    service_level_central: float  # probability (εC)
    service_level_station: float  # probability (εS)


class BatteryNetworkModel:
    """
    Optimization model for battery swapping network
    Based on Result 8 from the paper
    """

    def __init__(self, stations: List[SwappingStation], params: SystemParameters):
        self.stations = stations
        self.params = params
        self.n_stations = len(stations)

    def calculate_variance_function(self, Q: float, Delta: float, mu: float, sigma: float) -> float:
        """
        Equation (5) from paper: Variance function φ(Q)

        φ(Q) = {
            Δσ² + (Q²-1)/6,     if 0 ≤ Q ≤ ν
            QΔμ - (Δμ)²,        if Q ≥ ν
        }
        """
        nu = Delta * mu  # ν = Δμ

        if Q <= nu:
            return Delta * sigma**2 + (Q**2 - 1) / 6
        else:
            return Q * Delta * mu - (Delta * mu)**2

    def calculate_min_battery_stock(self, r: np.ndarray, Q: np.ndarray, R: float) -> float:
        """
        Result 8: Minimum total battery stock requirement

        R + Σ(ri + Qi) ≥ Σ[(TC + 2TTi)μi - 1 + Qi]
                          + Φ^(-1)(1-εC)√[Σφi(Qi)]
                          + ΣΦ^(-1)(1-εS)√(TTi)σi
        """
        TC = self.params.charging_time
        epsilon_C = self.params.service_level_central
        epsilon_S = self.params.service_level_station

        # Left side: total stock
        total_stock = R + sum(r[i] + Q[i] for i in range(self.n_stations))

        # Right side - three terms:
        # Term 1: Base requirement for each station
        term1 = sum(
            (TC + 2 * self.stations[i].transport_time) * self.stations[i].demand_rate - 1 + Q[i]
            for i in range(self.n_stations)
        )

        # Term 2: Safety stock at central hub
        sum_variance = sum(
            self.calculate_variance_function(
                Q[i],
                TC + self.stations[i].transport_time,
                self.stations[i].demand_rate,
                self.stations[i].demand_std
            )
            for i in range(self.n_stations)
        )
        term2 = norm.ppf(1 - epsilon_C) * np.sqrt(sum_variance)

        # Term 3: Safety stock at stations
        term3 = sum(
            norm.ppf(1 - epsilon_S) * np.sqrt(self.stations[i].transport_time) * self.stations[i].demand_std
            for i in range(self.n_stations)
        )

        min_required = term1 + term2 + term3

        return total_stock, min_required

    def calculate_total_cost(self, R: float, r: np.ndarray, Q: np.ndarray) -> float:
        """
        Total cost = Battery investment + Charging infrastructure + Operating costs
        """
        # Total batteries needed
        total_batteries = R + sum(r[i] + Q[i] for i in range(self.n_stations))
        battery_investment = total_batteries * self.params.battery_cost

        # Charging ports needed at central hub
        # Based on: ports = batteries_charging = (TC + avg_TT) * total_demand
        avg_TT = np.mean([s.transport_time for s in self.stations])
        total_demand = sum(s.demand_rate for s in self.stations)
        charging_ports = int(np.ceil((self.params.charging_time + avg_TT) * total_demand))
        charging_investment = charging_ports * self.params.charging_port_cost

        # Transportation cost (proportional to order quantities and frequencies)
        # More frequent deliveries (smaller Q) = higher transport cost
        transport_cost_factor = 50  # USD per delivery trip
        annual_deliveries = sum(
            (self.stations[i].demand_rate * 24 * 365) / Q[i]
            for i in range(self.n_stations)
        )
        annual_transport_cost = annual_deliveries * transport_cost_factor

        # Electricity cost
        annual_energy = total_demand * 24 * 365 * self.params.battery_capacity
        annual_electricity_cost = annual_energy * self.params.electricity_cost

        # Total annual operating cost
        annual_operating = annual_transport_cost + annual_electricity_cost

        # Convert to total cost (battery investment + 3-year operating cost NPV)
        discount_rate = 0.1
        operating_cost_npv = sum(
            annual_operating / (1 + discount_rate)**year
            for year in range(1, 4)
        )

        total_cost = battery_investment + charging_investment + operating_cost_npv

        return total_cost

    def optimize_network(self) -> dict:
        """
        Optimize the battery network configuration

        Decision variables:
        - R: Battery stock at central hub
        - ri: Reorder point for station i
        - Qi: Order quantity for station i

        Objective: Minimize total cost
        Constraint: Meet Result 8 minimum stock requirement
        """
        # Initial guess
        # R ≈ batteries needed for charging + safety stock
        total_demand = sum(s.demand_rate for s in self.stations)
        R_init = self.params.charging_time * total_demand * 1.2

        # ri ≈ demand during transport time
        r_init = np.array([
            s.transport_time * s.demand_rate
            for s in self.stations
        ])

        # Qi ≈ square root rule from EOQ
        Q_init = np.array([
            np.sqrt(2 * s.demand_rate * 24 * 365 * 50 / (self.params.battery_cost * 0.2))
            for s in self.stations
        ])

        # Combine into single vector
        x0 = np.concatenate([[R_init], r_init, Q_init])

        def objective(x):
            R = x[0]
            r = x[1:self.n_stations+1]
            Q = x[self.n_stations+1:]
            return self.calculate_total_cost(R, r, Q)

        def constraint_min_stock(x):
            """Stock must meet minimum requirement"""
            R = x[0]
            r = x[1:self.n_stations+1]
            Q = x[self.n_stations+1:]
            total_stock, min_required = self.calculate_min_battery_stock(r, Q, R)
            return total_stock - min_required  # Must be >= 0

        # Bounds: all variables must be positive
        bounds = [(1, None)] * len(x0)

        # Constraints
        constraints = [
            {'type': 'ineq', 'fun': constraint_min_stock}
        ]

        # Solve optimization
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if not result.success:
            print(f"Warning: Optimization did not converge. Message: {result.message}")

        # Extract results
        R_opt = result.x[0]
        r_opt = result.x[1:self.n_stations+1]
        Q_opt = result.x[self.n_stations+1:]

        # Calculate final metrics
        total_batteries = R_opt + sum(r_opt[i] + Q_opt[i] for i in range(self.n_stations))
        total_demand = sum(s.demand_rate for s in self.stations)
        avg_TT = np.mean([s.transport_time for s in self.stations])
        charging_ports = int(np.ceil((self.params.charging_time + avg_TT) * total_demand))

        return {
            'success': result.success,
            'R_central_hub': R_opt,
            'r_reorder_points': r_opt,
            'Q_order_quantities': Q_opt,
            'total_batteries': total_batteries,
            'charging_ports_needed': charging_ports,
            'total_cost': result.fun,
            'cost_breakdown': self._calculate_cost_breakdown(R_opt, r_opt, Q_opt),
            'optimization_result': result
        }

    def _calculate_cost_breakdown(self, R: float, r: np.ndarray, Q: np.ndarray) -> dict:
        """Detailed cost breakdown"""
        total_batteries = R + sum(r[i] + Q[i] for i in range(self.n_stations))
        battery_investment = total_batteries * self.params.battery_cost

        avg_TT = np.mean([s.transport_time for s in self.stations])
        total_demand = sum(s.demand_rate for s in self.stations)
        charging_ports = int(np.ceil((self.params.charging_time + avg_TT) * total_demand))
        charging_investment = charging_ports * self.params.charging_port_cost

        transport_cost_factor = 50
        annual_deliveries = sum(
            (self.stations[i].demand_rate * 24 * 365) / Q[i]
            for i in range(self.n_stations)
        )
        annual_transport = annual_deliveries * transport_cost_factor

        annual_energy = total_demand * 24 * 365 * self.params.battery_capacity
        annual_electricity = annual_energy * self.params.electricity_cost

        return {
            'battery_investment': battery_investment,
            'charging_infrastructure': charging_investment,
            'annual_transport': annual_transport,
            'annual_electricity': annual_electricity,
            'total_batteries': total_batteries,
            'charging_ports': charging_ports
        }

    def simulate_current_setup(self, current_batteries: int, current_ports: int) -> dict:
        """
        Evaluate your current setup against the paper's framework
        """
        # Current stock levels
        total_demand = sum(s.demand_rate for s in self.stations)

        # Assume evenly distributed across stations
        batteries_per_station = (current_batteries - current_ports) / self.n_stations

        # Estimate current (r, Q) policy
        r_current = np.array([batteries_per_station * 0.3 for _ in range(self.n_stations)])
        Q_current = np.array([batteries_per_station * 0.7 for _ in range(self.n_stations)])
        R_current = current_ports

        # Check if meets minimum requirement
        total_stock, min_required = self.calculate_min_battery_stock(r_current, Q_current, R_current)

        meets_requirement = total_stock >= min_required
        surplus = total_stock - min_required

        # Calculate current costs
        current_cost = self.calculate_total_cost(R_current, r_current, Q_current)

        return {
            'current_total_batteries': current_batteries,
            'current_charging_ports': current_ports,
            'min_required_batteries': min_required,
            'meets_paper_requirement': meets_requirement,
            'surplus_batteries': surplus,
            'surplus_percentage': (surplus / min_required) * 100,
            'current_total_cost': current_cost,
            'estimated_r': r_current,
            'estimated_Q': Q_current
        }


def create_muhanga_model():
    """
    Create model for your Muhanga deployment

    Current setup:
    - 200 vehicles
    - 2 swaps per vehicle per day
    - 300 total batteries
    - 100 charging ports
    - 4 swapping stations
    """
    # Total demand: 200 vehicles × 2 swaps/day = 400 swaps/day
    # = 16.67 swaps/hour

    # Assume demand distributed across 4 stations
    # Station 1: City center (high demand)
    # Station 2-3: Residential areas (medium demand)
    # Station 4: Industrial area (lower demand)

    stations = [
        SwappingStation(
            station_id=1,
            demand_rate=6.67,  # swaps/hour (40% of demand)
            demand_std=2.0,
            transport_time=0.5  # 30 minutes from central hub
        ),
        SwappingStation(
            station_id=2,
            demand_rate=4.17,  # swaps/hour (25% of demand)
            demand_std=1.5,
            transport_time=0.33  # 20 minutes
        ),
        SwappingStation(
            station_id=3,
            demand_rate=4.17,  # swaps/hour (25% of demand)
            demand_std=1.5,
            transport_time=0.33  # 20 minutes
        ),
        SwappingStation(
            station_id=4,
            demand_rate=1.67,  # swaps/hour (10% of demand)
            demand_std=0.8,
            transport_time=0.67  # 40 minutes
        )
    ]

    params = SystemParameters(
        charging_time=3.0,  # hours
        battery_cost=450.0,  # USD
        charging_port_cost=300.0,  # USD (estimate for 15A charger)
        electricity_cost=0.15,  # USD per kWh (Rwanda rate)
        battery_capacity=3.55,  # kWh (74V × 48Ah)
        charging_power=1.11,  # kW (15A × 74V)
        service_level_central=0.05,  # 95% service level (εC = 0.05)
        service_level_station=0.05   # 95% service level (εS = 0.05)
    )

    return BatteryNetworkModel(stations, params)


if __name__ == "__main__":
    # Create model for Muhanga
    print("=" * 60)
    print("BATTERY SWAPPING NETWORK OPTIMIZATION")
    print("Muhanga, Rwanda - 200 vehicles, 2 swaps/day")
    print("=" * 60)
    print()

    model = create_muhanga_model()

    # 1. Evaluate current setup
    print("1. EVALUATING YOUR CURRENT SETUP")
    print("-" * 60)
    current_eval = model.simulate_current_setup(
        current_batteries=300,
        current_ports=100
    )

    print(f"Current batteries: {current_eval['current_total_batteries']}")
    print(f"Current charging ports: {current_eval['current_charging_ports']}")
    print(f"Minimum required (paper): {current_eval['min_required_batteries']:.1f}")
    print(f"Meets requirement: {current_eval['meets_paper_requirement']}")
    print(f"Surplus: {current_eval['surplus_batteries']:.1f} batteries ({current_eval['surplus_percentage']:.1f}%)")
    print()

    # 2. Optimize network
    print("2. OPTIMIZING NETWORK CONFIGURATION")
    print("-" * 60)
    optimal = model.optimize_network()

    if optimal['success']:
        print(f"✓ Optimization successful!")
        print()
        print(f"Optimal central hub stock (R): {optimal['R_central_hub']:.1f} batteries")
        print(f"Total batteries needed: {optimal['total_batteries']:.1f}")
        print(f"Charging ports needed: {optimal['charging_ports_needed']}")
        print()
        print("Station reorder points (ri):")
        for i, r_i in enumerate(optimal['r_reorder_points']):
            print(f"  Station {i+1}: {r_i:.1f} batteries")
        print()
        print("Station order quantities (Qi):")
        for i, Q_i in enumerate(optimal['Q_order_quantities']):
            print(f"  Station {i+1}: {Q_i:.1f} batteries per delivery")
        print()

        # Cost analysis
        costs = optimal['cost_breakdown']
        print("COST BREAKDOWN:")
        print(f"  Battery investment: ${costs['battery_investment']:,.0f}")
        print(f"  Charging infrastructure: ${costs['charging_infrastructure']:,.0f}")
        print(f"  Annual transport: ${costs['annual_transport']:,.0f}")
        print(f"  Annual electricity: ${costs['annual_electricity']:,.0f}")
        print(f"  Total cost (3-year NPV): ${optimal['total_cost']:,.0f}")
        print()

        # Comparison
        print("3. COMPARISON: CURRENT vs OPTIMAL")
        print("-" * 60)
        battery_diff = optimal['total_batteries'] - current_eval['current_total_batteries']
        print(f"Battery difference: {battery_diff:+.1f} batteries")
        print(f"Cost difference: ${optimal['total_cost'] - current_eval['current_total_cost']:+,.0f}")

        if battery_diff < 0:
            print(f"✓ You could reduce batteries by {abs(battery_diff):.0f} and still maintain service levels")
        else:
            print(f"⚠ Consider adding {battery_diff:.0f} batteries for optimal service")
    else:
        print(f"✗ Optimization failed: {optimal['optimization_result'].message}")
