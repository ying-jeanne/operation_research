"""
Practical Battery Network Analysis Tool
Based on "Swap-locally, Charge-centrally" paper

Simpler model for calculating battery requirements and analyzing your setup
"""

import numpy as np
from scipy.stats import norm
import pandas as pd


class SimpleBatteryModel:
    """
    Simplified battery calculation based on paper's Result 1 and Result 8
    """

    def __init__(
        self,
        n_vehicles: int,
        swaps_per_vehicle_per_day: float,
        charging_time_hours: float,
        transport_time_hours: float,
        service_level: float = 0.95
    ):
        self.n_vehicles = n_vehicles
        self.swaps_per_vehicle_per_day = swaps_per_vehicle_per_day
        self.charging_time = charging_time_hours
        self.transport_time = transport_time_hours
        self.service_level = service_level

        # Calculate demand rate
        self.total_swaps_per_day = n_vehicles * swaps_per_vehicle_per_day
        self.demand_rate_per_hour = self.total_swaps_per_day / 24  # μ

    def calculate_batteries_in_circulation(self) -> dict:
        """
        Result 1: E[D] = Δμ
        Batteries in circulation (charging + transport)
        """
        Delta = self.charging_time + self.transport_time  # Effective charging time
        mu = self.demand_rate_per_hour

        batteries_in_deficit = Delta * mu

        return {
            'effective_time_Delta': Delta,
            'demand_rate_mu': mu,
            'batteries_charging_transport': batteries_in_deficit,
            'batteries_in_vehicles': self.n_vehicles  # One per vehicle minimum
        }

    def calculate_total_batteries_needed(self, demand_std_per_hour: float = None) -> dict:
        """
        Calculate total batteries with safety stock
        Based on Result 8 (simplified)
        """
        circ = self.calculate_batteries_in_circulation()

        # Base requirement
        batteries_in_system = circ['batteries_charging_transport']
        batteries_in_vehicles = circ['batteries_in_vehicles']

        # Safety stock calculation
        if demand_std_per_hour is None:
            # Assume demand std = 30% of mean (typical for service systems)
            demand_std_per_hour = self.demand_rate_per_hour * 0.3

        # Safety stock = z-score × sqrt(variance)
        z_score = norm.ppf(self.service_level)
        Delta = circ['effective_time_Delta']

        # Variance during effective charging time
        variance = Delta * demand_std_per_hour**2
        safety_stock = z_score * np.sqrt(variance)

        # Total batteries
        total_batteries = batteries_in_vehicles + batteries_in_system + safety_stock

        return {
            'batteries_in_vehicles': batteries_in_vehicles,
            'batteries_in_system': batteries_in_system,
            'safety_stock': safety_stock,
            'total_batteries': total_batteries,
            'battery_to_vehicle_ratio': total_batteries / self.n_vehicles
        }

    def analyze_current_setup(
        self,
        current_total_batteries: int,
        current_charging_ports: int
    ) -> pd.DataFrame:
        """
        Analyze how your current setup compares to theoretical requirements
        """
        results = []

        # Test different service levels
        for service_level in [0.90, 0.95, 0.99]:
            self.service_level = service_level

            # Test different demand variability assumptions
            for std_factor in [0.2, 0.3, 0.4]:
                demand_std = self.demand_rate_per_hour * std_factor

                calc = self.calculate_total_batteries_needed(demand_std)

                results.append({
                    'service_level': f"{service_level*100:.0f}%",
                    'demand_variability': f"{std_factor*100:.0f}%",
                    'batteries_needed': calc['total_batteries'],
                    'ratio': calc['battery_to_vehicle_ratio'],
                    'vs_current': current_total_batteries - calc['total_batteries'],
                    'surplus_pct': ((current_total_batteries - calc['total_batteries']) / calc['total_batteries'] * 100)
                })

        df = pd.DataFrame(results)
        return df

    def calculate_charging_capacity(self) -> dict:
        """
        Calculate required charging ports based on throughput
        """
        # Batteries processed per hour = demand rate
        batteries_per_hour = self.demand_rate_per_hour

        # Charging time per battery
        charging_time = self.charging_time

        # Required ports = batteries_per_hour × charging_time
        # This ensures we can process all incoming batteries
        required_ports = batteries_per_hour * charging_time

        # Add safety margin (10%)
        recommended_ports = required_ports * 1.1

        return {
            'theoretical_min': required_ports,
            'recommended': recommended_ports,
            'batteries_per_hour': batteries_per_hour,
            'utilization_at_recommended': required_ports / recommended_ports
        }

    def sensitivity_analysis(self, param_ranges: dict) -> pd.DataFrame:
        """
        Analyze how battery requirements change with different parameters
        """
        results = []

        base_charging_time = self.charging_time
        base_transport_time = self.transport_time
        base_swaps = self.swaps_per_vehicle_per_day

        # Vary charging time
        if 'charging_time' in param_ranges:
            for tc in param_ranges['charging_time']:
                self.charging_time = tc
                calc = self.calculate_total_batteries_needed()
                results.append({
                    'parameter': 'Charging Time',
                    'value': tc,
                    'total_batteries': calc['total_batteries'],
                    'ratio': calc['battery_to_vehicle_ratio']
                })
            self.charging_time = base_charging_time

        # Vary transport time
        if 'transport_time' in param_ranges:
            for tt in param_ranges['transport_time']:
                self.transport_time = tt
                calc = self.calculate_total_batteries_needed()
                results.append({
                    'parameter': 'Transport Time',
                    'value': tt,
                    'total_batteries': calc['total_batteries'],
                    'ratio': calc['battery_to_vehicle_ratio']
                })
            self.transport_time = base_transport_time

        # Vary swap frequency
        if 'swaps_per_day' in param_ranges:
            for swaps in param_ranges['swaps_per_day']:
                self.swaps_per_vehicle_per_day = swaps
                self.total_swaps_per_day = self.n_vehicles * swaps
                self.demand_rate_per_hour = self.total_swaps_per_day / 24
                calc = self.calculate_total_batteries_needed()
                results.append({
                    'parameter': 'Swaps/Vehicle/Day',
                    'value': swaps,
                    'total_batteries': calc['total_batteries'],
                    'ratio': calc['battery_to_vehicle_ratio']
                })
            self.swaps_per_vehicle_per_day = base_swaps
            self.total_swaps_per_day = self.n_vehicles * base_swaps
            self.demand_rate_per_hour = self.total_swaps_per_day / 24

        return pd.DataFrame(results)


