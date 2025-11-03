# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Plan & Review

### Before starting work
- Always in plan mode to make a plan
- After get the plan, make sure you write the plan to .claude/tasks/TASK_NAME.md
- The plan should be a detailed implementation plan and the reasoning behid them, as well as tasks broken down.
- If the task require external knowledge or certain package, also research to get latest knowledge (use Task tool for research)
- Don't over plan it, always think MVP.
- Once you write the plan, firstly ask me to review it. Do not continue until I approve the plan.

### While implementing 
- You should update the plan as you work.
- After you complete tasks in the plan, you should update and append detailed descriptions of the change you made, so following tasks can be easily hand over to other engineers.

## Project Overview

**Title:** Segmentation Strategy Selection: A Decision Framework for A/B Testing vs. Adaptive Learning

**Integration:** Operations Research + Business Analytics + Microeconomics

This project develops a **decision framework** that helps e-commerce platforms choose between three segmentation strategies:

1. **Static Segmentation with A/B Testing**: Upfront experimentation, fixed pricing
2. **Adaptive Learning**: No A/B tests, learn from actual purchases over time
3. **Hybrid Approach**: Light A/B testing followed by continuous adaptation

**Key Innovation:** Rather than advocating for one approach, this project provides a **comparative analysis** showing when each strategy is optimal based on business context (time horizon, customer base size, demand stability, competitive intensity).

**Research Question:** "Under what conditions should e-commerce platforms use upfront A/B testing versus adaptive learning for customer segmentation and pricing decisions?"

**Sub-Questions:**
1. When does A/B testing justify its upfront cost?
2. When is adaptive learning fast enough to outperform A/B testing?
3. What factors determine the optimal approach?
4. Can hybrid strategies outperform pure approaches?

## Dataset

**Source:** Olist Brazilian E-Commerce Public Dataset
**Link:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
**Size:** 100,000 orders (2016-2018)
**Key Features:** Prices, customer IDs, product categories, payment data, geographic locations, order timestamps

**Dataset Components:**
- `olist_customers_dataset.csv` - Customer information
- `olist_orders_dataset.csv` - Order details and timestamps
- `olist_order_items_dataset.csv` - Items, prices, shipping
- `olist_order_payments_dataset.csv` - Payment types and values
- `olist_products_dataset.csv` - Product categories
- `olist_geolocation_dataset.csv` - Geographic data

## Three-Domain Integration

### 1. Business Analytics Foundation (Predictive)

**Purpose:** Understand customers and predict demand behavior

**Tasks:**
- Exploratory data analysis (EDA)
- Customer segmentation using K-means clustering on RFM features (Recency, Frequency, Monetary)
- Demand curve estimation via regression: `log(quantity) = β₀ + β₁·log(price) + features`
- Price elasticity calculation per segment
- Model validation and performance metrics

**Key Outputs:**
- Optimal k from clustering analysis (elbow method, silhouette scores)
- Demand functions D_i(p) for each segment i
- Elasticity estimates ε_i per segment
- Customer lifetime value predictions

**Tools:** pandas, numpy, scikit-learn, matplotlib, seaborn

---

### 2. Microeconomics (Theoretical Foundation)

**Purpose:** Provide economic grounding and cost modeling

**Concepts:**
- **Third-degree price discrimination:** Charging different prices to segments based on elasticity
- **Incentive compatibility:** Customers self-select into correct segments
- **Information economics:** A/B testing as costly information acquisition
- **Expected Value of Perfect Information (EVPI):** Deciding when to run experiments

**Cost Modeling:**

```python
# Segmentation Cost Structure
C(k) = Setup_Cost(k) + Ongoing_Cost(k) + Learning_Cost(k)

Where:
- Setup_Cost: Infrastructure, website dev, legal compliance
- Ongoing_Cost: Marketing × k + Support × k + Analytics × k
- Learning_Cost: Number_of_AB_tests(k) × Cost_per_test

Example estimates:
k=1: $0 (baseline single price)
k=2: $95k first year (setup $30k + annual $40k + A/B $25k)
k=3: $185k first year (setup $50k + annual $75k + A/B $60k)
k=4: $320k first year (setup $80k + annual $120k + A/B $120k)
```

