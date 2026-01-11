import math

def run_simulation(module_list, selected_env, n_hum, n_rob, duration_hours):
    # 1. Setup Resources and Environment
    resources = selected_env.get('initial_resources', {}).copy()
    base_tags = set(selected_env.get('tags', []))
    logs = []

    complexity_index = {
        'very_low': 0.5, # Basic structural parts, no electronics
        'low': 1, # Wires, 
        'medium': 2.5,
        'high': 5,
        'ultra': 10
    }
    
    total_labour_req = 0
    total_labour_pro = 0
    total_labour = 0

    for m in module_list:
        # 1. Extract raw data
        base_labor = 2

        comp = m.get('complexity_tier', 1.0)

        comp = complexity_index[comp[0]]

        total_labour_req += (base_labor * comp)

        total_labour_pro = (n_hum * 8) + (n_rob * 24)

        # Check if Labour Produced is Greater than Labour Required
        total_labour = total_labour_pro - total_labour_req

        resources["labour"] = total_labour
    

    duration_hours = duration_hours + 1

    for hour in range(duration_hours):
        # solar_mult: Peak at 1.0 (noon), 0.0 at night (6pm-6am)
        # Using (hour % 24) to track the daily cycle
        solar_mult = max(0, math.sin(math.pi * (hour % 24) / 12))
        
        # 2. Dynamic Tag Collection
        current_tags = base_tags.copy()
        for mod in module_list:
            for tag in mod.get('provides_tags', []):
                current_tags.add(tag)

        # 3. Calculate Power Flow & Process Non-Power Inputs
        # We separate power because it's a "use-it-or-lose-it" resource
        total_power_demand = 0
        active_modules = []

        for mod in module_list:
            req_tags = mod.get('requires_env_tags', [])
            if all(tag in current_tags for tag in req_tags):
                active_modules.append(mod)
                
                # Calculate consumption
                for res, amount in mod.get('inputs', {}).items():
                    if res == "power":
                        total_power_demand += amount
                    elif res != "solar_exposure":
                        # Non-power resources still accumulate/deplete normally
                        resources[res] = round(resources.get(res, 0) - amount, 2)

        # 4. Process Power Generation & Static Attributes
        total_power_generation = 0
        max_battery_capacity = 0 # Reset every hour to calculate current total

        for mod in active_modules:
            for res, amount in mod.get('outputs', {}).items():
                if res == "power":
                    if "Solar" in mod.get('name', ''):
                        total_power_generation += amount * solar_mult
                    else:
                        total_power_generation += amount
                elif res == "capacity":
                    # Track capacity but DON'T add it to the resources bucket
                    max_battery_capacity += amount
                elif res == "discharge_out":
                    continue # This is a rate limit, not a resource
                elif res != "habitat_space":
                    # Only add actual consumable resources (Oxygen, Food, etc.)
                    resources[res] = round(resources.get(res, 0) + amount, 2)

        # 5. The Power "Bucket" Constraint
        net_power_flow = total_power_generation - total_power_demand
        current_power = resources.get('power', 0)

        # Apply flow, but cap it at the current max_battery_capacity
        resources['power'] = round(max(0, min(current_power + net_power_flow, max_battery_capacity)), 2)

        # 6. Check for Resource Depletion
        for res, val in resources.items():
            if val < 0:
                return {
                    "success": False, "hour": hour, "resources": resources,
                    "failure_reason": f"CRITICAL FAILURE: {res} exhausted at hour {hour}.",
                    "logs": logs
                }
        
        # If power dropped to 0 and we have a deficit, we failed the night
        if resources['power'] <= 0 and net_power_flow < 0:
             return {
                "success": False, "hour": hour, "resources": resources,
                "failure_reason": f"CRITICAL FAILURE: Power Grid Collapse at night.",
                "logs": logs
            }
        
        if total_labour < 0:
            return {
                "success": False, "hour": hour, "resources": resources,
                "failure_reason": f"CRITICAL FAILURE: Labour Needed exceeded Labour Provided.",
                "logs": logs
            }

        # 7. Logging
        if hour % 12 == 0:
            log_entry = f"Hour {hour:03d} | " + \
                        " | ".join([f"{k.capitalize()}: {v}" for k, v in resources.items()])
            logs.append(log_entry)
    

    return {
        "success": True, "hour": duration_hours, "resources": resources, "logs": logs
    }