# Segmentation Strategy Selection: A Decision Framework

**A Comparative Analysis of A/B Testing vs. Adaptive Learning for E-commerce Price Discrimination**

---

## 🎯 Project Overview

This project answers a critical question facing e-commerce platforms:

> **"Should we invest in upfront A/B testing or learn adaptively from customer behavior?"**

Rather than advocating for one approach, we develop a **decision framework** that identifies when each strategy is optimal based on business context.

### Three Strategies Compared

1. **Strategy A: Static Segmentation with A/B Testing**
   - Pay $50k-150k for upfront experimentation
   - Get optimal prices immediately
   - Fixed segmentation over time

2. **Strategy B: Adaptive Learning**
   - Zero A/B cost
   - Learn from actual purchases (free information)
   - Dynamic segmentation that evolves over time

3. **Strategy C: Hybrid Approach**
   - Light A/B testing ($20k-50k)
   - Then continuous adaptation
   - Best of both worlds

---

## 🔬 Methodology: Three-Domain Integration

### Business Analytics (Predictive)
- Customer segmentation using K-means on 100k e-commerce orders
- Demand curve estimation via regression
- Price elasticity calculation per segment

### Microeconomics (Theoretical)
- Third-degree price discrimination theory
- Information economics (A/B testing as costly information acquisition)
- Segmentation cost modeling (implementation + learning costs)

### Operations Research (Prescriptive)
- Multi-period optimization for each strategy
- Net Present Value (NPV) comparison
- Break-even analysis and sensitivity testing

---

## 📊 Dataset