**A/B Testing Cost Components:**
- Opportunity cost: Lost revenue during experiment (customers exposed to suboptimal prices)
- Implementation cost: Technical infrastructure and statistical analysis
- Duration: Longer tests = higher costs but more precision

**Key Outputs:**
- Segmentation cost function C(k)
- Consumer surplus calculations
- Incentive compatibility verification
- Break-even analysis for testing decisions

---

### 3. Operations Research (Prescriptive)

**Purpose:** Optimize and compare three segmentation strategies

---

#### **Strategy A: Static Segmentation with A/B Testing**

**Approach:**
- Period 0: Pay C_AB to run A/B tests, learn demand perfectly
- Period 1-T: Fixed k and prices based on A/B results

**Mathematical Formulation:**
```
Decision Variables: k ∈ {1,2,3,4,5}, p_i for i=1..k

Objective:
maximize: Σ(t=1 to T) [Profit_t(k,p) / (1+r)^t] - C_AB(k)

Where:
  Profit_t(k,p) = Σ[p_i · D_i(p_i) · N_i] - c·Σ[D_i(p_i) · N_i] - C_operating(k)
  C_AB(k) = Upfront A/B testing cost for k segments
```

**Advantages:**
- Optimal from day 1 (perfect demand knowledge)
- No learning period lost profit
- Simpler implementation (fixed prices)

**Disadvantages:**
- High upfront cost ($50k-150k)
- Risk if demand changes over time
- No adaptation capability

---

#### **Strategy B: Adaptive Learning (Dynamic Segmentation)**

**Approach:**
- Period 1: k=1 (universal price), observe purchases
- Period 2+: Adjust k(t), reassign customers based on revealed preferences, update demand beliefs

**Mathematical Formulation:**
```
State at period t: S_t = {purchase_history, current_beliefs, k_t}

Decision at period t: k_t, segment_assignment, prices p_t

Recursive Optimization:
V_t(S_t) = max{Profit_t(k_t, p_t) - C_setup(k_t) + β·E[V_{t+1}(S_{t+1}) | S_t]}

Learning Mechanism:
  If customer i buys at price p: WTP_i ≥ p (update belief upward)
  If customer i doesn't buy at p: WTP_i < p (update belief downward)

  Use Bayesian updating to reassign customers to segments each period
```

**Advantages:**
- Zero A/B testing cost
- Learns from free information (actual sales)
- Adapts to changing customer preferences
- Lower risk (incremental commitment)

**Disadvantages:**
- Slower convergence (takes time to learn)
- Foregone profit during exploration periods
- More operationally complex

---

#### **Strategy C: Hybrid Approach (Novel Contribution)**

**Approach:**
- Period 0: Light A/B testing (smaller sample, lower cost)
- Period 1+: Use A/B results as prior beliefs, then adapt like Strategy B

**Mathematical Formulation:**
```
Period 0: Pay C_AB_light (e.g., $20k vs $100k for full test)
          Get noisy demand estimates D̃_i(p) with uncertainty σ

Period t≥1: Same as Strategy B, but with informed priors
           Faster convergence due to better starting beliefs

Total NPV = Σ[Profit_t / (1+r)^t] - C_AB_light
```

**Advantages:**
- Faster convergence than pure adaptive (good priors)
- Lower cost than full A/B testing
- Still adapts over time (best of both)

**Disadvantages:**
- Still has some upfront cost
- More complex than either pure strategy

---

**Comparative Analysis:**
This project implements all three strategies on the same data and compares:
1. Net Present Value (NPV) over different time horizons
2. Break-even points (when does one outperform another?)
3. Sensitivity to key parameters (T, N, C_AB, demand volatility)

**Tools:** PuLP, scipy.optimize, custom simulation framework

---

## Project Structure

