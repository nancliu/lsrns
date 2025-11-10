# Toll Station Mapping

## Overview

This capability provides comprehensive toll station mapping data that links toll station IDs referenced in events to SUMO network elements (edge_id, junction_id, TAZ), enabling precise TEC (Toll Entrance Control) strategy generation from event data.

## ADDED Requirements

### Requirement: Toll Station Mapping CSV File

The system SHALL generate a CSV file containing toll station mappings with the following fields: toll_station_id, station_name, square_code, route_code, section_code, longitude, latitude, taz_id, entrance_exit, edge_id, and junction_id.

#### Scenario: Generate toll station mapping from database

Given toll station data exists in database tables dim.point_toll_84 and dim.point_toll_square
When the mapping generation script is executed
Then a CSV file is created at events/reference/toll_station_mapping.csv
And the CSV contains entries for all toll stations in the database
And each toll_station_id matches the last 3 digits of station_code_js

### Requirement: Toll ID Resolution

The system SHALL match event toll station IDs to database station codes by comparing the last 3 digits of station_code_js, handling leading zeros appropriately.

#### Scenario: Match event toll ID to database station

Given an event contains managed_toll_stations = "250,255,256"
And database has station_code_js = "GS5123250", "GS5123255", "GS5123256"
When toll IDs are resolved
Then the correct toll stations are identified
And their corresponding edge_ids are returned

### Requirement: Edge ID Mapping

The system SHALL map each toll station to its corresponding SUMO edge_id using TAZ definitions when available, falling back to coordinate-based matching for non-TAZ stations.

#### Scenario: Resolve toll station to edge via TAZ

Given a toll station with square_code mapped to a TAZ
And the TAZ defines a tazSource with an edge_id
When edge resolution is performed
Then the TAZ-defined edge_id is used
And the edge is validated against the network file

#### Scenario: Resolve toll station to edge via coordinates

Given a toll station without TAZ mapping
And the station has WGS84 coordinates
When edge resolution is performed
Then the nearest entrance-type edge within 500m is selected
And the edge_id is validated against dim.sim_network_edges

### Requirement: Toll Mapping Loader

The system SHALL provide a utility module to load and cache toll station mappings in memory for efficient lookup during event processing.

#### Scenario: Load toll mapping at startup

Given a valid toll_station_mapping.csv exists
When the scenario generator initializes
Then the toll mapping is loaded into memory
And subsequent lookups require no file I/O
And invalid entries are logged as warnings

## MODIFIED Requirements

### Requirement: Event Scenario Generation

The scenario generator SHALL use toll station mappings to automatically resolve toll references in events to SUMO network elements for TEC strategy creation.

#### Scenario: Generate TEC strategy from event with toll stations

Given an event with managed_toll_stations field
And toll station mapping is loaded
When a scenario is generated from the event
Then toll IDs are resolved to edge_ids
And a TEC control strategy is created with correct edges
And the additional file references the resolved edges

### Requirement: Event Injection

The event injector SHALL utilize toll station mappings when creating TEC control events, logging resolution details and handling missing mappings gracefully.

#### Scenario: Inject TEC event with toll mapping

Given an event injection request with toll station references
And some toll stations may not have mappings
When the event is injected
Then mapped stations generate TEC controls
And unmapped stations are logged as warnings
And the injection continues without failure

## Integration Points

- **Database**: Queries dim.point_toll_84, dim.point_toll_square, dim.taz_demonstration_mapping
- **TAZ File**: Parses templates/taz_files/TAZ_6.add.xml for edge validation
- **Network**: Validates against dim.sim_network_edges
- **Scenario Generator**: Updates shared/control_tools/scenario_generator.py
- **Event Injector**: Enhances shared/control_tools/event_injector.py
- **New Utilities**: Creates shared/utilities/toll_mapping_utils.py

## Validation

- All G5 toll stations must map to verified edges
- No duplicate toll_station_id entries allowed
- All edge_id values must exist in network
- TAZ associations must be validated where present
- Coordinates must be within network bounds

## Performance

- CSV loading: < 100ms for ~40 stations
- Lookup time: < 1ms per toll ID
- Memory usage: < 10KB for mapping cache
- No runtime database queries required