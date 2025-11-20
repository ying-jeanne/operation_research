# TSP Integrality Gap Analysis: GG vs DFJ

This project compares integrality gaps between two TSP formulations:
- **Gavish-Graves (GG)**: Flow-based formulation
- **Dantzig-Fulkerson-Johnson (DFJ)**: Subtour elimination with lazy constraints

## Dataset
We generated the four types of TSP data, and here's a quick summary of the CVs we obtained:

- Grid City (CV ≈ 0.42) – regular grid
- Random Euclidean (CV ≈ 0.46) – uniform points
- Clustered (CV ≈ 0.63) – tight clusters far apart
- Hub-and-Spoke (CV ≈ 0.65) – central hub + amplified spoke distances

Across all structures, we generated 10 instances for n = 15, 18, 20 (120 instances total).

You can find the original dataset here [DBA5103_TSP_Data](https://github.com/qiyazhao062-a11y/DBA5103_TSP_Data):

| Structure | CV |
|-----------|-----|
| Grid | 0.42 |
| Random | 0.46 |
| Clustered | 0.63 |
| Hub-Spoke | 0.65 |

## Usage

### Gavish-Graves (GG) Experiments
```bash
pip install -r requirements.txt
python run_gg_experiments.py   # Generate gg_results.csv
```
Once the file gg_results.csv is generated, you can analyze with `analyze_gg_results.ipynb`.

### Dantzig-Fulkerson-Johnson (DFJ) Experiments
```bash
python run_dfj_experiments.py   # Generate dfj_results.csv
```
Once the file dfj_results.csv is generated, you can analyze with `analyze_dfj_results.ipynb`.

## Key Findings: Bias-Variance Tradeoff

**GG (Gavish-Graves):**
- Low variance (consistent gaps across instances)
- High bias (larger average gaps ~17%)
- Predictable, stable performance

**DFJ (Dantzig-Fulkerson-Johnson):**
- Low bias (tighter gaps ~0.1% on average)
- High variance (gaps vary from 0% to 1.5%)
- Better average performance but less predictable

**References:**
- Held-Karp relaxation (Subtour Elimination Problem - SEP)
- [arXiv:2507.07003 - The Integrality Gap of the TSP](https://arxiv.org/abs/2507.07003)

See [GG_FORMULATION.md](GG_FORMULATION.md) and [GG_EXPERIMENT_GUIDE.md](GG_EXPERIMENT_GUIDE.md) for details.