```
project/
├── CLAUDE.md                    # This file
├── project.md                   # Original concept notes
├── README.md                    # Setup and quick start guide
│
├── data/
│   ├── raw/                    # Original Olist CSV files
│   └── processed/              # Cleaned, merged datasets
│       ├── customer_features.csv
│       └── orders_complete.csv
│
├── notebooks/
│   ├── 01_eda.ipynb                    # Exploratory data analysis
│   ├── 02_segmentation.ipynb           # K-means clustering
│   ├── 03_demand_estimation.ipynb      # Elasticity modeling
│   ├── 04_strategy_a_ab_testing.ipynb  # Strategy A implementation
│   ├── 05_strategy_b_adaptive.ipynb    # Strategy B implementation
│   ├── 06_strategy_c_hybrid.ipynb      # Strategy C implementation
│   └── 07_comparative_analysis.ipynb   # Compare all three strategies
│
├── src/
│   ├── analytics/
│   │   ├── data_processing.py          # ETL and feature engineering
│   │   ├── segmentation.py             # Clustering algorithms
│   │   └── demand_models.py            # Demand curve estimation
│   │
│   ├── economics/
│   │   ├── cost_models.py              # C(k) functions for all strategies
│   │   ├── welfare.py                  # Consumer surplus
│   │   └── ab_testing.py               # A/B testing cost & simulation
│   │
│   ├── optimization/
│   │   ├── static_optimization.py      # Strategy A (static with A/B)
│   │   ├── adaptive_learning.py        # Strategy B (dynamic)
│   │   ├── hybrid_optimization.py      # Strategy C (hybrid)
│   │   └── sensitivity.py              # Sensitivity analysis
│   │
│   └── comparison/
│       ├── simulator.py                # Multi-period simulation framework
│       ├── metrics.py                  # NPV, break-even calculations
│       └── decision_framework.py       # Recommendation engine
│
├── results/
│   ├── figures/                # Visualizations
│   ├── tables/                 # Results tables
│   └── sensitivity/            # Sensitivity analysis outputs
│
├── report/
│   ├── final_report.pdf
│   └── presentation.pptx
│
├── requirements.txt            # Python dependencies
└── config.py                   # Parameters and settings
```

## Development Workflow (7-Week Plan)

### Week 1: Data Preparation & EDA
1. Download Olist dataset from Kaggle
2. Load and merge all CSV files
3. Clean data (missing values, outliers)
4. Feature engineering: RFM scores, product categories
5. Exploratory visualization and summary statistics

### Week 2: Customer Segmentation & Demand Estimation
1. K-means clustering with k=2,3,4,5
2. Validate clusters (silhouette scores, business logic)
3. Estimate demand curves per segment (log-log regression)
4. Calculate price elasticities
5. Train/test validation

### Week 3: Strategy A - Static with A/B Testing
1. Define A/B testing cost structure
2. Simulate "perfect" demand knowledge scenario
3. Optimize k and prices assuming perfect information
4. Calculate NPV over T=1,2,3,5 year horizons
5. Document as baseline approach

### Week 4: Strategy B - Adaptive Learning
1. Implement 4-period simulation (quarters)
2. Period 1: Universal pricing (k=1), observe
3. Period 2+: Myopic optimization with Bayesian belief updating
4. Track k(t), prices(t), profit(t) trajectory
5. Calculate NPV and compare to Strategy A

### Week 5: Strategy C - Hybrid Approach
1. Simulate light A/B testing (reduced cost, noisy priors)
2. Implement adaptive refinement with informed priors
3. Compare convergence speed vs Strategy B
4. Calculate NPV and compare to both A and B
5. Identify sweet spot (cost vs. learning speed)

### Week 6: Comparative Analysis & Decision Framework
1. Run all three strategies on same data
2. Sensitivity analysis: Vary T, N, C_AB, demand volatility
3. Generate break-even charts and recommendation matrix
4. Build decision support tool (input context → output strategy)
5. Create visualizations for all comparisons

### Week 7: Synthesis & Reporting
1. Synthesize insights across all three strategies
2. Write final report with decision framework
3. Create presentation with key findings
4. Document code and deliverables
5. Prepare for presentation/submission

