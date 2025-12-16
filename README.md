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

