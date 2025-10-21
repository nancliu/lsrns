# Feature Specification: Database-Driven Edge Selector (Phase 1B)

**Feature Branch**: `004-database-edge-selector`
**Created**: 2025-10-20
**Status**: Draft
**Input**: User description: "进行roadmap中Phase 1B边选择器功能开发，参考 docs/design/development_roadmap.md，参考 docs/design/README_edge_selector.md 和其中指向的文档"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Traffic Control Engineer Filters Road Segments for VSS Control Strategy (Priority: P1)

A traffic control engineer needs to select appropriate road segments on highway G4202 to apply Variable Speed Sign (VSS) control strategies. They need to filter segments by multiple criteria including route, direction, stake range, length, and lane count to find suitable candidates.

**Why this priority**: This is the foundational capability that all other scenarios depend on. Without multi-dimensional filtering, users cannot effectively identify target road segments for any control strategy.

**Independent Test**: Can be fully tested by submitting filter criteria through the API and verifying that returned road segments match all specified conditions. Delivers immediate value by enabling basic segment selection.

**Acceptance Scenarios**:

1. **Given** the engineer has opened the edge selector interface, **When** they select route "G4202", direction "clockwise", stake range K20-K40, length 500-2000m, and minimum 3 lanes, **Then** the system returns 10-20 road segments matching all criteria within 2 seconds.

2. **Given** the engineer has applied multiple filters, **When** they modify the stake range from K20-K40 to K25-K38, **Then** the system immediately updates the results to show only segments within the new range.

3. **Given** the engineer has filtered segments, **When** they view the results table, **Then** each segment displays edge_id, route_code, section_code, stake range, length, lane count, node type, and gantry count.

4. **Given** the engineer wants to narrow down results, **When** they enable the "only segments with gantries" filter, **Then** the system shows only segments that have at least one gantry for traffic observation.

---

### User Story 2 - Engineer Selects Toll Entrance Edges for TEC Control Strategy (Priority: P2)

A traffic control engineer needs to identify entrance ramp segments connected to toll plazas to implement Toll Entrance Control (TEC) strategies. They need to filter by node type "entrance" and optionally by TAZ (Traffic Analysis Zone) to target specific toll entrances.

**Why this priority**: TEC is a high-value traffic control scenario that requires specialized filtering capabilities. The node type filtering already exists, but TAZ integration provides enhanced precision.

**Independent Test**: Can be tested by querying entrance-type nodes on specific routes and verifying the returned segments are actual entrance ramps. Delivers value for entrance flow control scenarios.

**Acceptance Scenarios**:

1. **Given** the engineer wants to control entrance flow, **When** they filter route "G4202" with node type "entrance", **Then** the system returns all entrance ramp segments for that route.

2. **Given** the engineer has identified entrance segments, **When** they review the results, **Then** each segment shows its connection to toll plaza or TAZ information when available.

3. **Given** the engineer wants to target specific toll plazas, **When** they filter by demonstration_id associated with a toll zone, **Then** the system returns only entrance segments within that demonstration area.

---

### User Story 3 - Engineer Identifies Hard Shoulder Segments for DHS Strategy (Priority: P3)

A traffic control engineer needs to find mainroad segments with emergency lanes that can be dynamically opened during peak hours using Dynamic Hard Shoulder (DHS) control strategies. They need to filter mainroad segments with 5+ lanes that have designated emergency lanes.

**Why this priority**: DHS requires specialized lane-level data integration. While valuable for capacity management, it depends on enhanced data models and is less common than basic filtering or TEC scenarios.

**Independent Test**: Can be tested by querying mainroad segments with emergency lane requirements and verifying that returned segments have lane configurations showing disallowed emergency lanes. Delivers value for capacity optimization scenarios.

**Acceptance Scenarios**:

1. **Given** the engineer wants to implement DHS, **When** they filter route "G4202", edge type "highway.motorway", minimum 5 lanes, **Then** the system returns mainroad segments likely to have emergency lanes.

2. **Given** the engineer has identified potential DHS segments, **When** they view detailed segment information, **Then** the system shows lane count, emergency lane count, and emergency lane indexes.

3. **Given** the engineer wants precise identification, **When** they use the emergency lane filter, **Then** the system only returns segments confirmed to have emergency lanes with disallow="all" configuration.

---

### User Story 4 - Engineer Visualizes Selected Segments on Network Map (Priority: P4)

