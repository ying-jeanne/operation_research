# Getting Started - Segmentation Strategy Project

**Congratulations!** Your project structure is set up. Here's what to do next.

---

## ✅ What's Been Created

### 1. **Folder Structure**
```
project/
├── data/raw/              ← Put Olist CSVs here
├── data/processed/        ← Generated cleaned data
├── notebooks/             ← Your Jupyter notebooks (to be created)
├── src/                   ← Reusable Python functions
│   ├── analytics/         ← Data processing, clustering, demand
│   ├── economics/         ← Cost models
│   ├── optimization/      ← Strategy A, B, C implementations
│   └── comparison/        ← NPV, metrics (to be created)
├── results/               ← Outputs: figures, tables, sensitivity
├── requirements.txt       ← Python packages
├── config.py              ← All parameters
└── .gitignore             ← Git ignore rules
```

### 2. **Configuration Files**
- ✅ [requirements.txt](requirements.txt) - All Python packages you need
- ✅ [config.py](config.py) - Centralized parameters (costs, k values, etc.)
- ✅ [.gitignore](.gitignore) - Ignore data files and cache

### 3. **Helper Function Templates** (in `src/`)
- ✅ `analytics/data_processing.py` - Load, merge, clean Olist data
- ✅ `analytics/segmentation.py` - K-means clustering functions
- ✅ `analytics/demand_models.py` - Demand curve estimation
- ✅ `economics/cost_models.py` - Segmentation cost calculations
- ✅ `optimization/static_optimization.py` - Strategy A template

**Note:** These are **templates with TODOs** - you'll implement the actual logic!

---

## 🚀 Next Steps (Start TODAY)

### **Step 1: Install Python Packages** (15 minutes)

```bash
# Navigate to project directory
cd /Users/ying-jeanne/Workspace/operation_research/project

# Install all dependencies
pip install -r requirements.txt

# Test that it worked
python -c "import pandas, sklearn, pulp; print('Success!')"
```

### **Step 2: Download Olist Data** (30 minutes)

1. Go to https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Click "Download" (requires Kaggle account - free)
3. Unzip all CSV files
4. Move them to `data/raw/` folder

**You should have these files:**
- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `product_category_name_translation.csv`

### **Step 3: Verify Setup** (10 minutes)

```bash
# Test config file
python config.py

# Should print:
# Configuration loaded successfully!
# Project directory: /Users/ying-jeanne/Workspace/operation_research/project
# K values to test: [1, 2, 3, 4, 5]
# ...
```

### **Step 4: Create Your First Notebook** (Week 1 Starts!)

Create `notebooks/01_eda.ipynb` with this starter code:

```python
# Cell 1: Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append('../')  # Add project root to path
from config import RAW_DATA_DIR, OLIST_FILES

# Cell 2: Load one file to test
orders = pd.read_csv(f"{RAW_DATA_DIR}/{OLIST_FILES['orders']}")
print(f"Loaded orders: {orders.shape}")
print(orders.head())

# Cell 3: TODO - Continue with full EDA
# ...
```

---

## 📅 Week 1 Checklist

Use this as your guide for the first week:

### Monday (3-4 hours)
- [ ] Install Python packages
- [ ] Download Olist data
- [ ] Create `01_eda.ipynb`
- [ ] Load and inspect `orders` table
- [ ] Check for missing values

### Wednesday (3-4 hours)
- [ ] Load all remaining CSV files
- [ ] Merge tables (use hints in `src/analytics/data_processing.py`)
- [ ] Create complete order dataset
- [ ] Handle missing values

### Friday (3-4 hours)
- [ ] Calculate summary statistics
- [ ] Create 5 visualizations:
  1. Price distribution
  2. Orders per customer
  3. Product categories
  4. Geographic distribution
  5. Time series

### Weekend (3-4 hours)
- [ ] Implement `calculate_rfm()` function
- [ ] Test RFM calculation
- [ ] Save processed data to `data/processed/`
- [ ] Document findings in notebook

### Sunday Checkpoint
- [ ] Do I have `orders_complete.csv` saved?
- [ ] Do I have RFM features for customers?
- [ ] Total hours this week: ___ (target: 12-15)

---

## 📚 Key Resources

### Documentation
- [CLAUDE.md](CLAUDE.md) - Complete technical documentation
- [README.md](README.md) - Project overview
- [project.md](project.md) - Original concept notes

### Helpers Created
- `src/analytics/data_processing.py` - Data loading functions
- `src/analytics/segmentation.py` - Clustering functions
- `src/analytics/demand_models.py` - Demand estimation
- `src/economics/cost_models.py` - Cost calculations
- `src/optimization/static_optimization.py` - Strategy A

### Config Parameters (in `config.py`)
- `K_VALUES = [1, 2, 3, 4, 5]` - Segments to test
- `AB_TESTING_COSTS` - Cost for each k
- `SETUP_COSTS` - Implementation costs
- `TIME_HORIZONS = [1, 2, 3, 5]` - Years to evaluate
- `DISCOUNT_RATE = 0.10` - 10% for NPV

---

## 💡 Tips for Success

### 1. **Use the Helper Functions**
Don't reinvent the wheel - implement the TODOs in `src/` files, then import:
```python
from src.analytics.data_processing import load_olist_data, calculate_rfm
from src.analytics.segmentation import cluster_customers
```

### 2. **Change Parameters in One Place**
All costs and parameters are in `config.py`. Change there, affects everywhere.

### 3. **Save Your Work Incrementally**
After each major step:
```python
df.to_csv(f"{PROCESSED_DATA_DIR}/checkpoint_name.csv", index=False)
```

### 4. **Track Your Hours**
- Use Sunday checkpoints to adjust if falling behind
- If Week 1 takes >20 hours, simplify Week 2

### 5. **Ask for Help When Stuck**
- Check helper function templates for hints
- Look at CLAUDE.md for implementation notes
- Common issues: file paths, missing values, data types

---

## 🎯 Success Criteria for Week 1

By end of Week 1, you should have:
1. ✅ All data loaded and merged
2. ✅ RFM features calculated
3. ✅ 5+ visualizations
4. ✅ Clean dataset saved to `data/processed/`
5. ✅ `01_eda.ipynb` complete and documented

**If you have these**, you're ready for Week 2 (clustering & demand estimation)!

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'pandas'"
```bash
pip install -r requirements.txt
```

### "FileNotFoundError: data/raw/olist_orders_dataset.csv"
- Download data from Kaggle
- Make sure files are in `data/raw/` (not in a subfolder)

### "ImportError: cannot import name 'load_olist_data'"
- Make sure you're in project root when running notebook
- Add `sys.path.append('../')` at top of notebook

### "My notebook can't find config.py"
```python
# Add to first cell:
import sys
sys.path.append('/Users/ying-jeanne/Workspace/operation_research/project')
from config import *
```

---

## 📞 What's Next

After Week 1, you'll move to:
- **Week 2:** Customer segmentation (K-means)
- **Week 3:** Strategy A implementation
- **Week 4:** Strategy B (adaptive learning)
- **Week 5:** Strategy C (hybrid)
- **Week 6:** Comparative analysis
- **Week 7:** Report and presentation

**Good luck! You've got a solid foundation. Now start building! 🚀**

---

Last updated: October 2025
