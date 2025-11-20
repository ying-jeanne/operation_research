"""
COMPREHENSIVE ANALYSIS: Centralized vs Distributed Charging
With ALL corrected assumptions and real-world costs
"""

import pandas as pd
import numpy as np


class ComprehensiveCostAnalysis:
    """
    Full cost analysis including:
    - Correct battery lifespan (2.96 years at 2.5 charges/day)
    - Transportation costs
    - Extra batteries for centralized model
    - Land/facility costs
    - Grid connection costs
    - Operational complexity
    """

    def __init__(self):
        # Fleet parameters
        self.n_vehicles = 200
        self.charges_per_vehicle_per_day = 2.5
        self.total_charges_per_day = 500
        self.n_stations = 4

        # Battery parameters (CORRECTED)
        self.battery_cost = 450
        self.battery_cycle_life = 1800
        self.charging_time_hours = 3.0
        self.transport_time_hours = 0.5

        # Cost parameters
        self.charging_port_cost_15A = 300
        self.charging_port_cost_30A = 500  # Fast chargers cost more

        # Transportation costs
        self.transport_cost_per_km = 0.5
        self.driver_cost_per_hour = 5
        self.vehicle_depreciation_per_km = 0.2
        self.avg_distance_to_station_km = 5

        # Facility costs (annual) - Muhanga is a small city, costs are similar
        self.industrial_land_cost_per_sqm = 30
        self.urban_land_cost_per_sqm = 40  # Only slightly higher, not 4x

        # Grid connection (one-time)
        self.grid_connection_per_station = 5000

        # Staff costs (monthly per person)
        self.staff_cost_monthly = 300

        # Electricity
        self.electricity_cost_kwh = 0.15
        self.urban_electricity_premium = 1.2  # 20% higher in urban
        self.battery_capacity_kwh = 3.55

    def calculate_centralized_model(self) -> dict:
        """Calculate all costs for centralized charging"""

        # 1. BATTERY INVENTORY
        batteries_in_vehicles = self.n_vehicles
        batteries_charging = self.charging_time_hours * (self.total_charges_per_day / 24)
        batteries_in_transit = 2 * self.transport_time_hours * (self.total_charges_per_day / 24)

        # Buffer per station
        buffer_per_station = max(5, (self.total_charges_per_day / 24) / self.n_stations * 2)
        total_buffer = buffer_per_station * self.n_stations

        # Working inventory at stations
        working_inventory_per_station = max(3, (self.total_charges_per_day / 24) / self.n_stations * 0.5)
        total_working_inventory = working_inventory_per_station * self.n_stations

        total_batteries = int(np.ceil(
            batteries_in_vehicles +
            batteries_charging +
            batteries_in_transit +
            total_buffer +
            total_working_inventory
        ))

        # 2. INITIAL CAPITAL
        battery_investment = total_batteries * self.battery_cost

        charging_ports = int(np.ceil(batteries_charging * 1.1))
        charging_investment = charging_ports * self.charging_port_cost_15A

        total_capex = battery_investment + charging_investment

        # 3. BATTERY REPLACEMENT COSTS (using corrected lifespan)
        cycles_per_battery_per_day = self.total_charges_per_day / total_batteries
        days_until_replacement = self.battery_cycle_life / cycles_per_battery_per_day
        years_until_replacement = days_until_replacement / 365

        annual_replacement_cost = (total_batteries / years_until_replacement) * self.battery_cost

        # 4. TRANSPORTATION COSTS (annual)
        deliveries_per_station_per_day = 2  # 2 delivery rounds per day
        total_deliveries_per_day = deliveries_per_station_per_day * self.n_stations
        annual_deliveries = total_deliveries_per_day * 365

        km_per_delivery = self.avg_distance_to_station_km * 2  # Round trip
        annual_km = annual_deliveries * km_per_delivery

        annual_transport_fuel = annual_km * self.transport_cost_per_km
        annual_transport_depreciation = annual_km * self.vehicle_depreciation_per_km
        annual_transport_driver = (annual_deliveries * self.transport_time_hours * 2) * self.driver_cost_per_hour

        annual_transport_total = annual_transport_fuel + annual_transport_depreciation + annual_transport_driver

        # 5. FACILITY COSTS (annual)
        facility_sqm = charging_ports * 2
        annual_facility_cost = facility_sqm * self.industrial_land_cost_per_sqm

        # 6. ELECTRICITY COSTS (annual)
        annual_energy_kwh = self.total_charges_per_day * 365 * self.battery_capacity_kwh
        annual_electricity = annual_energy_kwh * self.electricity_cost_kwh

        # 7. STAFF COSTS (annual)
        # 2 staff at central hub + 1 per station
        total_staff = 2 + self.n_stations
        annual_staff = total_staff * self.staff_cost_monthly * 12

        # 8. MAINTENANCE (annual)
        annual_maintenance = charging_ports * 50  # $50 per port per year

        # TOTAL ANNUAL OPERATING COST
        annual_opex = (
            annual_replacement_cost +
            annual_transport_total +
            annual_facility_cost +
            annual_electricity +
            annual_staff +
            annual_maintenance
        )

        # 5-YEAR TOTAL
        total_5yr = total_capex + (annual_opex * 5)

        return {
            'model': 'Centralized',
            'batteries': total_batteries,
            'batteries_breakdown': {
                'in_vehicles': batteries_in_vehicles,
                'charging': batteries_charging,
                'in_transit': batteries_in_transit,
                'buffer': total_buffer,
                'working_inventory': total_working_inventory
            },
            'charging_ports': charging_ports,
            'battery_lifespan_years': years_until_replacement,
            'capex_batteries': battery_investment,
            'capex_charging': charging_investment,
            'capex_total': total_capex,
            'annual_battery_replacement': annual_replacement_cost,
            'annual_transport': annual_transport_total,
            'annual_facility': annual_facility_cost,
            'annual_electricity': annual_electricity,
            'annual_staff': annual_staff,
            'annual_maintenance': annual_maintenance,
            'annual_opex_total': annual_opex,
            'total_5yr': total_5yr
        }

    def calculate_distributed_model(self) -> dict:
        """Calculate all costs for distributed charging"""

        # 1. BATTERY INVENTORY (LESS than centralized - no transit time!)
        batteries_in_vehicles = self.n_vehicles
        batteries_charging = self.charging_time_hours * (self.total_charges_per_day / 24)

        # Small buffer at each station
        buffer_per_station = max(2, (self.total_charges_per_day / 24) / self.n_stations)
        total_buffer = buffer_per_station * self.n_stations

        total_batteries = int(np.ceil(
            batteries_in_vehicles +
            batteries_charging +
            total_buffer
        ))

        # 2. INITIAL CAPITAL
        battery_investment = total_batteries * self.battery_cost

        charging_ports = int(np.ceil(batteries_charging * 1.1))
        charging_investment = charging_ports * self.charging_port_cost_15A

        # Grid connection fees (each station needs upgrade)
        grid_investment = self.grid_connection_per_station * self.n_stations

        total_capex = battery_investment + charging_investment + grid_investment

        # 3. BATTERY REPLACEMENT COSTS
        cycles_per_battery_per_day = self.total_charges_per_day / total_batteries
        days_until_replacement = self.battery_cycle_life / cycles_per_battery_per_day
        years_until_replacement = days_until_replacement / 365

        annual_replacement_cost = (total_batteries / years_until_replacement) * self.battery_cost

        # 4. TRANSPORTATION COSTS (ZERO!)
        annual_transport_total = 0

        # 5. FACILITY COSTS (HIGHER - urban locations)
        total_charging_ports = charging_ports
        ports_per_station = int(np.ceil(total_charging_ports / self.n_stations))
        sqm_per_station = ports_per_station * 2
        total_sqm = sqm_per_station * self.n_stations
        annual_facility_cost = total_sqm * self.urban_land_cost_per_sqm

        # 6. ELECTRICITY COSTS (HIGHER - urban premium)
        annual_energy_kwh = self.total_charges_per_day * 365 * self.battery_capacity_kwh
        annual_electricity = annual_energy_kwh * self.electricity_cost_kwh * self.urban_electricity_premium

        # 7. STAFF COSTS (HIGHER - need staff at each station)
        total_staff = self.n_stations * 2  # 2 per station
        annual_staff = total_staff * self.staff_cost_monthly * 12

        # 8. MAINTENANCE (HIGHER - distributed is more complex)
        annual_maintenance = charging_ports * 75  # $75 per port (50% more for distributed)

        # TOTAL ANNUAL OPERATING COST
        annual_opex = (
            annual_replacement_cost +
            annual_transport_total +
            annual_facility_cost +
            annual_electricity +
            annual_staff +
            annual_maintenance
        )

        # 5-YEAR TOTAL
        total_5yr = total_capex + (annual_opex * 5)

        return {
            'model': 'Distributed',
            'batteries': total_batteries,
            'batteries_breakdown': {
                'in_vehicles': batteries_in_vehicles,
                'charging': batteries_charging,
                'buffer': total_buffer
            },
            'charging_ports': charging_ports,
            'battery_lifespan_years': years_until_replacement,
            'capex_batteries': battery_investment,
            'capex_charging': charging_investment,
            'capex_grid': grid_investment,
            'capex_total': total_capex,
            'annual_battery_replacement': annual_replacement_cost,
            'annual_transport': annual_transport_total,
            'annual_facility': annual_facility_cost,
            'annual_electricity': annual_electricity,
            'annual_staff': annual_staff,
            'annual_maintenance': annual_maintenance,
            'annual_opex_total': annual_opex,
            'total_5yr': total_5yr
        }


