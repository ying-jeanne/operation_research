import gurobipy as gp
from gurobipy import GRB
import numpy as np

def build_model(fruits, prices, nutrition, requirements):
    """
    Build the diet optimization model
    """

    # Create a new model
    model = gp.Model("DietProblem")
    model.setParam('LogToConsole', 0)
    x = model.addVars(5, name=fruits, lb=0)
# Objective function: minimize cost
    model.setObjective(sum(prices[i] * x[i] for i in range(5)), GRB.MINIMIZE)

    # Add constraints
    for nutrient, values in nutrition.items():
        min_req, max_req = requirements[nutrient]
        
        # Minimum requirement
        model.addConstr(sum(values[i] * x[i] for i in range(5)) >= min_req, 
                    name=f"min_{nutrient}")
        
        # Maximum allowance
        model.addConstr(sum(values[i] * x[i] for i in range(5)) <= max_req, 
                    name=f"max_{nutrient}")
    return model

def main():
    # Decision variables (amounts in 100g units)
    fruits = ['Apple', 'Banana', 'Blueberries', 'Durian', 'Tangerine']
    prices = [0.5, 0.3, 2.5, 10, 0.5]
        # Nutritional data per 100g
    nutrition = {
        'Calories': [52, 89, 57, 147, 53],
        'Carbohydrate': [14, 23, 14, 27, 13],
        'Fiber': [2.4, 2.6, 2.4, 3.8, 1.8],
        'VitaminA': [54, 64, 54, 44, 681],
        'VitaminC': [4.6, 8.7, 9.7, 19.7, 26.7]
    }

    # Requirements [min, max]
    requirements = {
        'Calories': [500, 3000],
        'Carbohydrate': [50, 400],
        'Fiber': [20, 30],
        'VitaminA': [2000, 3500],
        'VitaminC': [75, 150]
    }

    model = build_model(fruits, prices, nutrition, requirements)
    model.optimize()
    x = model.getVars()

    print("=== PART (A): ORIGINAL DIET PROBLEM ===")
    if model.status == GRB.OPTIMAL:
        print(f"\nOptimal Cost: S${model.objVal}")
        print("\nOptimal Solution (100g units):")
        for i in range(5):
            print(f"  {fruits[i]}: {x[i].x:.3f} units ({x[i].x*100:.1f}g)")
        
        print("\nNutritional Content:")
        for nutrient, values in nutrition.items():
            total = sum(values[i] * x[i].x for i in range(5))
            print(f"  {nutrient}: {total:.2f} (Requirement: {requirements[nutrient][0]} - {requirements[nutrient][1]})")
        print("\nDual Variables (Shadow Prices):")
        
        #  Print optimal dual solutions with sensitivity ranges
        print("\n Dual solutions (Constraint | Shadow Price | Max Decrease | Max Increase):")
        for d in model.getConstrs():
            print('%s %g %g %g' % (d.ConstrName, d.Pi, d.SARHSLow, d.SARHSUp))
    else:
        print("No optimal solution found!")

if __name__ == "__main__":
    main()