A traffic control engineer needs to see the spatial distribution of filtered road segments on a network visualization to understand their geographic relationships and connectivity before finalizing selection.

**Why this priority**: Visualization enhances user experience and decision-making but is not critical for core functionality. Users can still select segments using data tables before visualization is available.

**Independent Test**: Can be tested by displaying filtered segments on a Canvas-based network map with color highlighting and verifying that clicking segments toggles their selection state. Delivers value by improving spatial understanding.

**Acceptance Scenarios**:

1. **Given** the engineer has filtered 15 segments, **When** they view the network visualization, **Then** the system displays all 15 segments highlighted on a simplified road network map.

2. **Given** the engineer is viewing the network map, **When** they hover over a highlighted segment, **Then** a tooltip shows edge_id, stake range, length, and lane count.

3. **Given** the engineer wants to refine selection, **When** they click on specific highlighted segments in the map, **Then** the system toggles selection state and updates the selected segments list.

4. **Given** the engineer has a large network, **When** they view the visualization, **Then** the system supports pan and zoom operations with smooth performance.

---

### User Story 5 - System Supports Hierarchical Filtering (Route → Section → Edge) (Priority: P2)

A traffic control engineer needs to narrow down segment selection using a hierarchical approach: first selecting a route (e.g., G4202), then a section within that route (e.g., G4202001), then specific edges within that section.

**Why this priority**: Hierarchical filtering matches organizational management structures and significantly improves filtering efficiency by reducing result sets at each level. This is a proven effective pattern from testing.

**Independent Test**: Can be tested by first querying available sections for a route, then filtering edges within a selected section, and verifying result counts decrease appropriately at each level. Delivers value by improving filtering workflow.

**Acceptance Scenarios**:

1. **Given** the engineer selects route "G4202", **When** they request available sections, **Then** the system returns sections "G4202001" (621 edges) and "G4202002" (577 edges) with stake ranges.

2. **Given** the engineer has selected section "G4202001", **When** they apply additional filters (direction, stake range, length), **Then** the result count reduces from 621 to under 20 segments.

3. **Given** the engineer is using hierarchical filtering, **When** they change from section G4202001 to G4202002, **Then** the system maintains other filter criteria and updates results for the new section.

---

### Edge Cases

- What happens when filter criteria produce zero matching segments? → System returns empty results with a clear message "No segments match the specified criteria" without errors.
- What happens when a user selects an invalid combination of filters (e.g., min_stake > max_stake)? → System validates filter parameters and returns validation error message before querying database.
- What happens when the database connection fails during a query? → System automatically retries once after 500ms delay. If both attempts fail, system logs the error and returns a user-friendly error message "Unable to retrieve segment data, please try again."
- What happens when the user applies very broad filters returning 1000+ segments? → System returns results but displays a warning "Too many results (1000+), please add more filters to narrow down selection."
- What happens when gantry or lane data is missing for some segments? → System still returns the segment but shows gantry_count as 0 or emergency_lane_count as "unknown" with appropriate UI indicators.
- What happens when a segment has multiple node types (connected to different junction types)? → System shows the node type from the from_junction by default, with an option to see all connected node types.
- What happens when the user switches between different demonstration areas rapidly? → System debounces or cancels previous queries to show only the latest results.

## Clarifications

### Session 2025-10-20

- Q: What level of observability is required for debugging query performance and monitoring operational health? → A: Application-level logging with structured events (query params, result counts, timing, errors)
- Q: What retry strategy should be implemented for transient database connection failures? → A: Basic retry with exponential backoff (2 attempts: immediate, +500ms delay)
- Q: What authentication/authorization mechanism is required for the edge query API endpoints? → A: Read-only access, no authentication required (use existing .env database credentials)
- Q: What scaling strategy should be implemented to handle user growth beyond the initial 10 concurrent users? → A: Vertical scaling strategy with connection pooling optimization (increase pool size as needed, tune query performance)
- Q: Should response caching be implemented for frequently accessed metadata to improve performance? → A: Response caching with 5-minute TTL for metadata endpoints (routes, sections, demonstrations)

## Requirements *(mandatory)*

### Functional Requirements

**Database Query Module**

