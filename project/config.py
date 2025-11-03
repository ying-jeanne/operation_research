"""
Configuration file for Segmentation Strategy Project.

All parameters centralized here for easy modification and consistency
across notebooks and modules.

Author: NUS Student
Course: Operations Research + Business Analytics + Microeconomics
"""

import os

# ============================================
# PROJECT PATHS
# ============================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
RESULTS_DIR = os.path.join(PROJECT_DIR, 'results')
FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')
TABLES_DIR = os.path.join(RESULTS_DIR, 'tables')
SENSITIVITY_DIR = os.path.join(RESULTS_DIR, 'sensitivity')

# ============================================
# DATA FILES (Olist Dataset)
# ============================================
OLIST_FILES = {
    'customers': 'olist_customers_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'geolocation': 'olist_geolocation_dataset.csv',
    'reviews': 'olist_order_reviews_dataset.csv',
    'category_translation': 'product_category_name_translation.csv'
}

# ============================================
# SEGMENTATION PARAMETERS
# ============================================
K_VALUES = [1, 2, 3, 4, 5]          # Number of segments to test
RANDOM_STATE = 42                    # For reproducibility (clustering, train/test split)

# RFM Calculation
ANALYSIS_DATE = '2018-09-01'         # Reference date for recency calculation

# ============================================
# COST PARAMETERS (in USD)
# ============================================

# Full A/B Testing Costs (Strategy A)
# Includes: test design, implementation, analysis, opportunity cost
AB_TESTING_COSTS = {
    1: 0,          # Single price (no testing needed)
    2: 50000,      # Test 2 segments (3 price points each = 6 tests)
    3: 100000,     # Test 3 segments (9 tests)
    4: 150000,     # Test 4 segments (12 tests)
    5: 200000      # Test 5 segments (15 tests)
}

# Light A/B Testing Costs (Strategy C - Hybrid)
# Smaller sample, shorter duration, less precision
LIGHT_AB_COST_MULTIPLIER = 0.3       # 30% of full A/B cost

# Segmentation Setup Costs (one-time)
# Includes: website changes, system integration, staff training
SETUP_COSTS = {
    1: 0,          # No segmentation
    2: 30000,      # Split into 2 tiers
    3: 50000,      # 3 tiers
    4: 80000,      # 4 tiers (increased complexity)
    5: 120000      # 5 tiers (high complexity)
}

# Annual Operating Costs per Segment
# Includes: marketing campaigns, customer support, analytics
OPERATING_COST_PER_SEGMENT = 25000   # Per segment per year

# Marginal Cost (production cost per unit)
MARGINAL_COST = 30                   # Assumed constant marginal cost

# ============================================
# OPTIMIZATION PARAMETERS
# ============================================

# Time Horizons for NPV Calculation
TIME_HORIZONS = [1, 2, 3, 5]         # Years to evaluate strategies

# Discount Rate for NPV
DISCOUNT_RATE = 0.10                 # 10% annual discount rate

# Adaptive Learning Simulation
N_PERIODS_ADAPTIVE = 4               # Number of periods (quarters) for Strategy B
QUARTERS_PER_YEAR = 4

# Price Bounds (for optimization)
PRICE_MIN = 10                       # Minimum price allowed
PRICE_MAX = 500                      # Maximum price allowed

# Demand Estimation
MIN_PURCHASES_PER_SEGMENT = 50       # Minimum sample size for elasticity estimation

# ============================================
# BAYESIAN LEARNING PARAMETERS (Strategy B)
# ============================================

# Prior beliefs about demand elasticity
PRIOR_ELASTICITY_MEAN = -2.0         # Expected elasticity (negative)
PRIOR_ELASTICITY_STD = 0.5           # Uncertainty in prior

# Learning rate (how fast beliefs update)
BAYESIAN_LEARNING_RATE = 0.3         # 0 = no learning, 1 = full update

# ============================================
# SENSITIVITY ANALYSIS PARAMETERS
# ============================================

SENSITIVITY_PARAMS = {
    # A/B testing cost variations
    'ab_cost_multipliers': [0.5, 1.0, 1.5, 2.0],

    # Discount rate variations
    'discount_rates': [0.05, 0.10, 0.15, 0.20],

    # Time horizon variations
    'time_horizons': [1, 2, 3, 4, 5, 7, 10],

    # Customer base size (for learning speed)
    'customer_base_sizes': [5000, 10000, 50000, 100000, 500000],

    # Demand volatility (coefficient of variation)
    'demand_volatility': [0.1, 0.2, 0.3, 0.5]
}

# ============================================
# VISUALIZATION PARAMETERS
# ============================================

# Color palette for segments
SEGMENT_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']

# Figure sizes
FIGURE_SIZE_SMALL = (8, 6)
FIGURE_SIZE_MEDIUM = (12, 8)
FIGURE_SIZE_LARGE = (16, 10)

# DPI for saving figures
FIGURE_DPI = 300

# ============================================
# DECISION FRAMEWORK THRESHOLDS
# ============================================

# When to recommend each strategy
RECOMMENDATION_THRESHOLDS = {
    'time_horizon_short': 2,         # Years (below this → favor A/B testing)
    'time_horizon_long': 3,          # Years (above this → favor adaptive)
    'customer_base_small': 10000,    # Customers (below this → A/B difficult)
    'customer_base_large': 100000,   # Customers (above this → fast learning)
    'npv_difference_threshold': 0.05 # 5% difference → strategies equivalent
}

# ============================================
# COMPUTATIONAL PARAMETERS
# ============================================

# Optimization solver settings
SOLVER_TIME_LIMIT = 300              # Maximum seconds per optimization
SOLVER_TOLERANCE = 1e-4              # Optimality tolerance

# Parallel processing
N_JOBS = -1                          # Use all available CPU cores (-1)

# ============================================
# REPORTING PARAMETERS
# ============================================

# Decimal places for rounding
DECIMALS_PRICE = 2
DECIMALS_ELASTICITY = 3
DECIMALS_NPV = 0                     # Whole dollars

# Significance level for statistical tests
ALPHA = 0.05                         # 5% significance level

# ============================================
# VALIDATION
# ============================================

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR,
                  RESULTS_DIR, FIGURES_DIR, TABLES_DIR, SENSITIVITY_DIR]:
    os.makedirs(directory, exist_ok=True)

# Print confirmation when imported
if __name__ == '__main__':
    print("Configuration loaded successfully!")
    print(f"Project directory: {PROJECT_DIR}")
    print(f"K values to test: {K_VALUES}")
    print(f"Time horizons: {TIME_HORIZONS}")
    print(f"A/B testing costs: {AB_TESTING_COSTS}")
