"""
Cost Modeling Module

Functions for calculating segmentation costs (setup, operating, A/B testing).

Author: NUS Student
"""

from config import (AB_TESTING_COSTS, SETUP_COSTS, OPERATING_COST_PER_SEGMENT,
                     LIGHT_AB_COST_MULTIPLIER)


def segmentation_cost(k, include_ab_testing=True, light_ab=False):
    """
    Calculate total cost of implementing k segments.

    Args:
        k (int): Number of segments
        include_ab_testing (bool): Include A/B testing cost (Strategy A)
        light_ab (bool): Use light A/B testing (Strategy C)

    Returns:
        float: Total cost in dollars

    Example:
        >>> cost_strategy_a = segmentation_cost(k=3, include_ab_testing=True)
        >>> cost_strategy_b = segmentation_cost(k=3, include_ab_testing=False)
        >>> cost_strategy_c = segmentation_cost(k=3, include_ab_testing=True, light_ab=True)

    Components:
        - Setup cost (one-time): Infrastructure, website, training
        - A/B testing (if included): Experimentation cost
        - Operating costs handled separately (annual)
    """
    # Setup cost
    setup = SETUP_COSTS.get(k, 0)

    # A/B testing cost
    ab_cost = 0
    if include_ab_testing:
        ab_cost = AB_TESTING_COSTS.get(k, 0)
        if light_ab:
            ab_cost *= LIGHT_AB_COST_MULTIPLIER

    return setup + ab_cost


def annual_operating_cost(k):
    """
    Calculate annual operating cost for k segments.

    Args:
        k (int): Number of segments

    Returns:
        float: Annual cost in dollars

    Components:
        - Marketing campaigns per segment
        - Customer support per segment
        - Analytics and monitoring per segment
    """
    return k * OPERATING_COST_PER_SEGMENT


def total_cost_over_time(k, time_horizon, include_ab_testing=True, light_ab=False):
    """
    Calculate total cost over multiple periods.

    Args:
        k (int): Number of segments
        time_horizon (int): Number of years
        include_ab_testing (bool): Include upfront A/B cost
        light_ab (bool): Use light A/B testing

    Returns:
        float: Total discounted cost

    Example:
        >>> total_5yr = total_cost_over_time(k=3, time_horizon=5, include_ab_testing=True)
    """
    # One-time costs (setup + A/B testing)
    one_time = segmentation_cost(k, include_ab_testing, light_ab)

    # Annual operating costs
    annual = annual_operating_cost(k)

    # Total = one-time + (annual × time_horizon)
    return one_time + (annual * time_horizon)


def marginal_cost_of_adding_segment(current_k, include_ab_delta=True):
    """
    Calculate marginal cost of going from k to k+1 segments.

    Args:
        current_k (int): Current number of segments
        include_ab_delta (bool): Include additional A/B testing cost

    Returns:
        float: Incremental cost

    Example:
        >>> # How much does it cost to go from 2 to 3 segments?
        >>> marginal = marginal_cost_of_adding_segment(current_k=2)

    TODO:
        - Calculate cost(k+1) - cost(k)
        - Include both setup and A/B testing differences
    """
    # TODO: Implement
    pass


def cost_sensitivity_analysis(k_range, ab_cost_multipliers):
    """
    Analyze how costs vary with different assumptions.

    Args:
        k_range (list): Values of k to test
        ab_cost_multipliers (list): Multipliers for A/B cost (e.g., [0.5, 1.0, 2.0])

    Returns:
        pd.DataFrame: Cost matrix

    Example:
        >>> import pandas as pd
        >>> costs = cost_sensitivity_analysis([1,2,3,4], [0.5, 1.0, 1.5])
        >>> print(costs)

    TODO:
        - Create matrix of costs for each (k, multiplier) combination
        - Return as dataframe for easy visualization
    """
    # TODO: Implement
    pass