- **FR-001**: System MUST provide a query function `query_edges_with_filters()` that accepts 11 filter parameters: route_codes, section_codes, node_types, min_stake, max_stake, min_length, max_length, route_direction, demonstration_ids, min_lanes, with_gantry
- **FR-002**: System MUST query data from PostgreSQL database schema `dim` including tables: sim_network_edges, multiscale_node_units, point_gantry, sim_network_junctions
- **FR-003**: System MUST support filtering by route codes (e.g., G4202, SA2, G5) with support for multiple route selection
- **FR-004**: System MUST support filtering by section codes (e.g., G4202001, G4202002) as a hierarchical level between routes and edges
- **FR-005**: System MUST support filtering by node types: diverging (分流点), merging (汇流点), entrance (入口), exit (出口)
- **FR-006**: System MUST support filtering by stake number ranges in kilometers (e.g., K20.0 to K40.0)
- **FR-007**: System MUST support filtering by road segment length ranges in meters (e.g., 500m to 2000m)
- **FR-008**: System MUST support filtering by route direction: clockwise or counterclockwise
- **FR-009**: System MUST support filtering by minimum lane count (e.g., minimum 3 lanes)
- **FR-010**: System MUST support filtering by gantry presence (only return segments with at least one gantry)
- **FR-011**: System MUST support filtering by demonstration_ids to select predefined demonstration areas
- **FR-012**: System MUST return for each edge: edge_id, route_code, section_code, start_stake, end_stake, length, num_lanes, route_direction, node_type, gantry_count, gantry_ids
- **FR-013**: System MUST support combining multiple filter criteria with AND logic (all conditions must be met)
- **FR-014**: System MUST order query results by route_code and start_stake ascending

**Advanced Filtering API**

- **FR-015**: System MUST provide GET endpoint `/api/v1/control/edges/query` accepting all filter parameters as query strings
- **FR-016**: System MUST provide GET endpoint `/api/v1/control/edges/routes` returning available route codes
- **FR-017**: System MUST provide GET endpoint `/api/v1/control/edges/sections` returning available section codes optionally filtered by route_code
- **FR-018**: System MUST provide GET endpoint `/api/v1/control/edges/demonstrations` returning demonstration area information
- **FR-019**: System MUST validate all filter parameters and return 400 Bad Request for invalid inputs
- **FR-020**: System MUST return query results in JSON format including edges array and total_count
- **FR-021**: System MUST complete all queries within 2 seconds for typical filter combinations
- **FR-022**: System MUST support comma-separated values for multi-value parameters (e.g., route_codes=G4202,SA2)

**Special Scenario Support**

- **FR-023**: System MUST support TEC (Toll Entrance Control) scenario by filtering node_type="entrance" to identify entrance ramp segments
- **FR-024**: System SHOULD provide extended support for DHS (Dynamic Hard Shoulder) scenario including:
  - FR-024a: Filter parameter `edge_types` to distinguish highway.motorway (mainroads) from highway.motorway_link (ramps)
  - FR-024b: Query function `query_edges_with_emergency_lanes()` to identify segments with emergency lanes
  - FR-024c: Return emergency lane information: emergency_lane_count and emergency_lane_indexes
- **FR-025**: System SHOULD provide optional TAZ (Traffic Analysis Zone) filtering through demonstration_id mapping

**Frontend Filtering Interface**

- **FR-026**: System MUST provide a web-based filtering interface with controls for all 9 filter dimensions
- **FR-027**: System MUST display filter results in a table showing: edge_id, route, stake_range, length, lanes, node_type, gantry_count
- **FR-028**: System MUST allow users to select individual segments from results using checkboxes
- **FR-029**: System MUST display selected segments count and list of selected segments with removal option
- **FR-030**: System MUST provide "Reset" and "Query" buttons for filter control
- **FR-031**: System MUST display result count in real-time as "Query result: N segments"
- **FR-032**: System MUST show route dropdown populated with available routes from API
- **FR-033**: System MUST show section dropdown dynamically populated based on selected route
- **FR-034**: System MUST provide visual feedback during query execution (loading state)

**Network Visualization**

- **FR-035**: System SHOULD provide a Canvas-based network visualization showing filtered road segments
- **FR-036**: System SHOULD highlight filtered segments on the network map with distinctive colors
- **FR-037**: System SHOULD support interactive segment selection by clicking on highlighted segments
- **FR-038**: System SHOULD display tooltip on hover showing segment details
- **FR-039**: System SHOULD support pan and zoom operations on the network visualization
- **FR-040**: System SHOULD use junction coordinates from database for accurate spatial positioning

**Data Models**

