"""
Data Processing Module

Functions for loading, cleaning, and preparing Olist e-commerce data.

Author: NUS Student
"""

import pandas as pd
import numpy as np
import os
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, OLIST_FILES, ANALYSIS_DATE


def load_olist_data():
    """
    Load all Olist CSV files and return as dictionary.

    Returns:
        dict: Keys are table names (e.g., 'customers', 'orders'),
              values are pandas DataFrames

    Example:
        >>> data = load_olist_data()
        >>> customers = data['customers']
        >>> orders = data['orders']

    TODO:
        - Implement file loading using OLIST_FILES from config
        - Handle FileNotFoundError if data not downloaded
        - Print confirmation of loaded tables
    """
    data = {}

    # TODO: Loop through OLIST_FILES and load each CSV
    # for table_name, filename in OLIST_FILES.items():
    #     filepath = os.path.join(RAW_DATA_DIR, filename)
    #     data[table_name] = pd.read_csv(filepath)
    #     print(f"Loaded {table_name}: {data[table_name].shape}")

    return data


def merge_order_data(data_dict):
    """
    Merge Olist tables into single complete order dataset.

    Args:
        data_dict (dict): Output from load_olist_data()

    Returns:
        pd.DataFrame: Merged dataset with:
            - Order details (date, status)
            - Item details (price, quantity, product)
            - Customer details (location)
            - Payment details (method, value)

    Example:
        >>> data = load_olist_data()
        >>> orders_complete = merge_order_data(data)
        >>> print(orders_complete.columns)

    TODO:
        - Start with orders table as base
        - Join order_items (on order_id)
        - Join customers (on customer_id)
        - Join payments (on order_id)
        - Join products (on product_id)
        - Handle duplicate columns (e.g., price in items vs payments)
        - Drop unnecessary columns
    """
    # TODO: Implement merging logic
    # orders = data_dict['orders']
    # orders_complete = orders.merge(data_dict['order_items'], ...)

    pass


def calculate_rfm(orders_df,
                  customer_id_col='customer_unique_id',
                  date_col='order_purchase_timestamp',
                  value_col='payment_value'):
    """
    Calculate RFM (Recency, Frequency, Monetary) features for each customer.

    Args:
        orders_df (pd.DataFrame): Order-level data
        customer_id_col (str): Column name for customer identifier
        date_col (str): Column name for order date
        value_col (str): Column name for order value

    Returns:
        pd.DataFrame: Customer-level DataFrame with columns:
            - customer_id
            - recency: Days since last purchase (lower is better)
            - frequency: Number of orders (higher is better)
            - monetary: Total or average spending (higher is better)

    Example:
        >>> rfm = calculate_rfm(orders, 'customer_id', 'order_date', 'price')
        >>> print(rfm.head())

    TODO:
        - Convert date_col to datetime if needed
        - Group by customer_id
        - Recency: (ANALYSIS_DATE - max(date)) in days
        - Frequency: count of orders
        - Monetary: sum or mean of value (choose one)
        - Handle edge cases (single purchase customers)
    """
    # TODO: Implement RFM calculation
    # Make sure date_col is datetime
    # orders_df[date_col] = pd.to_datetime(orders_df[date_col])

    # Calculate for each customer
    # rfm = orders_df.groupby(customer_id_col).agg({
    #     date_col: lambda x: (pd.to_datetime(ANALYSIS_DATE) - x.max()).days,
    #     customer_id_col: 'count',
    #     value_col: 'sum'
    # })

    pass


def clean_data(df):
    """
    Clean and validate dataframe.

    Args:
        df (pd.DataFrame): Raw data

    Returns:
        pd.DataFrame: Cleaned data

    TODO:
        - Remove duplicates
        - Handle missing values
        - Remove outliers (optional)
        - Validate data types
        - Filter invalid records (e.g., negative prices)
    """
    # TODO: Implement data cleaning
    pass


def save_processed_data(df, filename):
    """
    Save processed data to CSV.

    Args:
        df (pd.DataFrame): Data to save
        filename (str): Output filename (e.g., 'orders_complete.csv')

    Example:
        >>> save_processed_data(orders_complete, 'orders_complete.csv')
    """
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"Saved to {filepath}")


def load_processed_data(filename):
    """
    Load previously processed data.

    Args:
        filename (str): Filename in processed data directory

    Returns:
        pd.DataFrame: Loaded data

    Example:
        >>> orders = load_processed_data('orders_complete.csv')
    """
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    return pd.read_csv(filepath)
