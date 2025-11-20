"""
ANALYSIS: Should you switch from DISTRIBUTED to CENTRALIZED?
You currently have distributed charging - is centralized worth the investment?
"""

import pandas as pd
import numpy as np


def analyze_switching_decision():
    """
    Analyze whether switching from distributed to centralized makes sense
    """
    print("=" * 100)
    print("SWITCHING ANALYSIS: DISTRIBUTED (CURRENT) vs CENTRALIZED (PROPOSED)")
    print("Should you change your existing distributed setup to centralized?")
    print("=" * 100)
    print()

    print("YOUR CURRENT SITUATION:")
    print("  • You are operating DISTRIBUTED charging (at swapping stations)")
    print("  • You have 300 batteries, 100 charging ports")
    print("  • Considering switching to CENTRALIZED at industrial park")
    print()

    # Parameters
    battery_cost = 450
    charging_port_cost = 300

    print("SCENARIO 1: KEEP DISTRIBUTED (STATUS QUO)")
    print("-" * 100)

    # Current distributed setup
    current_batteries = 300
    current_ports = 100

    print(f"Current investment:")
    print(f"  • Batteries: {current_batteries} × ${battery_cost} = ${current_batteries * battery_cost:,}")
    print(f"  • Charging ports: {current_ports} × ${charging_port_cost} = ${current_ports * charging_port_cost:,}")
    print(f"  • Total sunk cost: ${current_batteries * battery_cost + current_ports * charging_port_cost:,}")
    print(f"  • Status: ALREADY PAID - no additional capex needed")
    print()

    # Annual costs for distributed
    annual_battery_replacement = 45625  # From earlier calculation
    annual_transport = 0  # No transport
    annual_facility = 5760  # Urban land
    annual_electricity = 97181  # ALREADY HAVE INDUSTRIAL RATES (no urban premium!)
    annual_staff = 28800  # 2 per station × 4 stations
    annual_maintenance = 5175

    annual_opex_distributed = (annual_battery_replacement + annual_transport +
                               annual_facility + annual_electricity +
                               annual_staff + annual_maintenance)

    print(f"Annual operating costs (distributed):")
    print(f"  • Battery replacements: ${annual_battery_replacement:,}")
    print(f"  • Transportation: $0 (no transport needed)")
    print(f"  • Facility/land: ${annual_facility:,}")
    print(f"  • Electricity: ${annual_electricity:,}")
    print(f"  • Staff: ${annual_staff:,}")
    print(f"  • Maintenance: ${annual_maintenance:,}")
    print(f"  • TOTAL ANNUAL: ${annual_opex_distributed:,}")
    print()

    print("SCENARIO 2: SWITCH TO CENTRALIZED")
    print("-" * 100)

    # Centralized requirements
    central_batteries = 337  # Need more due to transport
    central_ports = 69

    print(f"Required investment:")
    print(f"  • Batteries: {central_batteries} × ${battery_cost} = ${central_batteries * battery_cost:,}")
    print(f"  • Charging ports: {central_ports} × ${charging_port_cost} = ${central_ports * charging_port_cost:,}")
    print(f"  • Total required: ${central_batteries * battery_cost + central_ports * charging_port_cost:,}")
    print()

    # What you can reuse
    print(f"What you can reuse from current setup:")
    print(f"  • Batteries: {current_batteries} (need {central_batteries - current_batteries} more)")
    print(f"  • Charging ports: Depends on if you can relocate them")
    print()

    # Additional investment needed
    additional_batteries = central_batteries - current_batteries
    additional_batteries_cost = additional_batteries * battery_cost

    # Assume can't reuse distributed chargers (different location)
    new_chargers_cost = central_ports * charging_port_cost

    # What happens to old equipment?
    resale_value_old_chargers = current_ports * charging_port_cost * 0.5  # 50% resale

    switching_capex = additional_batteries_cost + new_chargers_cost - resale_value_old_chargers

    print(f"SWITCHING COST:")
    print(f"  • Additional {additional_batteries} batteries: ${additional_batteries_cost:,}")
    print(f"  • New charging infrastructure: ${new_chargers_cost:,}")
    print(f"  • Less: Resale of old chargers (50%): $-{resale_value_old_chargers:,}")
    print(f"  • NET SWITCHING COST: ${switching_capex:,}")
    print()

    # Annual costs for centralized
    annual_battery_replacement_central = 45625  # Same (battery lifespan same)
    annual_transport_central = 35040  # Need transport now
    annual_facility_central = 4140  # Cheaper industrial land
    annual_electricity_central = 97181  # Industrial rates
    annual_staff_central = 21600  # Fewer staff
    annual_maintenance_central = 3450

    annual_opex_central = (annual_battery_replacement_central + annual_transport_central +
                          annual_facility_central + annual_electricity_central +
                          annual_staff_central + annual_maintenance_central)

    print(f"Annual operating costs (centralized):")
    print(f"  • Battery replacements: ${annual_battery_replacement_central:,}")
    print(f"  • Transportation: ${annual_transport_central:,} (NEW COST)")
    print(f"  • Facility/land: ${annual_facility_central:,}")
    print(f"  • Electricity: ${annual_electricity_central:,}")
    print(f"  • Staff: ${annual_staff_central:,}")
    print(f"  • Maintenance: ${annual_maintenance_central:,}")
    print(f"  • TOTAL ANNUAL: ${annual_opex_central:,}")
    print()

    # Comparison
    print("FINANCIAL COMPARISON")
    print("=" * 100)

    annual_savings = annual_opex_distributed - annual_opex_central

    print(f"Annual operating cost savings (centralized): ${annual_savings:,}/year")
    print(f"Switching investment required: ${switching_capex:,}")

    if annual_savings > 0:
        payback_years = switching_capex / annual_savings
        print(f"Payback period: {payback_years:.1f} years")
        print()

        # 5-year analysis
        five_year_savings = (annual_savings * 5) - switching_capex
        print(f"5-YEAR ANALYSIS:")
        print(f"  • Distributed (keep current): ${annual_opex_distributed * 5:,}")
        print(f"  • Centralized (switch): ${switching_capex + (annual_opex_central * 5):,}")
        print(f"  • Net savings from switching: ${five_year_savings:,}")
        print()

        if five_year_savings > 0:
            print(f"✓ SWITCHING SAVES ${five_year_savings:,} over 5 years")
        else:
            print(f"✗ SWITCHING COSTS ${abs(five_year_savings):,} MORE over 5 years")
    else:
        print(f"⚠ Centralized has HIGHER operating costs by ${abs(annual_savings):,}/year")
        print(f"✗ Switching would increase both capex AND opex - NOT recommended")
        five_year_savings = -switching_capex + (annual_savings * 5)

    print()

    # Decision framework
    print("DECISION FRAMEWORK")
    print("=" * 100)
    print()

    print("REASONS TO STAY DISTRIBUTED (keep current setup):")
    print("  ✓ No switching cost - equipment already in place")
    print("  ✓ System is working - don't fix what isn't broken")
    print("  ✓ No transportation costs or logistics")
    print("  ✓ Fewer batteries needed (less capital tied up)")
    print("  ✓ More resilient (distributed failure modes)")
    print(f"  ✓ Avoid disruption to operations during transition")
    if five_year_savings < 50000:
        print(f"  ✓ Financial benefit of switching is small (${abs(five_year_savings):,} over 5 years)")
    print()

    print("REASONS TO SWITCH TO CENTRALIZED:")
    if annual_savings > 0:
        print(f"  ✓ Save ${annual_savings:,}/year in operating costs")
        if payback_years < 3:
            print(f"  ✓ Quick payback period ({payback_years:.1f} years)")
    print("  ✓ Easier management (single facility)")
    print("  ✓ Lower electricity costs (industrial rates)")
    print("  ✓ Cheaper land (if expanding)")
    print("  ✓ Better for scaling if adding more stations later")
    print()

    # Risk analysis
    print("RISK ANALYSIS")
    print("=" * 100)
    print()

    print("RISKS OF SWITCHING:")
    print("  ⚠ Operational disruption during transition")
    print("  ⚠ Need to build new central facility")
    print(f"  ⚠ Upfront investment: ${switching_capex:,}")
    print("  ⚠ Transportation dependency (vehicle breakdowns, fuel costs)")
    print("  ⚠ Battery logistics complexity")
    print("  ⚠ Single point of failure (if central hub goes down)")
    print()

    print("RISKS OF STAYING DISTRIBUTED:")
    print("  ⚠ Higher operating costs continue")
    print("  ⚠ More complex to scale (need grid at each new station)")
    print("  ⚠ Urban electricity premiums may increase")
    print("  ⚠ More staff management complexity")
    print()

    # Final recommendation
    print("FINAL RECOMMENDATION")
    print("=" * 100)
    print()

    if five_year_savings > 50000 and payback_years < 3:
        print(f"💡 CONSIDER SWITCHING TO CENTRALIZED")
        print(f"   • 5-year savings: ${five_year_savings:,}")
        print(f"   • Payback: {payback_years:.1f} years")
        print(f"   • Benefits justify the transition effort")
    elif five_year_savings > 0:
        print(f"💡 MARGINAL CASE - PROBABLY STAY DISTRIBUTED")
        print(f"   • 5-year savings from switching: ${five_year_savings:,}")
        print(f"   • Savings are modest relative to disruption risk")
        print(f"   • Consider centralized only if expanding significantly")
    else:
        print(f"💡 STAY DISTRIBUTED (CURRENT SETUP)")
        print(f"   • Switching would cost ${abs(five_year_savings):,} MORE over 5 years")
        print(f"   • Current system is working")
        print(f"   • Not worth the disruption and investment")

    print()
    print("ALTERNATIVE: Hybrid Approach")
    print("-" * 100)
    print("Consider keeping distributed for current 4 stations, but:")
    print("  • When you expand beyond 6-8 stations, add centralized hub")
    print("  • Use centralized for NEW stations (industrial park)")
    print("  • Keep existing distributed stations as-is (already sunk cost)")
    print("  • This maximizes existing investment while capturing centralized benefits for growth")
    print()
    print("=" * 100)

    return {
        'switching_cost': switching_capex,
        'annual_savings': annual_savings,
        'payback_years': payback_years if annual_savings > 0 else None,
        'five_year_savings': five_year_savings,
        'recommendation': 'switch' if five_year_savings > 50000 and payback_years < 3
                         else 'stay_distributed'
    }


if __name__ == "__main__":
    results = analyze_switching_decision()
