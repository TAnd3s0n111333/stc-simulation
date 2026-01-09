# Standard library imports

# Related third-party imports
import pulp

# Local application/library specific imports

def add_power_constraint(valid_modules, agents, reqs, prob, vars):

    # Steady mods provide power regardless of time (RTGs, Sabatier if it generates power, etc)
    steady_mods = [m for m in valid_modules if "Solar_Array" not in m['name'] and "Battery" not in m['name'] and m['outputs'].get('power', 0) > 0]
    battery_mods = [m for m in valid_modules if "Battery" in m['name']]
    
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
    if reqs.get('power', {}):
        power_req = reqs.get('power', {})
        power_target = power_req.get('minimum', 0)

        if power_target > 0:
            # We look for the 'capacity' output in our battery modules
            total_capacity = pulp.lpSum([vars[m['name']] * m.get('outputs', {}).get('capacity', 0) 
                                        for m in valid_modules if "Battery" in m['name']])
            
            # The Solver is now forced to pick enough batteries to hit 200.0
            prob += total_capacity >= power_target, "Force_Power_Storage_Capacity"

        