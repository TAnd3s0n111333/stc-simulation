import pulp

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

    for m in valid_modules:
        out_val = m.get('outputs', {}).get(resource_name, 0)
        in_val = m.get('inputs', {}).get(resource_name, 0)
        
        if resource_name == 'power' and "Solar" in m['name']:
            effective_out = out_val * SOLAR_CAPACITY_FACTOR
        else:
            effective_out = out_val

        net_contribution = vars[m['name']] * (effective_out - in_val) * duration
        net_flow.append(net_contribution)
    
    total_available = initial.get(resource_name, 0) + pulp.lpSum(net_flow) - total_agent_upkeep
    prob += total_available >= target, f"Sustain_{resource_name.capitalize()}"