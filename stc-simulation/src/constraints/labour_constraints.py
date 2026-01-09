import pulp
import math

def add_labor_constraint(prob, valid_modules, vars, colonists, robots):
    """
    vars: The dictionary of module variables { 'Solar_Panel': LpVariable, ... }
    colonists: The PuLP variable for number of humans
    robots: The PuLP variable for number of robots
    """

    mass_index = {
        'micro': 0.1, # Sensors, tools, small mechanical parts.
        'small': 0.5, # LED arrays, small pipes.
        'standard': 1, # Oxygen recyclers, batteries.
        'heavy': 2.5, # Sabatier reactors, smelters.
        'massive': 10 # Solar arrays, large habitats.
    }

    complexity_index = {
        'very_low': 0.5, # Basic structural parts, no electronics
        'low': 1, # Wires, 
        'medium': 2.5,
        'high': 5,
        'ultra': 10
    }

    labor_terms = []

    for m in valid_modules:

        # 1. Extract raw data
        base_labor = 2

        comp = m.get('complexity_tier', 1.0)

        comp = complexity_index[comp[0]]
        
        # 2. Apply your NEW equation
        # This determines the "Cost" of one single unit of this module
        mod_labor_coefficient = (base_labor * comp)
        
        # 3. Attach it to the PuLP variable
        labor_terms.append(vars[m['name']] * mod_labor_coefficient)

    # 4. Finalize the bucket
    total_demand = pulp.lpSum(labor_terms)
    total_supply = (colonists * 8) + (robots * 24)
    
    prob += total_supply >= total_demand, "Advanced_Labor_Constraint"
    
