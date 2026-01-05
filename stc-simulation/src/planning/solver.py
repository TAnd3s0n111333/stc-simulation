import pulp

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


    
    
    
    


def add_resource_constraint(prob, resource_name, valid_modules, vars, initial, reqs, duration, valid_agents, colonists, robots):
    """
    Handles the 72-hour total resource accumulation.
    """

    c_info = next((a for a in valid_agents if a['name'] == 'human'), {})
    r_info = next((a for a in valid_agents if a['name'] == 'robotic'), {})
    
    c_drain = c_info.get('inputs', {}).get(resource_name, 0)
    r_drain = r_info.get('inputs', {}).get(resource_name, 0)

    total_agent_upkeep = (colonists * c_drain * duration) + (robots * r_drain * duration)

    res_req = reqs.get(resource_name) or reqs.get(f"{resource_name}_resilience")
    target = res_req.get('minimum', 0) if isinstance(res_req, dict) else 0
    
    net_flow = []
    # Integration of sin(x) over 24h gives an average output of ~31.8%
    SOLAR_CAPACITY_FACTOR = 0.318 

    labour_hours_required = 0

    for m in valid_modules:
        out_val = m.get('outputs', {}).get(resource_name, 0)
        in_val = m.get('inputs', {}).get(resource_name, 0)
        mass_val = m.get('mass_tier', {})
        comp_val = m.get('complexity_tier', {})

        structural_parts_req = labour_calculator(mass_val, comp_val)
        
        if resource_name == 'power' and "Solar" in m['name']:
            effective_out = out_val * SOLAR_CAPACITY_FACTOR
        else:
            effective_out = out_val

        net_contribution = vars[m['name']] * (effective_out - in_val) * duration
        net_flow.append(net_contribution)
    
    total_available = initial.get(resource_name, 0) + pulp.lpSum(net_flow) - total_agent_upkeep
    prob += total_available >= target, f"Sustain_{resource_name.capitalize()}"


def optimize_loadout(valid_modules, environment, mission, agents):
    prob = pulp.LpProblem("Mission_Optimization", pulp.LpMinimize)

    # 1. Decision Variables
    vars = {m['name']: pulp.LpVariable(f"n_{m['name']}", lowBound=0, cat='Integer') 
            for m in valid_modules}
    colonists = pulp.LpVariable("n_colonists", lowBound=1, cat='Integer') # Min 1 human
    robots = pulp.LpVariable("n_robots", lowBound=0, cat='Integer')
    
    # 2. Objective: Minimize total module count
    prob += pulp.lpSum([vars[m['name']] for m in valid_modules]) + colonists + robots

    # 3. Environmental & Mission Setup
    reqs = mission.get('requirements', {})
    duration = mission.get('duration_hours', 24)
    initial = environment.get('initial_resources', {})
    SOLAR_CAPACITY_FACTOR = 0.318

    # 4. Define Module Subsets for Power Logic
    solar_mods = [m for m in valid_modules if "Solar" in m['name']]
    # Steady mods provide power regardless of time (RTGs, Sabatier if it generates power, etc)
    steady_mods = [m for m in valid_modules if "Solar" not in m['name'] and "Battery" not in m['name'] and m['outputs'].get('power', 0) > 0]
    battery_mods = [m for m in valid_modules if "Battery" in m['name']]

    total_modules = pulp.lpSum([vars[m['name']] for m in valid_modules])
    

    # Labor Logic
    total_labor_needed = pulp.lpSum([vars[m['name']] * m.get('labor_required', 1) for m in valid_modules])
    prob += (colonists * 8) + (robots * 24) >= total_labor_needed, "Labor_Constraint"

    # --- PRESSURIZATION LINKAGE ---
    space_providers = [m for m in valid_modules if 'pressurized' in m.get('provides_tags', [])]
    space_consumers = [m for m in valid_modules if 'pressurized' in m.get('requires_env_tags', [])]

    if space_consumers:
        total_space_needed = pulp.lpSum([vars[m['name']] for m in space_consumers])
        total_space_provided = pulp.lpSum([vars[m['name']] * m.get('outputs', {}).get('habitat_space', 1) 
                                        for m in space_providers])
        prob += total_space_provided >= total_space_needed, "Habitat_Capacity_Logic"
    
    # Total humans needing a bed
    total_humans = sum([a['count'] for a in agents if a.get('category') == 'human'])

    # Total space provided by modules (Habs)
    total_space_provided = pulp.lpSum([vars[m['name']] * m.get('outputs', {}).get('habitat_space', 0) 
                                    for m in space_providers])

    # Constraint: Every human must have a pressurized spot
    prob += total_space_provided >= total_humans, "Crew_Housing_Requirement"

    # --- NIGHTTIME POWER BALANCE (The "No Storage" Rule) ---
    # This ensures the colony doesn't die at hour 13 of the simulation.
    # We define Nighttime Consumption vs Nighttime Generation/Storage.
    
    # Consumption per hour
    base_load_hourly = pulp.lpSum([vars[m['name']] * m['inputs'].get('power', 0) for m in valid_modules])
    
    # Power available at midnight: Steady Gen (RTGs) + Battery Discharge Rate
    # Note: Using 'charge_in' as the capacity limit for storage
    night_power_available = pulp.lpSum([vars[m['name']] * m['outputs'].get('power', 0) for m in steady_mods]) + \
                            pulp.lpSum([vars[m['name']] * m['outputs'].get('charge_in', 0) for m in battery_mods])

    crew_power_per_hour = sum([a.get('inputs', {}).get('power', 0) * a.get('count', 0) for a in agents])

    # Survival Constraint: Available Night Power >= Hourly Drain
    # (We simplify here: Battery Capacity must cover the drain)
    prob += night_power_available >= (base_load_hourly + crew_power_per_hour), "Nighttime_Power_Balance"

    # --- POWER RESILIENCE GOAL ---
    power_req = reqs.get('power', {})
    power_target = power_req.get('minimum', 0)

    if power_target > 0:
        # We look for the 'capacity' output in our battery modules
        total_capacity = pulp.lpSum([vars[m['name']] * m.get('outputs', {}).get('capacity', 0) 
                                    for m in valid_modules if "Battery" in m['name']])
        
        # The Solver is now forced to pick enough batteries to hit 200.0
        prob += total_capacity >= power_target, "Force_Power_Storage_Capacity"                              
    
    # --- GENERAL RESOURCE ACCUMULATION ---
    resources = ['power', 'food', 'oxygen', 'water', 'waste', 'light']
    for res in resources:
        add_resource_constraint(prob, res, valid_modules, vars, initial, reqs, duration, agents, colonists, robots)

    # 5. Solve
    status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if pulp.LpStatus[status] == 'Optimal':
        loadout = {name: int(var.varValue) for name, var in vars.items() if var.varValue > 0}
        return loadout, int(colonists.varValue), int(robots.varValue)
    
    return None