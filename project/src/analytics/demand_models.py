"""
Demand Modeling Module

Functions for estimating demand curves and price elasticities.

Author: NUS Student
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import statsmodels.api as sm
from config import MIN_PURCHASES_PER_SEGMENT


def estimate_demand_curve(segment_data, price_col='price', quantity_col='quantity',
                          method='log-log'):
    """
    Estimate demand curve for a customer segment.

    Args:
        segment_data (pd.DataFrame): Purchase data for one segment
        price_col (str): Column name for price
        quantity_col (str): Column name for quantity purchased
        method (str): 'log-log' for constant elasticity, 'linear' for linear demand

    Returns:
        dict: {'model': fitted_model,
               'elasticity': price_elasticity,
               'r_squared': goodness_of_fit,
               'params': model_parameters}

    Example:
        >>> result = estimate_demand_curve(segment1_data)
        >>> print(f"Elasticity: {result['elasticity']:.2f}")

    TODO:
        - Check if segment has enough data (MIN_PURCHASES_PER_SEGMENT)
        - For log-log: estimate log(Q) = a + b*log(P)
          - Elasticity = b (coefficient on log(price))
        - For linear: estimate Q = a + b*P
          - Elasticity = (b * P) / Q (varies by price)
        - Use statsmodels for diagnostics (p-values, residuals)
        - Return model object and key metrics
    """
    # TODO: Implement demand estimation
    # if len(segment_data) < MIN_PURCHASES_PER_SEGMENT:
    #     raise ValueError("Insufficient data for estimation")

    # if method == 'log-log':
    #     # Take logs
    #     X = np.log(segment_data[[price_col]])
    #     y = np.log(segment_data[quantity_col])
    #
    #     # Add constant for intercept
    #     X = sm.add_constant(X)
    #
    #     # Fit OLS
    #     model = sm.OLS(y, X).fit()
    #
    #     # Elasticity is the coefficient on log(price)
    #     elasticity = model.params[1]
    #
    #     return {
    #         'model': model,
    #         'elasticity': elasticity,
    #         'r_squared': model.rsquared,
    #         'params': model.params
    #     }

    pass


def predict_demand(prices, demand_params, method='log-log'):
    """
    Predict quantity demanded at given prices using fitted demand model.

    Args:
        prices (array-like): Prices to evaluate
        demand_params (dict): Parameters from estimate_demand_curve()
        method (str): Same as used in estimation

    Returns:
        np.array: Predicted quantities

    Example:
        >>> params = estimate_demand_curve(segment_data)
        >>> quantities = predict_demand([10, 20, 30], params)

    TODO:
        - Extract parameters from demand_params
        - Apply demand function (log-log or linear)
        - Return predictions
    """
    # TODO: Implement prediction
    pass


def calculate_price_elasticity(segment_data, price_col='price', quantity_col='quantity'):
    """
    Calculate price elasticity of demand for a segment.

    Price elasticity = (% change in quantity) / (% change in price)
                     = (dQ/dP) * (P/Q)

    Args:
        segment_data (pd.DataFrame): Purchase data
        price_col (str): Price column
        quantity_col (str): Quantity column

    Returns:
        float: Price elasticity (typically negative)

    Example:
        >>> elasticity = calculate_price_elasticity(segment_data)
        >>> print(f"A 1% price increase leads to {-elasticity:.2f}% demand decrease")

    TODO:
        - Estimate demand curve
        - Extract elasticity from model
        - Validate elasticity is negative and reasonable
    """
    result = estimate_demand_curve(segment_data, price_col, quantity_col)
    return result['elasticity']


def validate_demand_model(model_result, segment_data, price_col='price', quantity_col='quantity'):
    """
    Validate demand model with diagnostics.

    Args:
        model_result (dict): Output from estimate_demand_curve()
        segment_data (pd.DataFrame): Data used for estimation
        price_col (str): Price column
        quantity_col (str): Quantity column

    Returns:
        dict: Validation metrics
            - 'r_squared': Goodness of fit
            - 'p_value': Statistical significance
            - 'residuals': Model residuals
            - 'heteroskedasticity_test': Test result

    TODO:
        - Check R-squared (> 0.3 is reasonable)
        - Check p-value (< 0.05 for significance)
        - Plot residuals vs fitted values
        - Test for heteroskedasticity
        - Check if elasticity makes economic sense
    """
    # TODO: Implement validation
    pass


def segment_demand_comparison(clustered_data, segment_col='segment'):
    """
    Compare demand elasticities across all segments.

    Args:
        clustered_data (pd.DataFrame): Data with segment labels
        segment_col (str): Column for segment labels

    Returns:
        pd.DataFrame: Elasticity estimates per segment

    Example:
        >>> comparison = segment_demand_comparison(data)
        >>> print(comparison)
        #   segment  elasticity  r_squared  sample_size
        # 0       0       -1.2       0.45         5000
        # 1       1       -2.5       0.52         3000
        # 2       2       -0.8       0.38         2000

    TODO:
        - Loop through each segment
        - Estimate demand curve for each
        - Compile results into dataframe
        - Validate ranking makes sense (premium less elastic than budget)
    """
    # TODO: Implement comparison
    pass
