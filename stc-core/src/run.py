import sys
from jsonschema.exceptions import ValidationError

# Custom Imports
# Loaders
from loaders.environment_loader import open_environments
from loaders.module_loader import open_modules
from loaders.mission_loader import open_missions
from loaders.agent_loader import open_agents

# Validators
from validators.environment_validator import validate_environment_file
from validators.module_validator import validate_module_file
from validators.mission_validator import validate_mission_file
from validators.agent_validator import validate_agent_file

# Constraints
from constraints.operational_constraints import filter_compatible_modules

# Solver & Planning
from planning.solver import optimize_loadout

# Simulation
from simulation.engine import run_simulation

def main():
    print("==========================================")
    print("STC SYSTEM: MISSION CONTROL")
    print("==========================================\n")

    try:
        # --- PHASE 1: LOAD DATA ---
        print("--- LOAD DATA ---")
        env_data, env_schema = open_environments()
        mod_data, mod_schema = open_modules()
        mis_data, mis_schema, mission_profiles = open_missions()
        agt_data, agt_schema = open_agents()

        # --- PHASE 2: VALIDATE DATA ---
        print("\n--- VALIDATE DATA ---")
        validate_environment_file(env_data, env_schema)
        validate_module_file(mod_data, mod_schema)
        validate_mission_file(mis_data, mis_schema)
        validate_agent_file(agt_data, agt_schema)

        # --- PHASE 3: INTERACTIVE SELECTION ---

        # B. Select Mission (Goals & Duration)
        print("\n--- Available Missions ---")
        for i, mis in enumerate(mission_profiles):
            print(f"[{i}] {mis['id']} - {mis['description']}")
        
        mis_choice = int(input("Select Mission Profile: "))
        selected_mission = mission_profiles[mis_choice]
        target_environment = selected_mission['environment']

        # 2. Find the actual environment dictionary in your loaded data
        selected_env = next((e for e in env_data['environments'] if e['id'] == target_environment), None)

        if not selected_env:
            print(f"❌ ERROR: Environment '{target_environment}' not found in data.")
            sys.exit(1)

        print(f"Selected Environment: {selected_env['name']}")

        # 3. Now call the optimizer with the DICTIONARY, not the string

        modules = mod_data['modules']
        valid_agents = agt_data['agents']

        print(f"\nStep 2: Checking Physics for {len(modules)} modules")
        valid_modules, module_error_report = filter_compatible_modules(mod_data, selected_env)

        recommended_modules, n_hum, n_rob = optimize_loadout(valid_modules, selected_env, selected_mission, valid_agents)

        if recommended_modules:
            print("Optimal Loadout Found:")
            for mod_name, count in recommended_modules.items():
                print("Modules: ")
                print(f"   - {count}x {mod_name}")

            print("\nAgents: ")
            print(f"   - {n_hum}x Humans")
            print(f"   - {count}x Robots")
            
        else:
            print("❌ IMPOSSIBLE: No combination of modules can meet these goals.")
            exit()

        # --- PHASE 4: SIMULATION ---
        duration = int(selected_mission['requirements']['duration']['minimum'])

        print(f"\nStep 3: Starting {duration}-Hour Simulation...")

        # 1. RE-HYDRATE: Convert {"Solar_Array": 3} -> [Solar_Dict, Solar_Dict, Solar_Dict]
        final_sim_list = []
        for mod_name, count in recommended_modules.items():
            # Find the full dictionary in valid_modules that matches this name
            actual_module_data = next(m for m in valid_modules if m['name'] == mod_name)
            for _ in range(count):
                final_sim_list.append(actual_module_data.copy())

        # 2. RUN SIM: Pass the list of DICTIONARIES, not the dictionary of COUNTS
        sim_results = run_simulation(final_sim_list, selected_env, duration_hours=duration)

        # 3. REPORT RESULTS
        if sim_results['success']:
            print("\n✅ MISSION SUCCESSFUL")
        else:
            print(f"\n❌ MISSION FAILED: {sim_results['failure_reason']}")

        for log in sim_results['logs']:
            print(f"   {log}")

        # --- PHASE 5: FORMAL GOAL EVALUATION ---
        print("\nStep 4: Mission Goal Evaluation")
        
        # We check both if the colony survived AND if it met the mission targets
        colony_survived = sim_results['success']
        all_critical_goals_met = True
        
        # Extract requirements from mission (Oxygen, Power, etc.)
        mission_requirements = selected_mission.get('requirements', {})
        final_resources = sim_results.get('resources', {})

        print(f"{'Requirement':<20} | {'Target':<10} | {'Actual':<10} | {'Status'}")
        print("-" * 60)

        for res_name, req_data in mission_requirements.items():
            # Skip 'duration' as that is handled by the simulation loop itself
            if res_name == 'duration':
                continue
                
            target_value = req_data.get('minimum', 0)
            actual_value = final_resources.get(res_name, 0)
            
            met = actual_value >= target_value
            status = "✅ MET" if met else "❌ FAILED"
            
            if not met:
                all_critical_goals_met = False
                
            print(f"{res_name.capitalize():<20} | {target_value:<10} | {actual_value:<10} | {status}")

        # --- FINAL REPORT ---
        print("\n" + "="*42)
        if colony_survived and all_critical_goals_met:
            print("MISSION ACCOMPLISHED")
            print(f"Colony is stable after {duration} hours.")
            # Print a neat summary of final stockpiles
            for res, val in final_resources.items():
                print(f"   > {res.capitalize()}: {val}")
        else:
            print("MISSION FAILED")
            if not colony_survived:
                print(f"Cause: Structural Collapse / Resource Depletion")
                print(f"Details: {sim_results.get('failure_reason')}")
            else:
                print("Cause: Mission parameters not met.")
                print("Details: Stockpiles below required threshold for foothold.")
        print("="*42)

    except (ValueError, IndexError):
        print("❌ Selection Error: Please choose a valid number from the list.")
    except ValidationError as e:
        print(f"❌ SCHEMA ERROR: {e.message}")
    except Exception as e:
        # This will catch that 'str' object error and other data mismatches
        import traceback
        print(f"❌ SYSTEM ERROR: {e}")
        traceback.print_exc() # Useful for debugging where exactly the .get() failed

main()