- **FR-041**: System MUST define EdgeInfo model with fields: edge_id, route_code, section_code, start_stake, end_stake, length, num_lanes, route_direction, node_type, gantry_count, gantry_ids
- **FR-042**: System MUST define EdgeQueryRequest model accepting all filter parameters as optional fields
- **FR-043**: System MUST define EdgeQueryResponse model with edges array and total_count
- **FR-044**: System SHOULD define EdgeInfoWithLanes model extending EdgeInfo with: emergency_lane_count, emergency_lane_indexes for DHS scenarios

**Logging and Observability**

- **FR-045**: System MUST log all filter query operations with structured events including: timestamp, filter_parameters (route_codes, section_codes, node_types, stake_range, etc.), result_count, query_execution_time_ms
- **FR-046**: System MUST log database query errors with error_type, error_message, query_context (without exposing sensitive data)
- **FR-047**: System MUST log query performance warnings when execution time exceeds 1500ms threshold
- **FR-048**: System MUST use Python logging module with appropriate log levels: INFO for normal queries, WARNING for slow queries or large result sets, ERROR for failures
- **FR-049**: System SHOULD structure log entries as JSON-compatible format to enable future integration with log aggregation tools

**Error Handling and Resilience**

- **FR-050**: System MUST implement retry logic for database connection failures with exponential backoff: maximum 2 attempts (immediate first attempt, second attempt after 500ms delay)
- **FR-051**: System MUST distinguish between retryable errors (connection timeout, connection refused) and non-retryable errors (authentication failure, invalid query syntax)
- **FR-052**: System MUST log retry attempts including attempt_number and delay_ms for debugging purposes
- **FR-053**: System MUST return appropriate HTTP status codes: 503 Service Unavailable for database connection failures after retry exhaustion, 500 Internal Server Error for unexpected failures

**Security and Access Control**

