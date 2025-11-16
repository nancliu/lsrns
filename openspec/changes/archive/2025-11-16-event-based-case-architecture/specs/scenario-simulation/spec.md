# Scenario Simulation Capability

## Overview

This capability manages scenario-specific simulation directories and configurations within event-based cases.

---

## ADDED Requirements

### Requirement: Simulation Directory Naming

Simulation directories for event-based cases SHALL use event-scenario naming convention.

#### Scenario: Generate simulation ID from scenario ID

**Given** a scenario ID `scenario_10814_vss`
**When** the system creates a simulation directory
**Then** the simulation ID is `event_simulation_scenario_10814_vss`
**And** the directory is created at `cases/case_event_10814/simulations/event_simulation_scenario_10814_vss/`

#### Scenario: Distinguish from time-based simulations

**Given** a time-based case `case_20251114_170211`
**When** the system creates a simulation directory
**Then** the simulation ID is `simulation_20251114_170211`
**And** does not use the event prefix

---

### Requirement: Scenario Add File Handling

Each simulation SHALL include the scenario-specific .add.xml file.

#### Scenario: Copy scenario add.xml to simulation directory

**Given** a scenario `scenario_10814_vss` in `output/scenarios/01_accident/`
**And** the scenario directory contains `scenario_accident_vss_10814.add.xml`
**When** the system creates a simulation for this scenario
**Then** the add.xml file is copied to the simulation directory
**And** the file is named `scenario_accident_vss_10814.add.xml`

#### Scenario: Handle missing scenario add.xml

**Given** a scenario directory that does not contain an add.xml file
**When** the system attempts to create a simulation
**Then** the system logs a warning
**And** continues simulation creation without the add.xml file
**And** marks the simulation as potentially incomplete

---

### Requirement: Output Directory Creation

Simulations SHALL create both edgedata and E1 detector output directories.

#### Scenario: Create both output directories

**Given** a simulation is being created
**When** the system sets up the simulation directory
**Then** an `edgedata/` directory is created
**And** an `e1/` directory is created
**And** both directories have write permissions

---

### Requirement: Simulation Metadata

Each simulation SHALL have metadata linking it to the parent case and scenario.

#### Scenario: Simulation metadata includes linkage

**Given** a simulation `event_simulation_scenario_10814_vss` in case `case_event_10814`
**When** the system creates simulation metadata
**Then** the metadata includes `simulation_id: "event_simulation_scenario_10814_vss"`
**And** the metadata includes `case_id: "case_event_10814"`
**And** the metadata includes `scenario_id: "scenario_10814_vss"`
**And** the metadata includes `event_id: "10814"`
**And** the metadata includes `strategy: "VSS"`

---

### Requirement: SUMOCFG Generation for Shared Config

The simulation sumocfg SHALL reference the shared config files correctly.

#### Scenario: SUMOCFG references shared network file

**Given** a simulation in `cases/case_event_10814/simulations/event_simulation_scenario_10814_vss/`
**And** the network file is at `cases/case_event_10814/config/sichuan202508v7.net.xml`
**When** the system generates simulation.sumocfg
**Then** the sumocfg contains `<net-file value="../../config/sichuan202508v7.net.xml"/>`

#### Scenario: SUMOCFG references shared routes file

**Given** a simulation in `cases/case_event_10814/simulations/event_simulation_scenario_10814_vss/`
**And** the routes file is at `cases/case_event_10814/config/dwd_od_weekly_xxx.rou.xml`
**When** the system generates simulation.sumocfg
**Then** the sumocfg contains `<route-files value="../../config/dwd_od_weekly_xxx.rou.xml"/>`
**And** the route file path is the actual .rou.xml file, not the database table name

---

### Requirement: Case Metadata Updates

The parent case metadata SHALL be updated when simulations are added.

#### Scenario: Add simulation to case metadata

**Given** a case `case_event_10814` with existing metadata
**And** a new simulation `event_simulation_scenario_10814_tec` is created
**When** the system updates the case metadata
**Then** `scenario_10814_tec` is added to the scenarios list (if not present)
**And** a simulation entry is added to the simulations dict with creation timestamp
**And** the `modified_at` timestamp is updated

---

## MODIFIED Requirements

### Requirement: Scenario Index Linking

Scenario index SHALL track which case and simulation each scenario belongs to.

#### Scenario: Update scenario index with case link

**Given** a scenario `scenario_10814_vss` in the scenario index
**And** a case `case_event_10814` is created for this scenario
**And** a simulation `event_simulation_scenario_10814_vss` is created
**When** the system updates the scenario index
**Then** the scenario entry includes `case_id: "case_event_10814"`
**And** the scenario entry includes `simulation_id: "event_simulation_scenario_10814_vss"`
**And** the scenario entry includes `linked_at` timestamp

---

## Related Capabilities

- [event-case-management](../event-case-management/spec.md) - Event case creation and management