## Key Implementation Notes

### Customer Segmentation
- Use StandardScaler before K-means (features have different scales)
- Test multiple k values, don't assume k=3 is best
- Validate clusters make business sense (not just statistical)

### Demand Estimation
- Use log-log specification for constant elasticity
- Separate model per segment (allows different elasticities)
- Include control variables: product category, seasonality
- Check for heteroskedasticity and autocorrelation

### Cost Modeling
- Base estimates on industry reports (cite sources)
- Use sensitivity analysis to handle uncertainty
- Consider multiple cost scenarios (optimistic/pessimistic)

### Optimization
- Start with simplified model (e.g., k fixed, optimize prices only)
- Then extend to full MINLP
- If computation is slow, use heuristics or decomposition
- Always validate solutions make economic sense

### Sensitivity Analysis
- Vary cost parameters: ±10%, ±20%, ±50%
- Test robustness to elasticity estimates
- Scenario analysis: What if segmentation costs double?
- Break-even: At what cost is k=2 optimal vs k=3?

## Common Pitfalls to Avoid

1. **Overfitting clusters:** Don't choose k too high just because metrics improve slightly
2. **Ignoring business logic:** Segments should be interpretable and actionable
3. **Assuming linear costs:** Test multiple cost function specifications
4. **Weak validation:** Always use train/test split and cross-validation
5. **Missing constraints:** Don't forget incentive compatibility and participation
6. **Over-optimization:** Model is for insights, not exact predictions
7. **Insufficient sensitivity:** One cost scenario is not enough—test robustness

## Decision Framework & Recommendations

This project's main contribution is a **decision framework** for choosing segmentation strategies.

### Key Factors That Determine Optimal Strategy

| Factor | Favors A/B Testing | Favors Adaptive Learning |
|--------|-------------------|-------------------------|
| **Time Horizon** | Short (< 2 years) | Long (> 3 years) |
| **Customer Base** | Small (< 10k) | Large (> 100k) |
| **Demand Stability** | Stable, predictable | Dynamic, seasonal |
| **Revenue Scale** | High ($50M+) | Low-Medium ($1-10M) |
| **Competition** | Intense (need speed) | Low (can experiment) |
| **Price Change Tolerance** | Low (B2B, luxury) | High (consumer tech) |
| **Operational Flexibility** | Low (physical infrastructure) | High (digital products) |

### Quantitative Decision Rule

**Break-Even Time Horizon (T*):**
```
Choose A/B Testing if: T < T*
Choose Adaptive if: T > T*
Choose Hybrid if: T ≈ T*

Where T* = C_AB / (Profit_AB_per_period - Profit_Adaptive_per_period)
```

**Example Calculation:**
- A/B cost: $100k
- Strategy A annual profit: $2.0M (optimal from start)
- Strategy B year 1 profit: $1.5M (learning)
- Strategy B year 2+ profit: $2.1M (adapted)

T* ≈ 2 years (break-even point)

### Recommendation Matrix (Example Output)

| Business Context | Recommended Strategy | Rationale |
|------------------|---------------------|-----------|
| **Startup SaaS (N=5k, T=1yr, uncertain demand)** | **Adaptive** | Low cost, discover market as you go, limited budget |
| **Mature E-commerce (N=500k, T=3yr, seasonal)** | **Adaptive** or **Hybrid** | Large scale enables fast learning, demand changes |
| **Enterprise Software (N=50k, T=5yr, stable)** | **A/B Testing** | Lock in optimal pricing, customers expect stability |
| **Fast Fashion (N=1M, T=2yr, volatile)** | **Adaptive** | Trends change faster than A/B results stay valid |
| **Luxury Brand (N=10k, T=5yr, stable)** | **A/B Testing** | Brand consistency critical, small base = slow learning |
| **New Product Launch (Unknown N, T=6mo)** | **Adaptive** | Market discovery phase, no data for A/B testing |

---

## Expected Outputs

### 1. Technical Deliverables

