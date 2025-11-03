"""
Quick test script to verify all imports work correctly
Run with: python test_imports.py
"""

print("Testing imports...")

try:
    print("✓ Checking gurobipy...")
    import gurobipy as gp
    print("  ✓ Gurobi available")
    GUROBI_AVAILABLE = True
except ImportError:
    print("  ✗ Gurobi not available (will use PuLP)")
    GUROBI_AVAILABLE = False

try:
    print("✓ Checking pulp...")
    from pulp import *
    print("  ✓ PuLP available")
except ImportError:
    print("  ✗ PuLP not available - install with: pip install pulp")
    exit(1)

try:
    print("✓ Checking numpy...")
    import numpy as np
    print("  ✓ NumPy available")
except ImportError:
    print("  ✗ NumPy not available - install with: pip install numpy")
    exit(1)

try:
    print("✓ Checking pandas...")
    import pandas as pd
    print("  ✓ Pandas available")
except ImportError:
    print("  ✗ Pandas not available - install with: pip install pandas")
    exit(1)

print("\n✓ All required dependencies installed!")
print("\nNext steps:")
print("1. Test core module:")
print("   python -c 'from src.rate_limiter_core import RateLimiterLP; print(\"✓ Core imports work!\")'")
print("\n2. Run basic test:")
print("   python simulations/compare_algorithms.py")
