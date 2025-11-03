"""
Customer Segmentation Module

Functions for clustering customers using K-means and validating segments.

Author: NUS Student
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns
from config import K_VALUES, RANDOM_STATE, FIGURES_DIR
import os


def cluster_customers(customer_features, k=3, features=['recency', 'frequency', 'monetary']):
    """
    Perform K-means clustering on customer RFM features.

    Args:
        customer_features (pd.DataFrame): Customer-level data with RFM columns
        k (int): Number of clusters
        features (list): Column names to use for clustering

    Returns:
        tuple: (clustered_df, kmeans_model, scaler)
            - clustered_df: Original data with 'segment' column added
            - kmeans_model: Fitted KMeans object
            - scaler: Fitted StandardScaler object

    Example:
        >>> df, model, scaler = cluster_customers(rfm_data, k=3)
        >>> print(df['segment'].value_counts())

    TODO:
        - Extract features from dataframe
        - Standardize features (important! RFM have different scales)
        - Fit K-means with k clusters
        - Add segment labels to original dataframe
        - Return all three objects
    """
    # TODO: Implement clustering
    # X = customer_features[features].copy()

    # Standardize (mean=0, std=1)
    # scaler = StandardScaler()
    # X_scaled = scaler.fit_transform(X)

    # Cluster
    # kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    # customer_features['segment'] = kmeans.fit_predict(X_scaled)

    # return customer_features, kmeans, scaler
    pass


def find_optimal_k(customer_features, features=['recency', 'frequency', 'monetary'],
                   k_range=None, plot=True):
    """
    Find optimal number of clusters using elbow method and silhouette score.

    Args:
        customer_features (pd.DataFrame): Customer data
        features (list): Features to use for clustering
        k_range (list): Values of k to test (default: from config)
        plot (bool): Whether to create plots

    Returns:
        dict: Metrics for each k value
            {'k': [2,3,4,5],
             'inertia': [...],
             'silhouette': [...],
             'davies_bouldin': [...]}

    Example:
        >>> metrics = find_optimal_k(rfm_data)
        >>> best_k = metrics['silhouette'].index(max(metrics['silhouette']))

    TODO:
        - Loop through k values
        - For each k, fit K-means
        - Calculate: inertia (within-cluster sum of squares)
        - Calculate: silhouette score (higher is better)
        - Calculate: Davies-Bouldin index (lower is better)
        - Plot all three metrics if plot=True
    """
    if k_range is None:
        k_range = K_VALUES

    metrics = {
        'k': [],
        'inertia': [],
        'silhouette': [],
        'davies_bouldin': []
    }

    # TODO: Implement metric calculation for each k
    # for k in k_range:
    #     df, kmeans, scaler = cluster_customers(customer_features, k, features)
    #     metrics['k'].append(k)
    #     metrics['inertia'].append(kmeans.inertia_)
    #     if k > 1:
    #         metrics['silhouette'].append(silhouette_score(...))
    #     ...

    # TODO: Create plots if requested

    return metrics


def analyze_segments(clustered_df, segment_col='segment',
                     features=['recency', 'frequency', 'monetary']):
    """
    Analyze characteristics of each segment.

    Args:
        clustered_df (pd.DataFrame): Data with segment labels
        segment_col (str): Column name for segment labels
        features (list): Features to summarize

    Returns:
        pd.DataFrame: Summary statistics per segment

    Example:
        >>> summary = analyze_segments(clustered_df)
        >>> print(summary)
        #         recency_mean  frequency_mean  monetary_mean  size
        # segment
        # 0              50.2            2.1           150.3   1000
        # 1             120.5            1.2            80.1   2000
        # 2              20.1            5.3           500.8    500

    TODO:
        - Group by segment
        - Calculate mean, median, std for each feature
        - Calculate segment size (count)
        - Create descriptive labels (e.g., "High-Value Loyal")
    """
    # TODO: Implement segment analysis
    # summary = clustered_df.groupby(segment_col)[features].agg(['mean', 'median', 'std'])
    # summary['size'] = clustered_df.groupby(segment_col).size()

    pass


def visualize_segments(clustered_df, segment_col='segment',
                       x_feature='frequency', y_feature='monetary',
                       save=False):
    """
    Create scatter plot of segments.

    Args:
        clustered_df (pd.DataFrame): Data with segment labels
        segment_col (str): Column for segment labels
        x_feature (str): Feature for x-axis
        y_feature (str): Feature for y-axis
        save (bool): Whether to save figure

    TODO:
        - Create scatter plot colored by segment
        - Add cluster centers if available
        - Label axes clearly
        - Add legend
        - Save to FIGURES_DIR if save=True
    """
    # TODO: Implement visualization
    pass


def assign_to_segment(new_customers, kmeans_model, scaler,
                      features=['recency', 'frequency', 'monetary']):
    """
    Assign new customers to existing segments.

    Args:
        new_customers (pd.DataFrame): New customer data
        kmeans_model: Fitted KMeans object
        scaler: Fitted StandardScaler object
        features (list): Features used in original clustering

    Returns:
        np.array: Segment assignments

    Example:
        >>> new_segments = assign_to_segment(new_data, model, scaler)

    TODO:
        - Extract features
        - Scale using fitted scaler
        - Predict using fitted kmeans model
    """
    # TODO: Implement prediction
    # X = new_customers[features]
    # X_scaled = scaler.transform(X)
    # segments = kmeans_model.predict(X_scaled)
    # return segments
    pass
