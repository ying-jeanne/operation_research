from gurobipy import *
import numpy as np
import copy

class MarkdownConfig:
    def __init__(self, price=None, demand=None, salvage_value=25, 
                 inventory=2000, time_horizon=15, full_price_week=1):
        # The vector of prices
        self.price = np.array(price)
        # The vector of demands
        self.demand = np.array(demand)
        # Salvage value
        self.s = salvage_value
        # Total number of inventory
        self.I = inventory
        # Time horizon
        self.T = time_horizon
        # Full price week
        self.full_price_week = full_price_week
        # Number of price levels
        self.N = len(self.price)
        
        # Validation
        if len(self.price) != len(self.demand):
            raise ValueError("Price and demand arrays must have the same length")
    


#########Model Set-up Using Function###############
def create_or_update_model(existing_model, config, force_rebuild=False):
    """
    Create new model or update existing one based on what changed
    """
    if existing_model is None or force_rebuild:
        # Create new model
        return _create_fresh_model(config)
    else:
        # Try to update existing model
        try:
            return _update_existing_model(existing_model, config)
        except:
            # Fall back to creating new model if update fails
            print("Update failed, creating new model...")
            return _create_fresh_model(config)

def _create_fresh_model(config):
    """Create a completely new optimization model"""
    print("Creating fresh model...")
    m = Model("Retail")
    m.setParam('LogToConsole', 0)
    x = m.addVars(config.N, name="x")
    
    # Store config reference and variables for later comparison/updates
    m._config = config
    m._variables = x
    
    # set objective
    m.setObjective( quicksum(config.price[i]*config.demand[i]*x[i] for i in range(config.N)) 
                + config.s*(config.I - quicksum(config.demand[i]*x[i] for i in range(config.N))), GRB.MAXIMIZE)

    # capcity constraint: 
    m.addConstr( quicksum(config.demand[i]*x[i] for i in range(config.N)) <= config.I , "inventory")
    # time constraint: 
    m.addConstr( quicksum(x[i] for i in range(config.N)) <= config.T , "time")
    # full price constraint: 
    m.addConstr( x[0] >= config.full_price_week , "full_price")

    return m

def _update_existing_model(model, new_config):
    """Update existing model with new configuration"""
    print("Updating existing model...")
    old_config = model._config
    
    # If structure changed (number of price levels), rebuild
    if len(new_config.price) != len(old_config.price):
        print("Structure changed, rebuilding model...")
        return _create_fresh_model(new_config)
    
    # Update RHS values efficiently
    model.getConstrByName("inventory").RHS = new_config.I
    model.getConstrByName("time").RHS = new_config.T
    model.getConstrByName("full_price").RHS = new_config.full_price_week
    
    # If objective coefficients changed, rebuild (Gurobi limitation)
    if not np.array_equal(new_config.price, old_config.price) or \
       not np.array_equal(new_config.demand, old_config.demand) or \
       new_config.s != old_config.s:
        print("Objective coefficients changed, rebuilding model...")
        return _create_fresh_model(new_config)
    
    # Update stored config and sync model
    model._config = new_config
    model.update()
    print("Model updated successfully!")
    return model

def solve_and_print(model, config_name=""):
    """Helper function to solve model and print results"""
    model.optimize()
    
    if model.status == GRB.OPTIMAL:
        print(f"\n=== {config_name} Results ===")
        print(f"Optimal objective value: {model.objVal:.2f}")
        for v in model.getVars():
            if v.x > 0:  # Only show non-zero variables
                print(f"  {v.varName}: {v.x:.2f}")
        # print the dual constraints and shadow prices
        for c in model.getConstrs():
            print(f"Constraint: {c.ConstrName}, Shadow Price: {c.Pi}, Range: [{c.SARHSLow}, {c.SARHSUp}]")
    else:
        print(f"No optimal solution found for {config_name}")

def main():
    model = None
    
    # Scenario 1: Initial configuration
    print("=== Scenario 1: Initial Setup ===")
    config1 = MarkdownConfig(
        price=[60, 54, 48, 36],
        demand=[125, 162.5, 217.5, 348.8],
        salvage_value=25,
        inventory=2000,
        time_horizon=15,
        full_price_week=1
    )
    model = create_or_update_model(model, config1)
    solve_and_print(model, "Initial Setup")
    
    # Scenario 2: Change only inventory (efficient update)
    print("\n=== Scenario 2: Change Inventory ===")
    config2 = copy.deepcopy(config1)
    config2.I = 2100
    model = create_or_update_model(model, config2)
    solve_and_print(model, "Changed Inventory")
    
    # Scenario 3: Change time horizon (efficient update)
    print("\n=== Scenario 3: Extended Time Horizon ===")
    config3 = copy.deepcopy(config1)
    config3.T = 20  # Extended time horizon
    model = create_or_update_model(model, config3)
    solve_and_print(model, "Extended Time")
    
    # Scenario 4: Change prices (requires rebuild)
    print("\n=== Scenario 4: Different Prices ===")
    config4 = copy.deepcopy(config1)
    config4.price = np.array([60, 58, 56, 54, 52, 50, 48, 46, 44, 42, 40, 38, 36]) 
    config4.demand = np.array([125, 137.5, 150, 162.5, 180.8, 199.1, 217.5, 239.4, 261.3, 283.2, 305.1, 327, 348.8])
    config4.N = len(config4.price)  # Update N as well
    model = create_or_update_model(model, config4, True)
    solve_and_print(model, "Different Prices")

if __name__ == "__main__":
    main()