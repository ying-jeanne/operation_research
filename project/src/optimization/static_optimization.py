"""
Strategy A: Static Segmentation with A/B Testing

Optimize prices assuming perfect demand knowledge from A/B testing.

Author: NUS Student
"""

import numpy as np
from scipy.optimize import minimize
from config import PRICE_MIN, PRICE_MAX, MARGINAL_COST


def optimize_static_pricing(k, segment_data, demand_functions):
    """
    Find optimal prices for k segments given known demand curves.

    This is Strategy A: We paid for A/B testing, so we know demand perfectly.
    Now optimize prices to maximize profit.

    Args:
        k (int): Number of segments
        segment_data (list of dict): Each dict has 'size' (number of customers)
        demand_functions (list of functions): D_i(p) for each segment i

    Returns:
        dict: {
            'optimal_prices': [p1, p2, ..., pk],
            'optimal_profit': float,
            'quantities': [q1, q2, ..., qk],
            'revenues': [r1, r2, ..., rk]
        }

    Example:
        >>> # Assume we have 3 segments with different demand curves
        >>> segments = [
        ...     {'size': 10000},
        ...     {'size': 5000},
        ...     {'size': 2000}
        ... ]
        >>> def demand_1(p): return 100 - 0.5*p  # Price-sensitive
        >>> def demand_2(p): return 80 - 0.3*p   # Medium
        >>> def demand_3(p): return 50 - 0.1*p   # Premium (less elastic)
        >>> demands = [demand_1, demand_2, demand_3]
        >>>
        >>> result = optimize_static_pricing(k=3, segments, demands)
        >>> print(result['optimal_prices'])

    TODO:
        - Define profit function: sum over segments of (p_i - c) * D_i(p_i) * N_i
        - Use scipy.optimize.minimize to find optimal prices
        - Constraints: PRICE_MIN <= p_i <= PRICE_MAX
        - Constraint: p_i >= MARGINAL_COST (no below-cost pricing)
        - Calculate quantities and revenues at optimal prices
    """
    # TODO: Implement optimization
    # def profit_function(prices):
    #     total_profit = 0
    #     for i in range(k):
    #         p_i = prices[i]
    #         q_i = demand_functions[i](p_i)
    #         n_i = segment_data[i]['size']
    #         profit_i = (p_i - MARGINAL_COST) * q_i * n_i
    #         total_profit += profit_i
    #     return -total_profit  # Negative because scipy minimizes
    #
    # # Initial guess: midpoint of price range
    # x0 = np.array([50.0] * k)
    #
    # # Bounds for each price
    # bounds = [(PRICE_MIN, PRICE_MAX) for _ in range(k)]
    #
    # # Optimize
    # result = minimize(profit_function, x0, bounds=bounds, method='L-BFGS-B')
    #
    # optimal_prices = result.x
    # optimal_profit = -result.fun  # Convert back to positive
    #
    # # Calculate quantities and revenues
    # quantities = [demand_functions[i](optimal_prices[i]) for i in range(k)]
    # revenues = [optimal_prices[i] * quantities[i] * segment_data[i]['size'] for i in range(k)]
    #
    # return {
    #     'optimal_prices': optimal_prices,
    #     'optimal_profit': optimal_profit,
    #     'quantities': quantities,
    #     'revenues': revenues
    # }

    pass


def find_best_k_static(segment_data_all_k, demand_functions_all_k, cost_function):
    """
    Find optimal number of segments for Strategy A.

    Args:
        segment_data_all_k (dict): {k: segment_data} for each k
        demand_functions_all_k (dict): {k: demand_functions} for each k
        cost_function (function): Returns cost for given k

    Returns:
        dict: {
            'optimal_k': int,
            'optimal_prices': list,
            'net_profit': float,
            'comparison': DataFrame with all k results
        }

    TODO:
        - For each k in [1, 2, 3, 4, 5]:
            - Optimize prices
            - Calculate profit - cost(k)
        - Select k with highest net profit
        - Return comparison table
    """
    # TODO: Implement
    pass


def calculate_npv_static(k, optimal_prices, segment_data, demand_functions,
                         time_horizon, discount_rate):
    """
    Calculate Net Present Value for Strategy A over time horizon.

    Args:
        k (int): Number of segments
        optimal_prices (list): Optimal prices from optimization
        segment_data (list): Segment information
        demand_functions (list): Demand functions
        time_horizon (int): Number of years
        discount_rate (float): Annual discount rate (e.g., 0.10 for 10%)

    Returns:
        float: NPV in dollars

    Notes:
        - Strategy A has constant profit each period (prices don't change)
        - NPV = sum over t of [Profit_t / (1 + r)^t]

    TODO:
        - Calculate single-period profit
        - Discount over time_horizon
        - Subtract upfront A/B testing cost
    """
    # TODO: Implement
    pass