- **FR-054**: System MUST use read-only database access through existing database connection configuration from .env file (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- **FR-055**: System MUST NOT require authentication or authorization for edge query API endpoints (internal tool assumption)
- **FR-056**: System MUST prevent SQL injection through parameterized queries using SQLAlchemy ORM or prepared statements
- **FR-057**: System MUST NOT log database credentials or sensitive connection details in any log output

**Performance and Scalability**

- **FR-058**: System MUST use SQLAlchemy connection pooling with configurable pool_size (initial: 10 connections) and max_overflow (initial: 5) to support concurrent users
- **FR-059**: System SHOULD monitor connection pool utilization through logging to identify when pool size adjustment is needed
- **FR-060**: System MUST ensure database queries use appropriate indexes on route_code, section_code, and junction-related fields to maintain <400ms query performance
- **FR-061**: System SHOULD support vertical scaling by allowing connection pool parameters to be adjusted via environment variables or configuration without code changes
- **FR-062**: System MUST implement response caching with 5-minute TTL (time-to-live) for metadata endpoints: `/api/v1/control/edges/routes`, `/api/v1/control/edges/sections`, `/api/v1/control/edges/demonstrations`
- **FR-063**: System SHOULD use in-memory caching mechanism (e.g., Python functools.lru_cache or cachetools with TTL support) to minimize external dependencies
- **FR-064**: System MUST include cache hit/miss information in structured logs for performance monitoring
- **FR-065**: System SHOULD NOT cache the main query endpoint `/api/v1/control/edges/query` as filter combinations are too diverse for effective caching

### Key Entities *(include if feature involves data)*

- **Road Edge (路段)**: Represents a directed road segment in the SUMO network. Key attributes include edge_id (unique identifier), route_code (highway route), section_code (management section), start_stake and end_stake (kilometer positions), length (meters), num_lanes (lane count), route_direction (clockwise/counterclockwise).

- **Node Unit (节点单元)**: Represents a junction or node in the road network with traffic significance. Key attributes include unit_id, junction_id, node_type (diverging/merging/entrance/exit), connected_edge_ids. Used to identify critical points like merging/diverging zones and entrance/exit ramps.

- **Gantry Point (门架点)**: Represents a gantry structure on the road with traffic observation equipment. Key attributes include gantry_id, gantry_stake (position in kilometers), route_code. Used for validating segments that have observation data.

- **Demonstration Area (示范段)**: Represents a predefined road section for traffic control demonstrations. Key attributes include demonstration_id, route_code, edge_count, stake_range. Provides quick selection of known operational areas.

- **Road Section (路段)**: Represents a management unit grouping multiple edges. Key attributes include section_code, route_code, min_stake, max_stake, edge_count. Serves as hierarchical filtering level between routes and edges.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can narrow down road segment selection from 1000+ candidates to under 20 target segments using multi-dimensional filtering
- **SC-002**: System responds to filter queries in under 2 seconds for 95% of requests
- **SC-003**: System achieves 100% data accuracy for all returned edge attributes (route_code, stake_range, length, lanes, gantry_count)
- **SC-004**: Users can successfully identify entrance ramp segments for TEC scenarios with 100% precision (all returned segments are actual entrance ramps)
- **SC-005**: System supports at least 8 distinct routes with accurate hierarchical filtering (route → section → edge)
- **SC-006**: Filter result counts decrease predictably at each hierarchical level: route (~1000 edges) → section (~600 edges) → filtered edges (~10-20 edges)
- **SC-007**: System handles edge cases gracefully with zero crashes or unhandled errors during filter operations
- **SC-008**: 90% of users can complete segment selection task within 3 minutes using the filtering interface
- **SC-009**: Database query performance remains under 400ms even for complex multi-dimensional queries with JOINs
- **SC-010**: System correctly identifies and returns gantry information for 100% of segments that have gantries

### Assumptions

1. **Database Schema Stability**: The dim schema tables (sim_network_edges, multiscale_node_units, point_gantry, sim_network_junctions) are stable and will not undergo major structural changes during development.

2. **Data Quality**: The data in the database is accurate and complete. Specifically:
   - All edges have valid route_code and section_code
   - Stake numbers (start_stake, end_stake) are accurate and in kilometers
   - Node types in multiscale_node_units accurately reflect junction characteristics
   - Gantry positions (gantry_stake) correctly correspond to edge stake ranges

3. **Database Performance**: The PostgreSQL database can handle concurrent queries with reasonable performance. Basic indexes on route_code, section_code, and junction fields are in place or can be added.

4. **Network Connectivity**: The frontend application has stable network connectivity to the backend API server.

5. **Browser Support**: Users access the filtering interface using modern web browsers (Chrome, Firefox, Edge, Safari) that support HTML5 Canvas for visualization.

6. **SUMO Data Accuracy**: The SUMO network data accurately represents the real-world road network topology, including junction positions for visualization.

7. **User Expertise**: Primary users are traffic control engineers with basic understanding of highway route codes, stake numbers, and traffic control concepts.

8. **Deployment Environment**: The system runs on Windows 10/11 with Python 3.10+ and has access to the configured PostgreSQL database at 10.149.235.123.

9. **Lane Data Availability**: For DHS scenarios, the sim_network_lanes table contains accurate lane-level configuration including disallow attributes for emergency lanes.

10. **TAZ Data Completeness**: The taz_demonstration_mapping table contains sufficient data to support TEC scenarios through demonstration_id filtering, even if direct TAZ filtering is not implemented initially.

### Constraints

1. **Database Schema**: Must work with existing dim schema tables without requiring structural modifications (read-only access pattern).

2. **Query Performance**: All database queries must complete within 2 seconds to maintain acceptable user experience.

3. **Result Set Size**: Filter results should be limited to avoid overwhelming users - warn when results exceed 50 segments, recommend additional filtering when exceeding 100.

4. **Backward Compatibility**: New API endpoints must follow existing project conventions (FastAPI, Pydantic models, /api/v1/ prefix).

5. **Deployment**: Solution must work within the existing OD_SIM project structure without requiring new external dependencies beyond standard Python scientific stack.

6. **Technology Stack**: Must use Python 3.10+, FastAPI for backend, vanilla JavaScript/Canvas for frontend visualization (no external mapping libraries).

7. **Database Access**: Must use existing database connection configuration from .env file and shared/data_access/connection.py.

8. **Data Privacy**: No sensitive traffic data should be logged or exposed through error messages. Database credentials must never appear in logs.

9. **Security Model**: No authentication required for API endpoints (internal tool for traffic engineers with network access to application server).

10. **Concurrent Users**: System should support at least 10 concurrent users performing filter operations without significant performance degradation. Vertical scaling approach: increase connection pool size and optimize query performance as user base grows to 50+ users.

11. **Incremental Delivery**: Feature must be deliverable in phases - core filtering (P1), TEC support (P2), DHS support (P3), visualization (P4) - with each phase independently usable.