**Analytics Outputs:**
- Customer segmentation (k=2,3,4,5) with validation
- Demand curves and elasticity estimates per segment
- Purchase behavior analysis

**Strategy Implementations:**
- Strategy A: Optimal k* and prices with A/B testing
- Strategy B: 4-period adaptive learning trajectory
- Strategy C: Hybrid approach with convergence analysis

**Comparative Analysis:**
- NPV comparison across all three strategies
- Break-even time horizon calculations
- Sensitivity heatmaps (T, N, C_AB, volatility)

**Decision Support:**
- Interactive recommendation tool (input context → output strategy)
- Visualization dashboard comparing strategies
- Managerial guidelines document

### 2. Report Structure

1. **Executive Summary** (1 page)
   - Problem: When to use A/B testing vs adaptive learning?
   - Approach: Comparative analysis of three strategies
   - Key findings: Decision framework with quantitative break-even analysis

2. **Introduction** (2-3 pages)
   - Motivation: Companies struggle with segmentation strategy choice
   - Research question and sub-questions
   - Contribution: Practical decision framework

3. **Literature Review** (2 pages)
   - Price discrimination and revenue management
   - A/B testing in pricing
   - Adaptive learning approaches
   - Gap: No comparative framework with realistic costs

4. **Methodology** (5-6 pages)
   - **Analytics:** Customer segmentation, demand estimation
   - **Economics:** Cost modeling for all three strategies
   - **OR:** Optimization models for each approach
   - Implementation details and assumptions

5. **Results** (5-6 pages)
   - Customer segments and characteristics
   - Demand curves and elasticity estimates
   - Strategy A results (static with A/B)
   - Strategy B results (adaptive learning)
   - Strategy C results (hybrid)
   - Comparative analysis and break-even

6. **Decision Framework** (3-4 pages)
   - Factor analysis (what determines optimal choice?)
   - Recommendation matrix
   - Sensitivity analysis
   - Practical guidelines for managers

7. **Discussion** (2-3 pages)
   - Managerial implications
   - Limitations and assumptions
   - When each strategy works best

8. **Conclusion** (1 page)
   - Summary of contributions
   - Future research directions
   - Practical takeaways

**Appendices:**
- Code documentation
- Additional sensitivity analysis
- Mathematical derivations

### 3. Presentation (15-20 minutes)

**Slide Structure:**
1. **Problem** (2 min): Companies face choice between A/B testing vs learning-by-doing
2. **Approach** (3 min): Three strategies, three-domain integration
3. **Data & Analytics** (3 min): Olist dataset, segmentation, demand estimation
4. **Strategy Comparison** (5 min): Results from A, B, C with NPV charts
5. **Decision Framework** (4 min): Recommendation matrix, break-even analysis
6. **Insights** (2 min): When to use which strategy
7. **Q&A** (3 min)

**Key Visualizations:**
- Profit trajectory over time for each strategy
- Break-even time horizon chart
- Sensitivity heatmap (T vs N)
- Decision tree or flowchart for strategy selection

## References & Resources

**Price Discrimination:**
- Tirole, J. (1988). *The Theory of Industrial Organization*
- Varian, H. R. (1989). "Price Discrimination" in *Handbook of Industrial Organization*

**Revenue Management:**
- Talluri, K., & Van Ryzin, G. (2004). *The Theory and Practice of Revenue Management*
- Phillips, R. L. (2005). *Pricing and Revenue Optimization*

**A/B Testing & Information Economics:**
- Kohavi, R., & Longbotham, R. (2017). "Online Controlled Experiments and A/B Testing"
- Blackwell, D. (1953). "Equivalent Comparisons of Experiments"

**Customer Segmentation:**
- Wedel, M., & Kamakura, W. A. (2000). *Market Segmentation: Conceptual and Methodological Foundations*

**Industry Reports (for cost estimates):**
- SaaS pricing strategy reports (ProfitWell, ChartMogul)
- E-commerce benchmarks (Shopify, BigCommerce)
- A/B testing platforms (Optimizely, VWO) pricing pages