def run_comprehensive_analysis():
    """Run full comparison with all corrected assumptions"""

    print("=" * 100)
    print("COMPREHENSIVE FINAL ANALYSIS: CENTRALIZED vs DISTRIBUTED CHARGING")
    print("With ALL Real-World Costs and Corrected Assumptions")
    print("=" * 100)
    print()
    print("ASSUMPTIONS:")
    print(f"  • 200 vehicles, 2.5 charges/vehicle/day = 500 charges/day")
    print(f"  • Battery cycle life: 1,800 cycles")
    print(f"  • Battery cost: $450")
    print(f"  • 15A charging (3 hour charge time)")
    print(f"  • 4 swapping stations")
    print()

    analyzer = ComprehensiveCostAnalysis()

    central = analyzer.calculate_centralized_model()
    distributed = analyzer.calculate_distributed_model()

    # 1. BATTERY REQUIREMENTS
    print("1. BATTERY INVENTORY REQUIREMENTS")
    print("-" * 100)
    print(f"{'Metric':<40} {'Centralized':<25} {'Distributed':<25} {'Difference':<15}")
    print("-" * 100)
    print(f"{'Batteries in vehicles':<40} {central['batteries_breakdown']['in_vehicles']:<25} {distributed['batteries_breakdown']['in_vehicles']:<25} {'-':<15}")
    print(f"{'Batteries charging':<40} {central['batteries_breakdown']['charging']:<25.1f} {distributed['batteries_breakdown']['charging']:<25.1f} {'-':<15}")
    print(f"{'Batteries in transit':<40} {central['batteries_breakdown']['in_transit']:<25.1f} {'0':<25} {central['batteries_breakdown']['in_transit']:<15.1f}")
    print(f"{'Buffer stock':<40} {central['batteries_breakdown']['buffer']:<25.1f} {distributed['batteries_breakdown']['buffer']:<25.1f} {central['batteries_breakdown']['buffer'] - distributed['batteries_breakdown']['buffer']:<15.1f}")
    print(f"{'Working inventory':<40} {central['batteries_breakdown']['working_inventory']:<25.1f} {'-':<25} {'-':<15}")
    print("-" * 100)
    print(f"{'TOTAL BATTERIES':<40} {central['batteries']:<25} {distributed['batteries']:<25} {central['batteries'] - distributed['batteries']:<15}")
    print(f"{'Battery lifespan':<40} {central['battery_lifespan_years']:<25.2f} {distributed['battery_lifespan_years']:<25.2f} {'-':<15}")
    print()

    # 2. CAPITAL COSTS
    print("2. INITIAL CAPITAL INVESTMENT")
    print("-" * 100)
    print(f"{'Cost Item':<40} {'Centralized':<25} {'Distributed':<25} {'Difference':<15}")
    print("-" * 100)
    print(f"{'Battery investment':<40} ${central['capex_batteries']:<24,} ${distributed['capex_batteries']:<24,} ${central['capex_batteries'] - distributed['capex_batteries']:<14,}")
    print(f"{'Charging infrastructure':<40} ${central['capex_charging']:<24,} ${distributed['capex_charging']:<24,} ${central['capex_charging'] - distributed['capex_charging']:<14,}")
    print(f"{'Grid connection fees':<40} ${0:<24,} ${distributed.get('capex_grid', 0):<24,} ${-distributed.get('capex_grid', 0):<14,}")
    print("-" * 100)
    print(f"{'TOTAL CAPEX':<40} ${central['capex_total']:<24,} ${distributed['capex_total']:<24,} ${central['capex_total'] - distributed['capex_total']:<14,}")
    print()

    # 3. ANNUAL OPERATING COSTS
    print("3. ANNUAL OPERATING COSTS")
    print("-" * 100)
    print(f"{'Cost Item':<40} {'Centralized':<25} {'Distributed':<25} {'Difference':<15}")
    print("-" * 100)
    print(f"{'Battery replacements':<40} ${central['annual_battery_replacement']:<24,.0f} ${distributed['annual_battery_replacement']:<24,.0f} ${central['annual_battery_replacement'] - distributed['annual_battery_replacement']:<14,.0f}")
    print(f"{'Transportation':<40} ${central['annual_transport']:<24,.0f} ${distributed['annual_transport']:<24,.0f} ${central['annual_transport'] - distributed['annual_transport']:<14,.0f}")
    print(f"{'Facility/land':<40} ${central['annual_facility']:<24,.0f} ${distributed['annual_facility']:<24,.0f} ${central['annual_facility'] - distributed['annual_facility']:<14,.0f}")
    print(f"{'Electricity':<40} ${central['annual_electricity']:<24,.0f} ${distributed['annual_electricity']:<24,.0f} ${central['annual_electricity'] - distributed['annual_electricity']:<14,.0f}")
    print(f"{'Staff':<40} ${central['annual_staff']:<24,.0f} ${distributed['annual_staff']:<24,.0f} ${central['annual_staff'] - distributed['annual_staff']:<14,.0f}")
    print(f"{'Maintenance':<40} ${central['annual_maintenance']:<24,.0f} ${distributed['annual_maintenance']:<24,.0f} ${central['annual_maintenance'] - distributed['annual_maintenance']:<14,.0f}")
    print("-" * 100)
    print(f"{'TOTAL ANNUAL OPEX':<40} ${central['annual_opex_total']:<24,.0f} ${distributed['annual_opex_total']:<24,.0f} ${central['annual_opex_total'] - distributed['annual_opex_total']:<14,.0f}")
    print()

    # 4. 5-YEAR TOTAL COST
    print("4. TOTAL COST OF OWNERSHIP (5 YEARS)")
    print("-" * 100)
    print(f"{'Model':<40} {'Initial Capex':<25} {'5-Year Opex':<25} {'5-Year Total':<25}")
    print("-" * 100)
    print(f"{'Centralized':<40} ${central['capex_total']:<24,} ${central['annual_opex_total']*5:<24,.0f} ${central['total_5yr']:<24,.0f}")
    print(f"{'Distributed':<40} ${distributed['capex_total']:<24,} ${distributed['annual_opex_total']*5:<24,.0f} ${distributed['total_5yr']:<24,.0f}")
    print("-" * 100)
    savings = distributed['total_5yr'] - central['total_5yr']
    if savings > 0:
        print(f"{'CENTRALIZED SAVES:':<40} ${savings:<24,.0f} ({(savings/distributed['total_5yr']*100):.1f}% cheaper)")
    else:
        print(f"{'DISTRIBUTED SAVES:':<40} ${abs(savings):<24,.0f} ({(abs(savings)/central['total_5yr']*100):.1f}% cheaper)")
    print()

    # 5. QUALITATIVE FACTORS
    print("5. QUALITATIVE FACTORS (NOT QUANTIFIED ABOVE)")
    print("=" * 100)
    print()
    print("CENTRALIZED ADVANTAGES:")
    print("  ✓ Single point of management - easier to supervise")
    print("  ✓ Grid capacity readily available at industrial park")
    print("  ✓ Economies of scale in operations")
    print("  ✓ Easier quality control and monitoring")
    print("  ✓ Lower electricity rates (industrial tariff)")
    print("  ✓ Cheaper land (industrial vs urban)")
    print()
    print("CENTRALIZED DISADVANTAGES:")
    print(f"  ✗ Need {central['batteries'] - distributed['batteries']} extra batteries (tied up capital)")
    print(f"  ✗ Transportation costs: ${central['annual_transport']:,.0f}/year")
    print("  ✗ Transportation risk (delays, vehicle breakdowns)")
    print("  ✗ Complexity of logistics (battery tracking)")
    print("  ✗ Fuel price exposure")
    print()
    print("DISTRIBUTED ADVANTAGES:")
    print(f"  ✓ Fewer batteries needed ({distributed['batteries']} vs {central['batteries']})")
    print("  ✓ No transportation costs or logistics")
    print("  ✓ Batteries always at point of use")
    print("  ✓ Simpler battery tracking")
    print("  ✓ More resilient (one station down ≠ system failure)")
    print()
    print("DISTRIBUTED DISADVANTAGES:")
    print("  ✗ Grid capacity may not be available in urban areas (MAJOR RISK)")
    print("  ✗ Higher land costs (urban locations)")
    print("  ✗ Higher electricity costs (urban premium)")
    print("  ✗ More staff needed (2 per station vs centralized team)")
    print("  ✗ More complex maintenance (4 locations vs 1)")
    print("  ✗ Higher infrastructure costs per kW")
    print()

    # 6. FINAL RECOMMENDATION
    print("6. FINAL RECOMMENDATION")
    print("=" * 100)
    print()

    # Calculate key metrics
    capex_diff = central['capex_total'] - distributed['capex_total']
    opex_diff = central['annual_opex_total'] - distributed['annual_opex_total']
    total_diff = central['total_5yr'] - distributed['total_5yr']

    print(f"FINANCIAL COMPARISON:")
    print(f"  • Initial capital: Centralized costs ${abs(capex_diff):,} {'MORE' if capex_diff > 0 else 'LESS'}")
    print(f"  • Annual operating: Centralized costs ${abs(opex_diff):,} {'MORE' if opex_diff > 0 else 'LESS'} per year")
    print(f"  • 5-year total: Centralized costs ${abs(total_diff):,} {'MORE' if total_diff > 0 else 'LESS'}")
    print()

    if abs(total_diff) < 50000:
        print("💡 VERDICT: COSTS ARE SIMILAR - DECISION DEPENDS ON NON-FINANCIAL FACTORS")
        print()
        print("Key decision factors:")
        print("  1. Grid availability: Can urban stations get 60-100kW power? (CRITICAL)")
        print("  2. Operational preference: Centralized control vs distributed resilience")
        print("  3. Land availability: Can you secure urban space for 4 stations?")
        print("  4. Growth plans: Centralized scales worse with more stations")
        print()
        print("RECOMMENDATION: CENTRALIZED for Muhanga because:")
        print("  ✓ Industrial park has reliable grid capacity")
        print("  ✓ Urban grid may not support 4 distributed charging stations")
        print("  ✓ Rwanda's electrical infrastructure favors centralized approach")
        print("  ✓ Operational simplicity outweighs small cost difference")
    elif total_diff > 0:
        print(f"💡 VERDICT: DISTRIBUTED IS CHEAPER by ${abs(total_diff):,} over 5 years")
        print()
        print("HOWEVER, consider non-financial factors:")
        print("  ⚠ Urban grid capacity - can 4 stations each get 15-25 kW?")
        print("  ⚠ Urban land availability and zoning")
        print("  ⚠ Operational complexity of managing 4 charging locations")
        print()
        if abs(total_diff) < 100000:
            print("RECOMMENDATION: CENTRALIZED despite higher cost because:")
            print(f"  • Cost difference (${abs(total_diff):,}) is small relative to total investment")
            print("  • Grid risk in urban Rwanda is HIGH")
            print("  • Operational simplicity has value not captured in model")
        else:
            print("RECOMMENDATION: DISTRIBUTED if:")
            print("  • You can secure reliable grid connections at all 4 stations")
            print("  • Urban land is available at reasonable cost")
            print("  • You have management capacity for distributed operations")
    else:
        print(f"💡 VERDICT: CENTRALIZED IS CHEAPER by ${abs(total_diff):,} over 5 years")
        print()
        print("RECOMMENDATION: CENTRALIZED - clear winner on both cost and practicality")

    print("=" * 100)

    return {
        'centralized': central,
        'distributed': distributed,
        'recommendation': 'centralized' if total_diff <= 0 or abs(total_diff) < 50000 else 'distributed'
    }


if __name__ == "__main__":
    results = run_comprehensive_analysis()
