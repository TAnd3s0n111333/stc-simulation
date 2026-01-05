# C:\Projects\stc\stc-core\constraints\dependencies.py

def validate_dependencies(modules: list[dict]) -> list[str]:
    """
    Analyzes the module list for missing or circular dependencies.
    Returns a list of error strings.
    """
    errors = []
    
    # 1. Create a map of names for quick lookup and build the graph
    # module_map = { "Oxygen_Recycler": ["Power_Bus", "Structure"], ... }
    module_map = {m['name']: m.get('dependencies', []) for m in modules}
    all_module_names = set(module_map.keys())

    # --- Check 1: Missing Dependencies ---
    for mod_name, deps in module_map.items():
        for dep in deps:
            if dep not in all_module_names:
                errors.append(f"Missing Dependency: '{mod_name}' requires '{dep}', but '{dep}' is not loaded.")

    # --- Check 2: Circular Dependencies ---
    # We use a standard DFS (Depth-First Search) to find cycles
    visited = set()
    path = set()

    def has_cycle(node):
        if node in path:
            return True
        if node in visited:
            return False

        visited.add(node)
        path.add(node)

        # Check all dependencies of this module
        for neighbor in module_map.get(node, []):
            if neighbor in all_module_names: # Only check if the dep exists
                if has_cycle(neighbor):
                    return True
        
        path.remove(node)
        return False

    for mod_name in all_module_names:
        if mod_name not in visited:
            if has_cycle(mod_name):
                errors.append(f"Circular Dependency: A loop was detected involving module '{mod_name}'.")
                break # One cycle error is usually enough to stop the process

    return errors