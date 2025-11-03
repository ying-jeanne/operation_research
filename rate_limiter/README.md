# Dynamic Priced Rate Limiting for APIs Using Duality

**Author:** Ying WANG
**Course:** Operations Research
**Project Type:** Semester Project

## Overview

This project implements a dynamic rate limiter for APIs that uses **LP duality** to derive real-time congestion prices. The implementation incorporates insights from **Vehicle Routing Problem (VRP)** literature to enhance performance, stability, and robustness.

## Key Features

1. **Dual-Based Dynamic Pricing**: Uses shadow prices (π) from LP to set real-time request prices
2. **Hard SLA Guarantees**: Premium clients get guaranteed minimum rates
3. **Client Willingness-to-Pay**: Customers pre-define maximum prices they'll accept
4. **VRP-Inspired Enhancements**:
   - Warm-start solving (faster re-optimization)
   - Rolling horizon optimization (price stability)
   - Robust capacity buffers (demand uncertainty handling)
   - Intelligent re-optimization triggers

## Project Structure

```
rate_limiter/
├── README.md                   # This file
├── idea.tex                    # Project proposal (LaTeX)
├── idea.pdf                    # Project proposal (PDF)
├── requirements.txt            # Python dependencies
│
├── src/                        # Core implementation
│   ├── __init__.py
│   ├── rate_limiter_core.py    # Base LP formulation
│   ├── vrp_enhancements.py     # VRP-inspired techniques
│   ├── fairness_metrics.py     # Fairness evaluation
│   └── dynamic_pricing.py      # Price-based admission control
│
├── simulations/                # Simulation scripts
│   ├── __init__.py
│   ├── workload_generator.py   # Synthetic workload creation
│   └── compare_algorithms.py   # Benchmark comparisons
│
├── notebooks/                  # Jupyter analysis
│   └── rate_limiter_demo.ipynb # Interactive demo
│
├── data/                       # Generated data (gitignored)
│   └── workloads/
│
└── results/                    # Output figures and tables
    ├── figures/
    └── tables/
```

## Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Note: Gurobi requires a license (free academic licenses available)
# Alternatively, use PuLP which uses free solvers (COIN-OR CBC)
```

### Running the Demo

```bash
# Start Jupyter notebook
jupyter notebook notebooks/rate_limiter_demo.ipynb
```

### Running Simulations

```bash
# Compare algorithms
python simulations/compare_algorithms.py

# Results will be saved to results/
```

## VRP Connection

This project applies concepts from Vehicle Routing Problem (VRP) research:

| VRP Concept | Rate Limiter Application |
|-------------|-------------------------|
| **Hard time windows** | Hard SLA constraints (r_i ≥ R_i^min) |
| **Vehicle capacity** | System capacity (Σr_i ≤ C) |
| **Dual variables in column generation** | Congestion pricing (π = shadow price) |
| **Warm-starting** | Re-use previous solution for faster solving |
| **Rolling horizon** | Multi-period lookahead for price stability |
| **Robust optimization** | Capacity buffers for demand uncertainty |

## Methodology

### 1. LP Formulation

```
max Σ w_i * r_i          (weighted throughput)
s.t. Σ r_i ≤ C           (capacity constraint, dual: π)
     r_i ≥ R_i^min       (hard SLA for premium clients)
     r_i ≥ 0
```

### 2. Dynamic Request Processing

```
For each incoming request:
  1. Check hard SLA constraints → reject if violated
  2. Check soft limit:
     - If customer_price ≥ current_π → accept & charge
     - If customer_price < current_π → reject
  3. Update system state
```

### 3. VRP Enhancements

- **Warm Start**: Initialize LP with previous r_i* values
- **Rolling Horizon**: Optimize over next T periods with decreasing weights
- **Robust Buffer**: Reserve C_buffer = β * std(recent_demand) capacity
- **Smart Triggers**: Re-solve when time≥10s OR load_change>20%

## Evaluation Metrics

1. **Request acceptance rate** (overall and per-tier)
2. **Fairness** (Jain's fairness index)
3. **SLA compliance** (% of hard constraints met)
4. **System utilization** (% of capacity used)
5. **Revenue** (total collected from pricing)
6. **Price stability** (coefficient of variation in π over time)
7. **Solving time** (impact of warm-starting)

## Expected Results

Preliminary analysis suggests VRP enhancements provide:
- **30-40% faster solving** (warm-start vs cold-start)
- **40-50% less price volatility** (rolling horizon vs myopic)
- **95%+ SLA compliance** (hard constraints always met)
- **15-20% revenue increase** vs static rate limiting

## References

### Rate Limiting & Congestion Control
- Token bucket and leaky bucket algorithms (RFC 1363)
- Kelly, F. (1997). "Charging and rate control for elastic traffic"

### VRP & Duality
- Desrochers et al. (1992). "A column generation approach for large-scale aircrew rostering"
- Barnhart et al. (1998). "Branch-and-price: Column generation for solving huge integer programs"

### Cloud Pricing
- Agmon Ben-Yehuda et al. (2013). "Deconstructing Amazon EC2 Spot Instance Pricing"

## License

Academic project for educational purposes.

## Contact

Ying WANG - National University of Singapore
