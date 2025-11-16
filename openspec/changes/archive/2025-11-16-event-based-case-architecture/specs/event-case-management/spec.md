# Event Case Management Capability

## Overview

This capability enables event-based case creation and management, allowing multiple scenarios from the same event to share common configuration while maintaining isolated simulation environments.

---

## ADDED Requirements

### Requirement: Event Case Creation

The system SHALL support creating event-based cases that group multiple scenarios from the same traffic event.

#### Scenario: First scenario from event creates new case

**Given** a user wants to create a case from scenario `scenario_10814_vss`
**And** no case exists for event `10814`
**When** the user submits a case creation request
**Then** the system creates a new case with ID `case_event_10814`
**And** creates a config directory with network, OD, and TAZ files
**And** initiates OD data generation for the event time range
**And** creates a simulation directory `event_simulation_scenario_10814_vss`
**And** returns `is_new_case: true` in the response

#### Scenario: Subsequent scenario from same event reuses case

**Given** a case `case_event_10814` already exists
**And** contains complete config files (network, OD, TAZ)
**When** the user creates a case from scenario `scenario_10814_tec`
**Then** the system reuses the existing case `case_event_10814`
**And** skips OD data generation
**And** creates a new simulation directory `event_simulation_scenario_10814_tec`
**And** returns `is_new_case: false` in the response
**And** returns `od_generation_status: completed`

---

### Requirement: Event ID Extraction

The system SHALL extract event IDs from scenario IDs to enable case grouping.

#### Scenario: Extract event ID from valid scenario ID

**Given** a scenario ID `scenario_10814_vss`
**When** the system extracts the event ID
**Then** the event ID is `10814`

#### Scenario: Handle invalid scenario ID format

**Given** an invalid scenario ID `invalid_format`
**When** the system attempts to extract the event ID
**Then** the system raises a ValueError
**And** provides a clear error message

---

### Requirement: Case Type Detection

The system SHALL distinguish between event-based and time-based cases.

#### Scenario: Detect event-based case

**Given** a case ID `case_event_10814`
**When** the system checks the case type
**Then** the case type is `event_based`
**And** the extracted event ID is `10814`

#### Scenario: Detect time-based case

**Given** a case ID `case_20251114_170211`
**When** the system checks the case type
**Then** the case type is `time_based`
**And** no event ID is extracted

---

### Requirement: Config File Sharing

Event-based cases SHALL share configuration files across all scenarios from the same event.

#### Scenario: Multiple scenarios share config directory

**Given** scenarios `scenario_10814_vss` and `scenario_10814_tec` from event `10814`
**When** both scenarios create simulations
**Then** both reference the same config directory `cases/case_event_10814/config/`
**And** the config contains network, OD, TAZ, and edgeData files
**And** the config is created only once

---

### Requirement: Case Metadata Structure

Event-based cases SHALL track associated scenarios and simulations in metadata.

#### Scenario: Case metadata includes scenario list

**Given** an event case `case_event_10814`
**And** scenarios `scenario_10814_vss` and `scenario_10814_tec` have been created
**When** the system loads the case metadata
**Then** the metadata contains `scenarios: ["scenario_10814_vss", "scenario_10814_tec"]`
**And** the metadata contains `simulations: {...}` mapping simulation IDs to creation info

#### Scenario: Case metadata includes event information

**Given** an event case `case_event_10814`
**When** the system loads the case metadata
**Then** the metadata contains `case_type: "event_based"`
**And** the metadata contains `event_id: "10814"`
**And** the metadata contains `event_type: "01_accident"`

---

### Requirement: Config Validation

The system SHALL validate config completeness before reusing an event case.

#### Scenario: Validate complete config

**Given** a case `case_event_10814` with config directory
**And** the config contains network file `*.net.xml`
**And** the config contains routes file `*_od_*.rou.xml`
**When** the system validates the config
**Then** validation passes
**And** the case can be reused

#### Scenario: Detect incomplete config

**Given** a case `case_event_10814` with config directory
**And** the network file is missing
**When** the system validates the config
**Then** validation fails
**And** the system treats the case as new
**And** recreates the config directory

---

### Requirement: Concurrent Case Creation Handling

The system SHALL handle concurrent creation requests for the same event safely.

#### Scenario: Lock prevents race condition

**Given** two users simultaneously create cases for event `10814`
**When** both requests are processed
**Then** only one case `case_event_10814` is created
**And** the first request creates the case and config
**And** the second request reuses the existing case
**And** no config files are duplicated or corrupted

---

## MODIFIED Requirements

### Requirement: Case Creation Response Format

The case creation API response SHALL include event-based case information.

#### Scenario: Response includes case type and reuse status

**Given** a case creation request is completed
**When** the API returns the response
**Then** the response includes `case_type` field ("event_based" or "time_based")
**And** the response includes `is_new_case` field (boolean)
**And** the response includes `od_generation_status` field

---

## Related Capabilities

- [scenario-simulation](../scenario-simulation/spec.md) - Scenario simulation management