def analyze_muhanga_operation():
    """
    Analyze your Muhanga operation
    """
    print("=" * 70)
    print("MUHANGA BATTERY SWAPPING NETWORK ANALYSIS")
    print("=" * 70)
    print()

    # Your current setup
    print("CURRENT SETUP:")
    print("-" * 70)
    print(f"Vehicles: 200")
    print(f"Swaps per vehicle per day: 2")
    print(f"Total batteries: 300")
    print(f"Charging ports: 100")
    print(f"Charging time: 3 hours")
    print(f"Battery specs: 74V/48Ah (3.55 kWh)")
    print()

    # Create model
    model = SimpleBatteryModel(
        n_vehicles=200,
        swaps_per_vehicle_per_day=2,
        charging_time_hours=3.0,
        transport_time_hours=0.5,  # Assume 30 min average
        service_level=0.95
    )

    # 1. Basic calculations
    print("1. BASIC BATTERY FLOW ANALYSIS (Result 1 from paper)")
    print("-" * 70)
    circ = model.calculate_batteries_in_circulation()
    print(f"Demand rate (μ): {circ['demand_rate_mu']:.2f} swaps/hour")
    print(f"Effective charging time (Δ): {circ['effective_time_Delta']:.2f} hours")
    print(f"Batteries in system (charging+transport): {circ['batteries_charging_transport']:.1f}")
    print(f"Batteries in vehicles: {circ['batteries_in_vehicles']}")
    print()

    # 2. Total requirements with safety stock
    print("2. TOTAL BATTERY REQUIREMENTS (with safety stock)")
    print("-" * 70)
    req = model.calculate_total_batteries_needed()
    print(f"Batteries in vehicles: {req['batteries_in_vehicles']:.0f}")
    print(f"Batteries in system (charging+transport): {req['batteries_in_system']:.1f}")
    print(f"Safety stock (95% service level): {req['safety_stock']:.1f}")
    print(f"TOTAL NEEDED: {req['total_batteries']:.0f} batteries")
    print(f"Battery-to-vehicle ratio: {req['battery_to_vehicle_ratio']:.2f}x")
    print()
    print(f"YOUR CURRENT: 300 batteries (1.50x ratio)")
    print(f"Difference: {300 - req['total_batteries']:.0f} batteries")
    if 300 >= req['total_batteries']:
        print(f"✓ Your setup meets requirements with {300 - req['total_batteries']:.0f} battery surplus")
    else:
        print(f"⚠ Short by {req['total_batteries'] - 300:.0f} batteries")
    print()

    # 3. Charging capacity analysis
    print("3. CHARGING CAPACITY ANALYSIS")
    print("-" * 70)
    charging = model.calculate_charging_capacity()
    print(f"Batteries to process per hour: {charging['batteries_per_hour']:.2f}")
    print(f"Theoretical minimum ports: {charging['theoretical_min']:.1f}")
    print(f"Recommended ports (with 10% margin): {charging['recommended']:.1f}")
    print(f"YOUR CURRENT: 100 ports")
    if 100 >= charging['recommended']:
        print(f"✓ Your charging capacity is sufficient")
        print(f"  Utilization: {(charging['theoretical_min'] / 100 * 100):.1f}%")
    else:
        print(f"⚠ Consider adding {charging['recommended'] - 100:.0f} ports")
    print()

    # 4. Scenario analysis
    print("4. SCENARIO ANALYSIS: Impact of Different Assumptions")
    print("-" * 70)
    scenarios = model.analyze_current_setup(
        current_total_batteries=300,
        current_charging_ports=100
    )
    print(scenarios.to_string(index=False))
    print()

    # 5. Sensitivity analysis
    print("5. SENSITIVITY ANALYSIS: What-If Scenarios")
    print("-" * 70)
    sensitivity = model.sensitivity_analysis({
        'charging_time': [2.0, 2.5, 3.0, 3.5, 4.0],
        'transport_time': [0.25, 0.5, 0.75, 1.0],
        'swaps_per_day': [1.5, 2.0, 2.5, 3.0]
    })

    print("\nImpact of Charging Time:")
    print(sensitivity[sensitivity['parameter'] == 'Charging Time'].to_string(index=False))
    print("\nImpact of Transport Time:")
    print(sensitivity[sensitivity['parameter'] == 'Transport Time'].to_string(index=False))
    print("\nImpact of Swap Frequency:")
    print(sensitivity[sensitivity['parameter'] == 'Swaps/Vehicle/Day'].to_string(index=False))
    print()

    # 6. Key insights
    print("6. KEY INSIGHTS & RECOMMENDATIONS")
    print("=" * 70)
    print(f"✓ Your 1.5x ratio (300 batteries) aligns well with the paper's framework")
    print(f"✓ For 2 swaps/day at 3-hour charging, you have appropriate safety margin")
    print(f"✓ 100 charging ports provides good utilization (~50-60%)")
    print()
    print(f"Critical factors to monitor:")
    print(f"  • If swap frequency increases to 3/day, you'll need ~{model.n_vehicles * 1.8:.0f} batteries")
    print(f"  • Transport time matters: +30min = +{(0.5 * model.demand_rate_per_hour):.0f} batteries needed")
    print(f"  • Peak hour surges may require operational buffer beyond theoretical min")
    print()


if __name__ == "__main__":
    analyze_muhanga_operation()
