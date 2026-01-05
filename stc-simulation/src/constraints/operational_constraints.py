

def filter_compatible_modules(module_input, env_data: dict) -> tuple[list, dict]:
    # SAFETY CHECK: If the user passed the dict containing "modules", extract the list
    if isinstance(module_input, dict) and 'modules' in module_input:
        module_list = module_input['modules']
    else:
        module_list = module_input

    valid_modules = []
    report = {}

    # Extract environmental constants
    env_tags = env_data.get('tags', [])
    e_temp = env_data.get('temperature', {'min': -273.15, 'max': 1000.0})
    e_atmo = env_data.get('atmosphere', {})
    e_pressure = e_atmo.get('pressure', 0.0)
    e_grav = env_data.get('gravity', 9.8)

    for module in module_list:
        # If module is still a string (key), something is wrong with the input data structure
        if not isinstance(module, dict):
            continue

        errors = []
        name = module.get('name', 'Unknown')
        
        # Check if internal
        req_tags = module.get('requires_env_tags', [])
        is_internal = 'pressurized' in req_tags

        # 1. Temperature Check (Bypassed if Internal)
        if not is_internal:
            m_temp = module.get('temp_range', [-273.15, 1000.0])
            if e_temp['min'] < m_temp[0]:
                errors.append(f"Thermal: {e_temp['min']}°C is below module limit {m_temp[0]}°C.")
            if e_temp['max'] > m_temp[1]:
                errors.append(f"Thermal: {e_temp['max']}°C is above module limit {m_temp[1]}°C.")

        # 2. Pressure Check (Bypassed if Internal)
        if not is_internal:
            m_press = module.get('pressure_range', [0.0, 10.0])
            if not (m_press[0] <= e_pressure <= m_press[1]):
                errors.append(f"Pressure: {e_pressure} bar is outside {m_press}.")

        # 3. Gravity Check (Universal)
        if e_grav > module.get('max_gravity', 20.0):
            errors.append(f"Gravity: {e_grav} exceeds limit {module.get('max_gravity')}.")

        # 4. Tag Check
        for tag in req_tags:
            if tag == 'pressurized': continue 
            if tag not in env_tags:
                errors.append(f"Tag: Missing '{tag}'.")

        if not errors:
            valid_modules.append(module)
        else:
            report[name] = errors

    print(f"{len(valid_modules)} modules passed physics checks.")
    return valid_modules, report