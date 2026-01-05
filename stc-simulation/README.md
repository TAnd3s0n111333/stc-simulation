# STC Simulation

**Simulation Framework for the Standard Template Construct**

## Overview

`stc-simulation` implements the **simulation and validation layer** of the STC.  
It evaluates how STC-defined modules, environments, and plans behave over time under realistic constraints.

Simulation is treated as a **decision-validation tool**, not a visualisation engine.

## Scope

This repository includes:
- Environment models
- Module behaviour models
- Resource and energy flow simulation
- Planning and evaluation loops
- Metrics and validation tooling

It depends on definitions from `stc-core`.

## What This Repository Is Not

- A physics-accurate game engine  
- A robotics driver stack  
- A colony visualiser  
- A finished autonomy system  

Fidelity increases incrementally across roadmap phases.

## Repository Structure

stc-simulation/
- data/ # Agent, mission, environment, and module data
- src/
    - constraints/ # Enforces global and mission constraints to the solver 
    - loaders/ # Loads yaml files for modules, environments, missions, and agents
    - planning/ # Planning and optimisation logic
    - simulation/ # State engine and time stepping
    - validators/ # Validates loaded data to strict schema structures
    - run.py # A CLI to run the individual components
- README.md
- changelog.md

## Relationship to the STC

This repository validates:
- STC module definitions
- planning decisions
- system-level interactions

All simulations conform to interfaces defined in `stc-core`.

## Status

**Phase 1 — Foundations**  
Early discrete-time simulation with simplified models.

## Roadmap Alignment

- Phase 1: single-module and small system simulations
- Phase 2: integrated multi-module planning
- Phase 3+: hardware-in-the-loop and multi-agent simulation

## License

Apache License 2.0

## Author

Toby Anderson  
Robotics & Mechatronics Engineering (AI) — Monash University