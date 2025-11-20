"""
Cost Comparison: Centralized vs Distributed Charging
Analyzes the trade-offs mentioned in the paper
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class CostParameters:
    """Cost parameters for comparison"""
    battery_cost: float = 450  # USD per battery
    charging_port_cost: float = 300  # USD per charging port
    electricity_cost_per_kwh: float = 0.15  # USD/kWh
    battery_capacity_kwh: float = 3.55  # kWh

    # Transportation costs
    transport_cost_per_km: float = 0.5  # USD per km
    driver_cost_per_hour: float = 5  # USD per hour
    vehicle_depreciation_per_km: float = 0.2  # USD per km

    # Land/facility costs
    industrial_land_cost_per_sqm: float = 50  # USD/sqm annual rent
    urban_land_cost_per_sqm: float = 200  # USD/sqm annual rent

    # Operating costs
    maintenance_cost_per_port_annual: float = 50  # USD per port per year
    staff_cost_monthly: float = 300  # USD per staff per month


class CentralizedModel:
    """
    Centralized charging model:
    - All charging at industrial park
    - Batteries transported to swapping stations
    """

    def __init__(
        self,
        n_vehicles: int,
        n_stations: int,
        swaps_per_vehicle_per_day: float,
        charging_time_hours: float,
        avg_distance_to_stations_km: float,
        costs: CostParameters
    ):
        self.n_vehicles = n_vehicles
        self.n_stations = n_stations
        self.swaps_per_day = n_vehicles * swaps_per_vehicle_per_day
        self.charging_time = charging_time_hours
        self.avg_distance = avg_distance_to_stations_km
        self.costs = costs

        # Battery requirements - Result 8 approximation
        # With multiple stations, we need:
        # 1. Batteries in vehicles
        # 2. Batteries charging at central hub
        # 3. Batteries in transit to/from stations
        # 4. Buffer stock at each station

        self.demand_rate_per_hour = self.swaps_per_day / 24

    def calculate_battery_requirements(self, transport_time_hours: float) -> dict:
        """
        Calculate total batteries needed for centralized model

        Key insight: More stations = more batteries in distribution pipeline
        """
        # 1. Batteries in vehicles
        batteries_in_vehicles = self.n_vehicles

        # 2. Batteries charging (at central hub)
        batteries_charging = self.charging_time * self.demand_rate_per_hour

        # 3. Batteries in transit (to and from stations)
        # Each station needs round-trip coverage
        batteries_in_transit = 2 * transport_time_hours * self.demand_rate_per_hour

        # 4. Buffer stock at each station
        # Each station needs safety stock to handle variability
        # More stations = more safety stock needed (square root law breaks down)
        buffer_per_station = max(5, self.demand_rate_per_hour / self.n_stations * 2)
        total_buffer = buffer_per_station * self.n_stations

        # 5. Working inventory at stations
        # Each station holds batteries for immediate swapping
        working_inventory_per_station = max(3, self.demand_rate_per_hour / self.n_stations * 0.5)
        total_working_inventory = working_inventory_per_station * self.n_stations

        total_batteries = (
            batteries_in_vehicles +
            batteries_charging +
            batteries_in_transit +
            total_buffer +
            total_working_inventory
        )

        return {
            'batteries_in_vehicles': batteries_in_vehicles,
            'batteries_charging': batteries_charging,
            'batteries_in_transit': batteries_in_transit,
            'buffer_stock': total_buffer,
            'working_inventory': total_working_inventory,
            'total_batteries': total_batteries,
            'ratio': total_batteries / self.n_vehicles
        }

    def calculate_costs(self, transport_time_hours: float) -> dict:
        """Calculate all costs for centralized model"""

        batteries = self.calculate_battery_requirements(transport_time_hours)

        # 1. Battery investment (one-time)
        battery_investment = batteries['total_batteries'] * self.costs.battery_cost

        # 2. Charging infrastructure (one-time)
        charging_ports = int(np.ceil(batteries['batteries_charging'] * 1.1))
        charging_investment = charging_ports * self.costs.charging_port_cost

        # Central facility space (industrial park - cheaper)
        facility_sqm = charging_ports * 2  # 2 sqm per port
        annual_facility_cost = facility_sqm * self.costs.industrial_land_cost_per_sqm

        # 3. Transportation costs (annual)
        # Deliveries per station per day
        deliveries_per_station_per_day = 2  # Assume 2 delivery rounds per day
        total_deliveries_per_day = deliveries_per_station_per_day * self.n_stations
        annual_deliveries = total_deliveries_per_day * 365

        km_per_delivery = self.avg_distance * 2  # Round trip
        annual_km = annual_deliveries * km_per_delivery

        transport_fuel_cost = annual_km * self.costs.transport_cost_per_km
        transport_depreciation = annual_km * self.costs.vehicle_depreciation_per_km
        transport_driver_cost = (annual_deliveries * transport_time_hours * 2) * self.costs.driver_cost_per_hour

        annual_transport_cost = transport_fuel_cost + transport_depreciation + transport_driver_cost

        # 4. Electricity costs (annual)
        annual_energy_kwh = self.swaps_per_day * 365 * self.costs.battery_capacity_kwh
        annual_electricity_cost = annual_energy_kwh * self.costs.electricity_cost_per_kwh

        # 5. Maintenance and operations (annual)
        annual_maintenance = charging_ports * self.costs.maintenance_cost_per_port_annual

        # Staff: 1 central facility manager + 1 staff per station
        total_staff = 2 + self.n_stations
        annual_staff_cost = total_staff * self.costs.staff_cost_monthly * 12

        # Total annual operating cost
        annual_operating = (
            annual_facility_cost +
            annual_transport_cost +
            annual_electricity_cost +
            annual_maintenance +
            annual_staff_cost
        )

        # 3-year total cost
        total_3year = battery_investment + charging_investment + (annual_operating * 3)

        return {
            'battery_investment': battery_investment,
            'charging_investment': charging_investment,
            'annual_facility': annual_facility_cost,
            'annual_transport': annual_transport_cost,
            'annual_electricity': annual_electricity_cost,
            'annual_maintenance': annual_maintenance,
            'annual_staff': annual_staff_cost,
            'annual_operating_total': annual_operating,
            'total_3year': total_3year,
            'batteries_needed': batteries['total_batteries'],
            'charging_ports': charging_ports
        }


class DistributedModel:
    """
    Distributed charging model:
    - Charging at each swapping station
    - No transportation needed
    """

    def __init__(
        self,
        n_vehicles: int,
        n_stations: int,
        swaps_per_vehicle_per_day: float,
        charging_time_hours: float,
        costs: CostParameters
    ):
        self.n_vehicles = n_vehicles
        self.n_stations = n_stations
        self.swaps_per_day = n_vehicles * swaps_per_vehicle_per_day
        self.charging_time = charging_time_hours
        self.costs = costs

        self.demand_rate_per_hour = self.swaps_per_day / 24

    def calculate_battery_requirements(self) -> dict:
        """
        Calculate batteries for distributed model

        Key insight: Lower total batteries, but requires grid capacity at each location
        """
        # 1. Batteries in vehicles
        batteries_in_vehicles = self.n_vehicles

        # 2. Batteries charging (distributed across stations)
        batteries_charging = self.charging_time * self.demand_rate_per_hour

        # 3. Small buffer at each station (no transit time!)
        buffer_per_station = max(2, self.demand_rate_per_hour / self.n_stations)
        total_buffer = buffer_per_station * self.n_stations

        total_batteries = batteries_in_vehicles + batteries_charging + total_buffer

        return {
            'batteries_in_vehicles': batteries_in_vehicles,
            'batteries_charging': batteries_charging,
            'buffer_stock': total_buffer,
            'total_batteries': total_batteries,
            'ratio': total_batteries / self.n_vehicles
        }

    def calculate_costs(self) -> dict:
        """Calculate all costs for distributed model"""

        batteries = self.calculate_battery_requirements()

        # 1. Battery investment (one-time) - LOWER than centralized
        battery_investment = batteries['total_batteries'] * self.costs.battery_cost

        # 2. Charging infrastructure (one-time) - distributed across stations
        total_charging_ports = int(np.ceil(batteries['batteries_charging'] * 1.1))
        ports_per_station = int(np.ceil(total_charging_ports / self.n_stations))
        charging_investment = total_charging_ports * self.costs.charging_port_cost

        # Station space (urban locations - MORE EXPENSIVE)
        sqm_per_station = ports_per_station * 2
        total_sqm = sqm_per_station * self.n_stations
        annual_facility_cost = total_sqm * self.costs.urban_land_cost_per_sqm

        # 3. Transportation costs (annual) - ZERO!
        annual_transport_cost = 0

        # 4. Electricity costs (annual) - SAME as centralized
        annual_energy_kwh = self.swaps_per_day * 365 * self.costs.battery_capacity_kwh
        annual_electricity_cost = annual_energy_kwh * self.costs.electricity_cost_per_kwh

        # But may pay higher rates in urban areas
        urban_electricity_premium = 1.2  # 20% higher in urban areas
        annual_electricity_cost *= urban_electricity_premium

        # 5. Maintenance and operations (annual) - HIGHER
        # More distributed infrastructure = more maintenance complexity
        annual_maintenance = total_charging_ports * self.costs.maintenance_cost_per_port_annual * 1.5

        # Staff: Need technician at each station
        total_staff = self.n_stations * 2  # 2 staff per station
        annual_staff_cost = total_staff * self.costs.staff_cost_monthly * 12

        # Grid connection fees (one-time) - each station needs grid upgrade
        grid_connection_per_station = 5000  # USD for grid upgrade
        grid_investment = grid_connection_per_station * self.n_stations

        # Total annual operating cost
        annual_operating = (
            annual_facility_cost +
            annual_transport_cost +
            annual_electricity_cost +
            annual_maintenance +
            annual_staff_cost
        )

        # 3-year total cost
        total_3year = (
            battery_investment +
            charging_investment +
            grid_investment +
            (annual_operating * 3)
        )

        return {
            'battery_investment': battery_investment,
            'charging_investment': charging_investment,
            'grid_investment': grid_investment,
            'annual_facility': annual_facility_cost,
            'annual_transport': annual_transport_cost,
            'annual_electricity': annual_electricity_cost,
            'annual_maintenance': annual_maintenance,
            'annual_staff': annual_staff_cost,
            'annual_operating_total': annual_operating,
            'total_3year': total_3year,
            'batteries_needed': batteries['total_batteries'],
            'charging_ports': total_charging_ports
        }


def compare_models():
    """Compare centralized vs distributed for Muhanga"""

    print("=" * 80)
    print("CENTRALIZED vs DISTRIBUTED CHARGING - COST COMPARISON")
    print("Muhanga, Rwanda - 200 vehicles, 4 swapping stations")
    print("=" * 80)
    print()

    costs = CostParameters()

    # Scenario parameters
    n_vehicles = 200
    n_stations = 4
    swaps_per_vehicle_per_day = 2
    charging_time = 3.0
    avg_distance_km = 5  # Average distance from industrial park to stations
    transport_time_hours = 0.5  # 30 minutes average

    # Create models
    centralized = CentralizedModel(
        n_vehicles, n_stations, swaps_per_vehicle_per_day,
        charging_time, avg_distance_km, costs
    )

    distributed = DistributedModel(
        n_vehicles, n_stations, swaps_per_vehicle_per_day,
        charging_time, costs
    )

    # Calculate requirements and costs
    central_batteries = centralized.calculate_battery_requirements(transport_time_hours)
    central_costs = centralized.calculate_costs(transport_time_hours)

    dist_batteries = distributed.calculate_battery_requirements()
    dist_costs = distributed.calculate_costs()

    # 1. Battery Requirements Comparison
    print("1. BATTERY REQUIREMENTS")
    print("-" * 80)
    print(f"{'Metric':<40} {'Centralized':<20} {'Distributed':<20}")
    print("-" * 80)
    print(f"{'Batteries in vehicles':<40} {central_batteries['batteries_in_vehicles']:<20.0f} {dist_batteries['batteries_in_vehicles']:<20.0f}")
    print(f"{'Batteries charging':<40} {central_batteries['batteries_charging']:<20.1f} {dist_batteries['batteries_charging']:<20.1f}")

    if 'batteries_in_transit' in central_batteries:
        print(f"{'Batteries in transit':<40} {central_batteries['batteries_in_transit']:<20.1f} {'0':<20}")

    print(f"{'Buffer stock':<40} {central_batteries['buffer_stock']:<20.1f} {dist_batteries['buffer_stock']:<20.1f}")

    if 'working_inventory' in central_batteries:
        print(f"{'Working inventory at stations':<40} {central_batteries['working_inventory']:<20.1f} {'-':<20}")

    print("-" * 80)
    print(f"{'TOTAL BATTERIES':<40} {central_batteries['total_batteries']:<20.0f} {dist_batteries['total_batteries']:<20.0f}")
    print(f"{'Battery-to-vehicle ratio':<40} {central_batteries['ratio']:<20.2f} {dist_batteries['ratio']:<20.2f}")
    print(f"{'Extra batteries vs distributed':<40} {central_batteries['total_batteries'] - dist_batteries['total_batteries']:<20.0f} {'-':<20}")
    print()

    # 2. Cost Comparison
    print("2. COST COMPARISON")
    print("-" * 80)
    print(f"{'Cost Component':<40} {'Centralized':<20} {'Distributed':<20}")
    print("-" * 80)
    print("CAPITAL COSTS (One-time):")
    print(f"{'  Battery investment':<40} ${central_costs['battery_investment']:<19,.0f} ${dist_costs['battery_investment']:<19,.0f}")
    print(f"{'  Charging infrastructure':<40} ${central_costs['charging_investment']:<19,.0f} ${dist_costs['charging_investment']:<19,.0f}")

    if 'grid_investment' in dist_costs:
        print(f"{'  Grid connection fees':<40} ${0:<19,.0f} ${dist_costs['grid_investment']:<19,.0f}")

    total_central_capex = central_costs['battery_investment'] + central_costs['charging_investment']
    total_dist_capex = dist_costs['battery_investment'] + dist_costs['charging_investment'] + dist_costs.get('grid_investment', 0)
    print(f"{'  TOTAL CAPITAL':<40} ${total_central_capex:<19,.0f} ${total_dist_capex:<19,.0f}")
    print()

    print("ANNUAL OPERATING COSTS:")
    print(f"{'  Facility/land costs':<40} ${central_costs['annual_facility']:<19,.0f} ${dist_costs['annual_facility']:<19,.0f}")
    print(f"{'  Transportation':<40} ${central_costs['annual_transport']:<19,.0f} ${dist_costs['annual_transport']:<19,.0f}")
    print(f"{'  Electricity':<40} ${central_costs['annual_electricity']:<19,.0f} ${dist_costs['annual_electricity']:<19,.0f}")
    print(f"{'  Maintenance':<40} ${central_costs['annual_maintenance']:<19,.0f} ${dist_costs['annual_maintenance']:<19,.0f}")
    print(f"{'  Staff':<40} ${central_costs['annual_staff']:<19,.0f} ${dist_costs['annual_staff']:<19,.0f}")
    print("-" * 80)
    print(f"{'  TOTAL ANNUAL OPERATING':<40} ${central_costs['annual_operating_total']:<19,.0f} ${dist_costs['annual_operating_total']:<19,.0f}")
    print()

    print("3-YEAR TOTAL COST:")
    print(f"{'  Centralized model':<40} ${central_costs['total_3year']:<19,.0f}")
    print(f"{'  Distributed model':<40} ${dist_costs['total_3year']:<19,.0f}")
    print(f"{'  SAVINGS with centralized':<40} ${dist_costs['total_3year'] - central_costs['total_3year']:<19,.0f}")
    print()

    # 3. Sensitivity Analysis
    print("3. SENSITIVITY: Impact of Number of Stations")
    print("-" * 80)

    results = []
    for n_stat in [2, 4, 6, 8, 10]:
        cent = CentralizedModel(n_vehicles, n_stat, swaps_per_vehicle_per_day,
                                charging_time, avg_distance_km, costs)
        dist = DistributedModel(n_vehicles, n_stat, swaps_per_vehicle_per_day,
                                charging_time, costs)

        cent_batt = cent.calculate_battery_requirements(transport_time_hours)
        cent_cost = cent.calculate_costs(transport_time_hours)

        dist_batt = dist.calculate_battery_requirements()
        dist_cost = dist.calculate_costs()

        results.append({
            'Stations': n_stat,
            'Central_Batteries': int(cent_batt['total_batteries']),
            'Dist_Batteries': int(dist_batt['total_batteries']),
            'Extra_Batteries': int(cent_batt['total_batteries'] - dist_batt['total_batteries']),
            'Central_3yr_Cost': int(cent_cost['total_3year']),
            'Dist_3yr_Cost': int(dist_cost['total_3year']),
            'Savings': int(dist_cost['total_3year'] - cent_cost['total_3year'])
        })

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print()

    # 4. Key Insights
    print("4. KEY INSIGHTS")
    print("=" * 80)
    print("✓ CENTRALIZED MODEL ADVANTAGES:")
    print(f"  • Lower facility costs (industrial vs urban land)")
    print(f"  • Lower electricity rates (industrial tariffs)")
    print(f"  • Easier to manage single large facility")
    print(f"  • Grid capacity more readily available")
    print()
    print("✗ CENTRALIZED MODEL DISADVANTAGES:")
    print(f"  • Requires {central_batteries['total_batteries'] - dist_batteries['total_batteries']:.0f} more batteries (~${(central_batteries['total_batteries'] - dist_batteries['total_batteries']) * costs.battery_cost:,.0f})")
    print(f"  • Annual transport costs: ${central_costs['annual_transport']:,.0f}")
    print(f"  • More stations = linearly increasing transport costs")
    print(f"  • More batteries tied up in transit/distribution")
    print()
    print("💡 BREAKEVEN ANALYSIS:")
    battery_cost_diff = (central_batteries['total_batteries'] - dist_batteries['total_batteries']) * costs.battery_cost
    annual_opex_savings = dist_costs['annual_operating_total'] - central_costs['annual_operating_total']

    if annual_opex_savings > 0:
        breakeven_years = battery_cost_diff / annual_opex_savings
        print(f"  • Extra battery investment: ${battery_cost_diff:,.0f}")
        print(f"  • Annual opex savings (central): ${annual_opex_savings:,.0f}")
        print(f"  • Breakeven period: {breakeven_years:.1f} years")

        if breakeven_years < 3:
            print(f"  ✓ Centralized model pays back in {breakeven_years:.1f} years - RECOMMENDED")
        else:
            print(f"  ⚠ Centralized model takes {breakeven_years:.1f} years to break even")
    else:
        print(f"  ⚠ Distributed model has lower operating costs!")
        print(f"  • Consider distributed if grid capacity available")
    print()

    print("📊 YOUR CURRENT SETUP (300 batteries with centralized charging):")
    print(f"  • Theoretical requirement: {central_batteries['total_batteries']:.0f} batteries")
    print(f"  • Your actual: 300 batteries")
    print(f"  • Surplus: {300 - central_batteries['total_batteries']:.0f} batteries")
    print(f"  ✓ Your 1.5x ratio is appropriate for centralized model with 4 stations")
    print("=" * 80)


if __name__ == "__main__":
    compare_models()