**Source:** [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

**Size:** 100,000 orders from 2016-2018

**Key Features:**
- Order prices and quantities
- Customer IDs and purchase history
- Product categories
- Geographic locations
- Payment methods

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.8+
Jupyter Notebook
```

### Installation

```bash
# Clone the repository
cd project/

# Install dependencies
pip install -r requirements.txt
```

### Download Data

1. Visit [Kaggle - Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Download all CSV files
3. Place in `data/raw/` directory

### Run Analysis

```bash
# Start with exploratory analysis
jupyter notebook notebooks/01_eda.ipynb

# Follow the numbered notebooks in sequence:
# 01_eda.ipynb → 02_segmentation.ipynb → 03_demand_estimation.ipynb
# → 04_strategy_a_ab_testing.ipynb → 05_strategy_b_adaptive.ipynb
# → 06_strategy_c_hybrid.ipynb → 07_comparative_analysis.ipynb
```

---

## 📁 Project Structure

```
project/
├── README.md                   # This file
├── CLAUDE.md                   # Comprehensive technical documentation
├── requirements.txt            # Python dependencies
│
├── data/
│   ├── raw/                   # Original Olist CSV files
│   └── processed/             # Cleaned and merged data
│
├── notebooks/                  # Jupyter notebooks (run in order)
│   ├── 01_eda.ipynb
│   ├── 02_segmentation.ipynb
│   ├── 03_demand_estimation.ipynb
│   ├── 04_strategy_a_ab_testing.ipynb
│   ├── 05_strategy_b_adaptive.ipynb
│   ├── 06_strategy_c_hybrid.ipynb
│   └── 07_comparative_analysis.ipynb
│
├── src/                       # Python source code
│   ├── analytics/            # Data processing, clustering, demand models
│   ├── economics/            # Cost models, A/B testing simulation
│   ├── optimization/         # Strategy implementations
│   └── comparison/           # NPV calculation, decision framework
│
└── results/                   # Outputs
    ├── figures/              # Visualizations
    ├── tables/               # Results tables
    └── sensitivity/          # Sensitivity analysis
```

---

## 🎓 Key Contributions

### 1. Comparative Framework
Most research advocates for ONE approach. We provide objective comparison showing when each works best.

### 2. Realistic Cost Modeling
Explicitly models:
- A/B testing costs (opportunity + implementation)
- Segmentation setup costs
- Ongoing operational costs
- Learning costs (foregone profit during exploration)

### 3. Adaptive Segmentation
Novel approach where k (number of segments) evolves over time based on observed customer behavior.

### 4. Decision Support Tool
Practical framework managers can use:
- Input: Time horizon, customer base size, revenue scale, demand stability
- Output: Recommended strategy with quantitative justification

---

## 📈 Example Results

### Break-Even Analysis

| Scenario | Time Horizon | Recommended Strategy | Break-Even Point |
|----------|--------------|---------------------|------------------|
| Startup SaaS | 1 year | **Adaptive** | N/A (A/B too expensive) |
| Mid-Size E-commerce | 2 years | **Hybrid** | T* = 1.8 years |
| Enterprise Software | 5 years | **A/B Testing** | Immediate ROI |
| Fast Fashion | 2 years | **Adaptive** | T* = 1.2 years (demand volatile) |

### NPV Comparison (Example)

```
Strategy A (A/B Testing):  NPV = $5.8M (optimal from day 1, but $100k upfront)
Strategy B (Adaptive):     NPV = $5.9M (slower start, converges by year 3)
Strategy C (Hybrid):       NPV = $6.1M (best of both, $30k upfront)

Winner: Strategy C for T=3 year horizon
```

---

## 🛠️ Technologies Used

**Languages:** Python 3.8+

**Libraries:**
- **Analytics:** pandas, numpy, scikit-learn
- **Visualization:** matplotlib, seaborn, plotly
- **Optimization:** PuLP, scipy.optimize
- **Statistics:** statsmodels

---

## 📝 Research Question

**Main Question:**
> "Under what conditions should e-commerce platforms use upfront A/B testing versus adaptive learning for customer segmentation and pricing decisions?"

**Sub-Questions:**
1. When does A/B testing justify its upfront cost?
2. When is adaptive learning fast enough to outperform A/B testing?
3. What factors determine the optimal approach?
4. Can hybrid strategies outperform pure approaches?

---

## 🎯 Decision Framework

### Factors That Determine Optimal Strategy

| Factor | Favors A/B Testing | Favors Adaptive |
|--------|-------------------|-----------------|
| Time Horizon | Short (< 2 years) | Long (> 3 years) |
| Customer Base | Small (< 10k) | Large (> 100k) |
| Demand Stability | Stable | Volatile/Seasonal |
| Competition | Intense | Low |
| Revenue Scale | High ($50M+) | Low-Medium |

### Quantitative Decision Rule

```
Break-even time: T* = C_AB / (Profit_AB - Profit_Adaptive)

If T < T*: Choose A/B Testing
If T > T*: Choose Adaptive Learning
If T ≈ T*: Choose Hybrid
```

---

## 📚 References

**Key Literature:**
- Talluri & Van Ryzin (2004): *The Theory and Practice of Revenue Management*
- Phillips (2005): *Pricing and Revenue Optimization*
- Kohavi & Longbotham (2017): "Online Controlled Experiments and A/B Testing"
- Tirole (1988): *The Theory of Industrial Organization*

**Industry Sources:**
- SaaS pricing benchmarks (ProfitWell, ChartMogul)
- A/B testing platform pricing (Optimizely, VWO)
- E-commerce metrics (Shopify, BigCommerce)

---

## 🤝 Author

**Student Project:** NUS Business Analytics Foundation + Operations Research + Microeconomics Integration

**Advisor:** Professor Zhenyu Hu (Operations Research), NUS Business School

---

## 📄 License

This project is for academic purposes. Dataset provided by Olist under CC BY-NC-SA 4.0.

---

## 🔗 Links

- [Olist Dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [Project Documentation](CLAUDE.md)
- [Project Concept Notes](project.md)

---

## 📧 Contact

For questions or feedback about this project, please contact via NUS channels.

---

## 🙏 Acknowledgments

- **Olist** for providing the open e-commerce dataset
- **Professor Zhenyu Hu** for guidance on revenue management and dynamic pricing
- **Microeconomics instructor** for insights on information economics and A/B testing costs
- **Analytics instructors** for predictive modeling foundation

---

**Last Updated:** October 2025
