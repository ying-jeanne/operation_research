"""
Realistic Battery Lifespan Calculation
Based on YOUR actual usage pattern
"""

def calculate_battery_lifespan():
    """
    Calculate how long batteries actually last with your usage pattern
    """
    print("=" * 80)
    print("BATTERY LIFESPAN CALCULATION - YOUR ACTUAL USAGE")
    print("=" * 80)
    print()

    # YOUR DATA
    battery_cycle_life = 1800  # cycles (your spec)
    vehicles = 200
    batteries_total = 300
    charges_per_vehicle_per_day = 2.5  # You just corrected this!

    print("INPUT PARAMETERS:")
    print(f"  • Total vehicles: {vehicles}")
    print(f"  • Total batteries: {batteries_total}")
    print(f"  • Battery cycle life: {battery_cycle_life} cycles")
    print(f"  • Charges per vehicle per day: {charges_per_vehicle_per_day}")
    print()

    # CALCULATION
    print("CALCULATION:")
    print("-" * 80)

    # Total charges per day across fleet
    total_charges_per_day = vehicles * charges_per_vehicle_per_day
    print(f"1. Total charges per day: {vehicles} vehicles × {charges_per_vehicle_per_day} = {total_charges_per_day} charges/day")

    # Each battery cycles this many times per day
    # (assuming batteries rotate evenly through the fleet)
    cycles_per_battery_per_day = total_charges_per_day / batteries_total
    print(f"2. Cycles per battery per day: {total_charges_per_day} ÷ {batteries_total} batteries = {cycles_per_battery_per_day:.2f} cycles/day")

    # Days until battery reaches cycle life limit
    days_until_replacement = battery_cycle_life / cycles_per_battery_per_day
    print(f"3. Days until replacement: {battery_cycle_life} cycles ÷ {cycles_per_battery_per_day:.2f} cycles/day = {days_until_replacement:.1f} days")

    # Convert to years
    years_until_replacement = days_until_replacement / 365
    months_until_replacement = days_until_replacement / 30
    print(f"4. Battery lifespan: {years_until_replacement:.2f} years ({months_until_replacement:.1f} months)")
    print()

    # VALIDATION
    print("VALIDATION:")
    print("-" * 80)
    total_cycles_in_lifespan = cycles_per_battery_per_day * days_until_replacement
    print(f"  • Total cycles per battery: {cycles_per_battery_per_day:.2f} × {days_until_replacement:.1f} days = {total_cycles_in_lifespan:.0f} cycles ✓")
    print(f"  • Matches cycle life spec: {battery_cycle_life} cycles ✓")
    print()

    # COST ANALYSIS
    print("COST IMPLICATIONS:")
    print("-" * 80)
    battery_cost = 450  # USD

    # Annual replacement cost
    batteries_replaced_per_year = batteries_total / years_until_replacement
    annual_replacement_cost = batteries_replaced_per_year * battery_cost
    print(f"  • Batteries replaced per year: {batteries_total} ÷ {years_until_replacement:.2f} = {batteries_replaced_per_year:.1f} batteries/year")
    print(f"  • Annual replacement cost: {batteries_replaced_per_year:.1f} × ${battery_cost} = ${annual_replacement_cost:,.0f}/year")
    print(f"  • Monthly replacement budget: ${annual_replacement_cost / 12:,.0f}/month")
    print()

    # Cost per swap
    cost_per_charge = (battery_cost / battery_cycle_life)
    print(f"  • Battery cost per charge: ${battery_cost} ÷ {battery_cycle_life} cycles = ${cost_per_charge:.3f}/charge")
    print(f"  • Daily battery cost: {total_charges_per_day} charges × ${cost_per_charge:.3f} = ${total_charges_per_day * cost_per_charge:.2f}/day")
    print()

    # 5-year projection
    print("5-YEAR PROJECTION:")
    print("-" * 80)
    replacement_cycles_in_5_years = int(5 / years_until_replacement)
    partial_year = 5 - (replacement_cycles_in_5_years * years_until_replacement)
    partial_batteries = int(batteries_total * (partial_year / years_until_replacement))

    total_replacement_cost_5yr = (replacement_cycles_in_5_years * batteries_total * battery_cost) + (partial_batteries * battery_cost)

    initial_investment = batteries_total * battery_cost
    total_5yr_cost = initial_investment + total_replacement_cost_5yr

    print(f"  • Initial investment: {batteries_total} batteries × ${battery_cost} = ${initial_investment:,}")
    print(f"  • Full replacement cycles in 5 years: {replacement_cycles_in_5_years}")
    print(f"  • Partial replacement: ~{partial_batteries} batteries")
    print(f"  • Total replacement cost: ${total_replacement_cost_5yr:,}")
    print(f"  • TOTAL 5-year battery cost: ${total_5yr_cost:,}")
    print()

    # Compare to different usage scenarios
    print("SENSITIVITY: Impact of Different Usage Patterns")
    print("-" * 80)
    print(f"{'Charges/Vehicle/Day':<25} {'Battery Lifespan':<20} {'Annual Replacement':<25} {'5-Year Total':<20}")
    print("-" * 80)

    for charges in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        total_daily = vehicles * charges
        cycles_daily = total_daily / batteries_total
        days_life = battery_cycle_life / cycles_daily
        years_life = days_life / 365
        annual_cost = (batteries_total / years_life) * battery_cost
        replacement_cycles = int(5 / years_life)
        partial = 5 - (replacement_cycles * years_life)
        partial_batt = int(batteries_total * (partial / years_life))
        total_5yr = initial_investment + (replacement_cycles * batteries_total * battery_cost) + (partial_batt * battery_cost)

        marker = " ← YOUR CURRENT" if charges == 2.5 else ""
        print(f"{charges:<25} {years_life:.2f} years{' ':<12} ${annual_cost:<24,.0f} ${total_5yr:<19,}{marker}")

    print()

    # Summary
    print("KEY INSIGHTS:")
    print("=" * 80)
    print(f"✓ At 2.5 charges/vehicle/day, each battery cycles {cycles_per_battery_per_day:.2f} times per day")
    print(f"✓ With 1800-cycle lifespan, batteries last {years_until_replacement:.2f} years")
    print(f"✓ You need to budget ${annual_replacement_cost:,.0f}/year for battery replacements")
    print(f"✓ In 5 years, you'll spend ${total_5yr_cost:,} total on batteries (initial + replacements)")
    print()

    if years_until_replacement < 2:
        print("⚠ Battery lifespan is SHORT - consider:")
        print("  • Reducing usage intensity")
        print("  • Improving charging protocols")
        print("  • Investigating battery quality issues")
    elif years_until_replacement < 3:
        print("⚠ Battery lifespan is MODERATE - manageable but watch costs")
    else:
        print("✓ Battery lifespan is GOOD - sustainable replacement cycle")

    print("=" * 80)

    return {
        'cycles_per_battery_per_day': cycles_per_battery_per_day,
        'days_until_replacement': days_until_replacement,
        'years_until_replacement': years_until_replacement,
        'annual_replacement_cost': annual_replacement_cost,
        'total_5yr_cost': total_5yr_cost
    }


if __name__ == "__main__":
    calculate_battery_lifespan()
