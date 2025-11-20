# Gavish-Graves (GG) Formulation Reference

## Mathematical Formulation

### Sets and Parameters
- **V** = {0, 1, ..., n-1}: Set of nodes (cities)
- **c[i,j]**: Distance/cost from node i to node j
- **n**: Number of nodes

### Decision Variables
- **x[i,j]** ∈ {0,1}: Binary variable, = 1 if edge (i,j) is included in tour
- **f[i,j]** ≥ 0: Continuous flow variable, amount of commodity flowing on edge (i,j)

---

## Integer Program (IP) - Exact TSP

```
minimize:   Σ(i,j∈V, i≠j) c[i,j] · x[i,j]

subject to:

  (1) Degree constraints - outgoing:
      Σ(j∈V, j≠i) x[i,j] = 1    ∀i ∈ V

  (2) Degree constraints - incoming:
      Σ(i∈V, i≠j) x[i,j] = 1    ∀j ∈ V

  (3) Flow from source (node 0):
      Σ(j∈V, j≠0) f[0,j] = n-1

  (4) No flow into source:
      Σ(i∈V, i≠0) f[i,0] = 0

  (5) Flow conservation (each non-source node consumes 1 unit):
      Σ(j∈V, j≠i) f[j,i] - Σ(j∈V, j≠i) f[i,j] = 1    ∀i ∈ V \ {0}

  (6) Flow capacity (flow only on selected edges):
      f[i,j] ≤ (n-1) · x[i,j]    ∀i,j ∈ V, i≠j

  (7) Binary constraints:
      x[i,j] ∈ {0,1}    ∀i,j ∈ V, i≠j

  (8) Non-negativity:
      f[i,j] ≥ 0    ∀i,j ∈ V, i≠j
```

---

## LP Relaxation

Replace constraint (7) with:
```
  (7') 0 ≤ x[i,j] ≤ 1    ∀i,j ∈ V, i≠j
```

All other constraints remain the same.

---

## Why This Works (Subtour Elimination)

The flow mechanism prevents subtours:

1. **Source node 0** sends out exactly (n-1) units of flow
2. **Each other node** consumes exactly 1 unit of flow
3. **Flow capacity constraint** ensures flow only travels on selected edges

If there were a subtour not containing node 0:
- Those nodes would need flow to satisfy conservation constraints
- But they wouldn't be connected to the source
- Therefore, no feasible flow exists → subtour is prevented

---

## Comparison with Other Formulations

| Formulation | Constraints | Variables | LP Gap | Notes |
|-------------|-------------|-----------|--------|-------|
| **DFJ** | Exponential | O(n²) | Tightest | Best LP bound, use with cuts |
| **GG** (this) | O(n²) | O(n²) | Medium | Compact, stronger than MTZ |
| **MTZ** | O(n²) | O(n²) | Weakest | Compact, but weak LP relaxation |

---

## Integrality Gap

**Definition:**
```
Gap(%) = (IP_OPT - LP_OPT) / IP_OPT × 100%
```

Where:
- **IP_OPT**: Optimal integer solution (exact TSP tour cost)
- **LP_OPT**: Optimal LP relaxation solution (lower bound)

**Interpretation:**
- **0%**: LP solution is already integer (very rare)
- **Low (<5%)**: LP relaxation is very tight
- **Medium (5-15%)**: LP relaxation is reasonably tight
- **High (>15%)**: LP relaxation is weak

## References

Gavish, B., & Graves, S. (1978). "The Travelling Salesman Problem and Related Problems."
Working Paper, MIT.

This formulation is particularly useful for:
- Medium-sized TSP instances (n < 100)
- When you need a compact formulation
- Analyzing integrality gaps
- Comparing LP relaxation quality across problem structures