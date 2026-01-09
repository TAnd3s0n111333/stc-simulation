# Standard library imports

# Related third-party imports
import pulp

# Local application/library specific imports
from constraints.resource_constraint import add_resource_constraint
from constraints.labour_constraints import add_labor_constraint
from constraints.power_constraints import add_power_constraint

def optimize_loadout(valid_modules, environment, mission, agents):
    prob = pulp.LpProblem("Mission_Optimization", pulp.LpMinimize)

    # 1. Decision Variables
    vars = {m['name']: pulp.LpVariable(f"n_{m['name']}", lowBound=0, cat='Integer') 
            for m in valid_modules}
    colonists = pulp.LpVariable("n_colonists", lowBound=0, cat='Integer')
    robots = pulp.LpVariable("n_robots", lowBound=0, cat='Integer')
    
    # 2. Objective: Minimize total module count
    prob += pulp.lpSum([vars[m['name']] for m in valid_modules]) + colonists + robots

    # 3. Environmental & Mission Setup
    reqs = mission.get('requirements', {})
    duration = mission.get('duration_hours', 24)
    initial = environment.get('initial_resources', {})

    # 4. Define Module Subsets for Power Logic
    add_power_constraint(valid_modules, agents, reqs, prob, vars)

    add_labor_constraint(prob, valid_modules, vars, colonists, robots)

    if reqs.get('module_num'):
        module_req = reqs.get('module_num')
        module_name = module_req['metric']
        module_num = module_req['minimum']
        module_num = int(module_num)

        module_name = module_name.replace(" ", "_")
        module_name = str(module_name)

        # 1. Locate the specific data dictionary from your list
        target_data = next((m for m in valid_modules if m['name'] == module_name), None)

        # 2. Add the constraint to the solver using the name we found
        if target_data:
            prob += vars[module_name] >= module_num, 'Minimum Modules Required by Mission'


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

    # --- GENERAL RESOURCE ACCUMULATION ---
    resources = ['power', 'food', 'oxygen', 'water', 'waste', 'light', 'hydrogen']
    for res in resources:
        add_resource_constraint(prob, res, valid_modules, vars, initial, reqs, duration, agents, colonists, robots)

    # 5. Solve
    status = prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[status] == 'Optimal':
        loadout = {name: int(var.varValue) for name, var in vars.items() if var.varValue > 0}

        return loadout, int(colonists.varValue), int(robots.varValue)


    return None, 0, 0