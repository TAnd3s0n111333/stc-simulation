import pulp

def add_labor_constraint(prob, valid_modules, vars, colonists, robots):
    """
    vars: The dictionary of module variables { 'Solar_Panel': LpVariable, ... }
    colonists: The PuLP variable for number of humans
    robots: The PuLP variable for number of robots
    """

    # Labor Logic
    total_labor_needed = pulp.lpSum([vars[m['name']] * m.get('labor_required', 1) for m in valid_modules])
    prob += (colonists * 8) + (robots * 24) >= total_labor_needed, "Labor_Constraint"
    
    # --- STEP A: CALCULATE TOTAL DEMAND (The "Holes" in the bucket) ---
    # We look at every module the solver MIGHT pick and multiply it by its labor need.
    total_labor_needed = pulp.lpSum([
        vars[m['name']] * m.get('labor_required', 0) 
        for m in valid_modules
    ])

    # --- STEP B: CALCULATE TOTAL SUPPLY (The "Filler") ---
    # Humans provide 8 hours of high-quality work.
    # Robots provide 24 hours of tireless work.
    human_supply = colonists * 8
    robot_supply = robots * 24
    
    total_labor_supply = human_supply + robot_supply

    # --- STEP C: THE LINKAGE ---
    # This is the actual constraint line. 
    # The solver cannot find a solution where this is False.
    prob += total_labor_supply >= total_labor_needed, "Labor_Staffing_Balance"

"""
Low tech:
  Humans → Operation → Output

Mid tech:
  Robots → Operation
  Humans → Maintenance

High tech:
  Automation → Operation
  Robots → Maintenance
  Humans → Oversight
"""

def labour_calculator(mass_val, com_val, size, automation):

    base_weight = 500

    if size == 'small':
        size_multi = 0.5
    elif size == 'standard':
        size_multi = 1
    elif size == "large":
        size_multi = 1.5

    if mass_val == "micro": # Sensors, tools, small mechanical parts.
        mass_scalar = 0.1
    elif mass_val == "small": # LED arrays, small pipes.
        mass_scalar = 0.5
    elif mass_val == "standard": # Oxygen recyclers, batteries.
        mass_scalar = 1
    elif mass_val == "heavy": # Sabatier reactors, smelters.
        mass_scalar = 2.5
    elif mass_val == "massive": # Solar arrays, large habitats.
        mass_scalar = 10
    
    if com_val == "very_low":
        com_scalar = 0.5
    elif com_val == "low":
        com_scalar == 1
    elif com_val == "medium":
        com_scalar == 2.5
    elif com_val == "high":
        com_scalar == 5
    elif com_val == "ultra":
        com_scalar == 10
    
    structual_parts_req = mass_scalar * base_weight * size_multi

    electronic_parts_req = size_multi * com_scalar

    return structual_parts_req, electronic_parts_req