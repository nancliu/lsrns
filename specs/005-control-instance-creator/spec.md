# Feature Specification: Control Strategy Instance Creator (Phase 1C)

**Feature Branch**: `005-control-instance-creator`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "继续 Phase 1C - 策略实例创建。根据开发路线图,建议进入 Phase 1C: 策略实例创建与应用：核心功能包括策略实例配置界面、策略实例管理、策略应用到仿真"

## Clarifications

### Session 2025-10-21

- Q: How should user identity be captured for the `created_by` field in strategy metadata (FR-005, FR-016, FR-020)? → A: Use system identifier (e.g., "system" or hostname) - no authentication required for Phase 1C as this is an internal tool
- Q: What logging strategy should be implemented for operational monitoring and debugging beyond delete operations (FR-020)? → A: Standard operational logging - errors, key operations (create/update/delete), performance metrics (response times), validation failures
- Q: What backup strategy should be implemented for strategy JSON files in case of disk failure or accidental deletion? → A: No automated backup for Phase 1C - rely on general system backup procedures, defer backup automation to Phase 2
- Q: How should the Phase 1C frontend be integrated with the Phase 1A template page? → A: Embedded tabs in Phase 1A template page - add "Strategy Instances" tab to existing `/control/index.html` to provide cohesive template → strategy workflow

## User Scenarios & Testing

### User Story 1 - Create Strategy Instance from Template (Priority: P1)

A traffic control engineer has selected a VSS (Variable Speed Sign) template and identified 15 road segments using the edge selector (Phase 1B). They now need to create a concrete strategy instance by filling in parameter values and associating the selected edges with the strategy.

**Why this priority**: This is the core capability that bridges template definitions (Phase 1A) and edge selection (Phase 1B) to create actionable traffic control strategies. Without this, users cannot create executable control configurations.

**Independent Test**: Can be fully tested by selecting a template, choosing edges, filling parameters, and saving the strategy instance. Verifying the saved instance contains all configuration data and can be retrieved via API.

**Acceptance Scenarios**:

1. **Given** the engineer has selected VSS moderate template and 15 edges from Phase 1B, **When** they navigate to the strategy creation form, **Then** the system dynamically generates input fields for all template parameters (speed_limit, time_intervals, affected_edges) with appropriate input types and validation rules.

2. **Given** the engineer is filling out the strategy form, **When** they enter a speed_limit value of 85 km/h, **Then** the system validates it against the template's parameter schema (min: 40, max: 120) and accepts the value without errors.

3. **Given** the engineer has filled all required parameters and selected edges, **When** they click "Create Strategy", **Then** the system saves the strategy instance to `control_data/strategies/{strategy_id}.json` and displays a success message with the new strategy ID.

4. **Given** the engineer has created a strategy instance, **When** they view the strategy list, **Then** the new strategy appears with its name, strategy type badge, affected edges count, and creation timestamp.

---

### User Story 2 - List and View Strategy Instances (Priority: P2)

After creating multiple strategy instances for different scenarios (morning peak, evening peak, incident response), a traffic control engineer needs to view all created strategies, search for specific ones, and inspect their detailed configurations.

**Why this priority**: Essential for managing multiple strategies over time. Enables users to review existing strategies before creating new ones or applying them to simulations.

**Independent Test**: Can be tested by creating 5 strategy instances and verifying they all appear in the list with correct information. Testing search and filter functionality independently.

**Acceptance Scenarios**:

1. **Given** the system has 10 strategy instances created, **When** the engineer navigates to the strategy management page, **Then** all 10 strategies are displayed in a table showing strategy_id, name, type, edges_count, created_at, and action buttons.

2. **Given** the engineer is viewing the strategy list, **When** they type "morning" in the search box, **Then** only strategies with "morning" in their name are displayed.

3. **Given** the engineer wants to see strategy details, **When** they click "View" on a strategy row, **Then** a modal dialog opens showing complete strategy information: template name, all parameter values, list of affected edges with edge details, and metadata.

4. **Given** the engineer is viewing strategy details, **When** they see the affected edges section, **Then** each edge displays its edge_id, route_code, stake_range, and length for easy verification.

---

### User Story 3 - Edit Existing Strategy Instance (Priority: P2)

A traffic control engineer realizes that a previously created VSS strategy has an incorrect time interval (set for 7-9 AM but should be 8-10 AM). They need to update the strategy parameters without recreating it from scratch.

**Why this priority**: Enables iterative refinement of strategy configurations. Avoids data loss and maintains strategy history.

**Independent Test**: Can be tested by creating a strategy, modifying its parameters through the edit form, saving changes, and verifying the updated values persist correctly.

**Acceptance Scenarios**:

1. **Given** a strategy instance exists with time_intervals set to "07:00-09:00", **When** the engineer clicks "Edit" and changes time_intervals to "08:00-10:00", **Then** the system validates the new value and saves the updated strategy.

2. **Given** the engineer is editing a strategy, **When** they modify the affected edges list by removing 3 edges, **Then** the updated strategy reflects the new edge count and only retains the remaining edges.

3. **Given** the engineer has made changes to a strategy, **When** they click "Cancel" instead of "Save", **Then** the system discards all changes and the strategy retains its original values.

4. **Given** the engineer updates a strategy's speed_limit parameter, **When** they save the changes, **Then** the system updates the strategy's `updated_at` timestamp and increments the `version` field.

---

### User Story 4 - Delete Strategy Instance (Priority: P3)

A traffic control engineer has created a test strategy for experimentation and now wants to remove it from the system to avoid clutter in the strategy list.

**Why this priority**: Important for data hygiene but lower priority than creation and editing. Users can work effectively even without delete functionality temporarily.

**Independent Test**: Can be tested by creating a strategy, deleting it, and verifying it no longer appears in the list or file system.

**Acceptance Scenarios**:

1. **Given** a strategy instance exists in the system, **When** the engineer clicks "Delete" and confirms the deletion, **Then** the system removes the strategy JSON file and updates the strategies index.

2. **Given** the engineer clicks "Delete" on a strategy, **When** a confirmation dialog appears, **Then** the engineer can choose "Cancel" to abort the deletion without removing the strategy.

3. **Given** a strategy is referenced by an existing plan (Phase 2), **When** the engineer attempts to delete it, **Then** the system displays a warning message: "Cannot delete strategy - it is used by 2 plan(s). Remove it from plans first." and prevents deletion.

---

### User Story 5 - Validate Strategy Parameters (Priority: P1)

A traffic control engineer is creating a VSS strategy and accidentally enters a speed_limit of 150 km/h, which exceeds the template's maximum allowed value of 120 km/h. The system should prevent invalid configurations.

**Why this priority**: Critical for data integrity and preventing simulation errors. Invalid parameters could cause SUMO simulation failures.

**Independent Test**: Can be tested by intentionally entering invalid values (out of range, wrong type, missing required fields) and verifying appropriate error messages appear.

**Acceptance Scenarios**:

1. **Given** the engineer is filling a speed_limit parameter with range [40, 120], **When** they enter 150, **Then** the system displays an inline validation error: "Speed limit must be between 40 and 120 km/h" and disables the Save button.

2. **Given** a parameter is marked as required in the template schema, **When** the engineer leaves it empty and attempts to save, **Then** the system highlights the field in red and displays "This field is required".

3. **Given** a parameter expects an array of time intervals, **When** the engineer enters malformed data like "8-10" instead of "08:00-10:00", **Then** the system displays a format validation error with an example of the correct format.

4. **Given** the engineer selects zero edges for a strategy, **When** they attempt to save, **Then** the system displays an error: "At least one edge must be selected for this strategy".

---

### Edge Cases

- What happens when a strategy's template no longer exists in the system? → System displays a warning badge on the strategy list indicating "Template missing" and allows viewing but not editing the strategy.
- What happens when selected edges reference edge_ids that no longer exist in the database? → System validates edge existence during save and displays warning: "3 of 15 selected edges not found in network. Do you want to remove invalid edges and continue?"
- What happens when the control_data/strategies directory doesn't exist? → System automatically creates the directory structure on first strategy creation.
- What happens when two users try to edit the same strategy simultaneously? → Last write wins (optimistic concurrency). Display warning if strategy's updated_at timestamp changed since loading the edit form.
- What happens when a strategy JSON file becomes corrupted? → System logs the error, marks the strategy as "corrupted" in the index, and excludes it from the normal list. Provides a "Recover" tool to attempt JSON repair.
- What happens when the strategies_index.json file is missing? → System automatically regenerates the index by scanning all strategy JSON files in the directory at startup.
- What happens when user creates 1000+ strategies? → System implements pagination (20 strategies per page) and provides search/filter to maintain performance.

## Requirements

### Functional Requirements

**Strategy Instance Creation**

- **FR-001**: System MUST provide a dynamic form generator that reads a template's `parameters_schema` and renders appropriate input controls for each parameter type: integer → number input, string → text input, array → multi-line textarea or tag input, boolean → checkbox
- **FR-002**: System MUST pre-populate the `affected_edges` parameter with edge IDs selected from the Phase 1B edge selector
- **FR-003**: System MUST validate all parameter values against their schema constraints: required fields, min/max ranges for numeric types, allowed_values for enums, format validation for time intervals
- **FR-004**: System MUST assign a unique `strategy_id` using format `strat_{timestamp}_{random_suffix}` (e.g., strat_20251021_a3f7b9)
- **FR-005**: System MUST save strategy instances as JSON files in `control_data/strategies/{strategy_id}.json` with structure: strategy_id, strategy_name, template_id, template_name, strategy_type, parameters (key-value pairs), affected_edges (array of edge_ids), metadata (created_at, updated_at, created_by using system identifier, version)
- **FR-006**: System MUST update the `control_data/strategies/strategies_index.json` file after each create/update/delete operation to maintain a searchable index
- **FR-007**: System MUST provide POST `/api/v1/control/strategies/` endpoint accepting StrategyCreateRequest with fields: strategy_name, template_id, parameters (JSON object), affected_edges (array of strings)
- **FR-008**: System MUST return appropriate HTTP status codes: 201 Created on success with strategy_id in response, 400 Bad Request for validation errors with detailed error messages, 404 Not Found if template_id doesn't exist

**Strategy Instance Retrieval**

- **FR-009**: System MUST provide GET `/api/v1/control/strategies/` endpoint returning paginated list of strategies with query parameters: page (default 1), page_size (default 20), search (filter by name), strategy_type (filter by type)
- **FR-010**: System MUST provide GET `/api/v1/control/strategies/{strategy_id}` endpoint returning complete strategy details including resolved edge information (edge_id, route_code, stake_range, length) by joining with database
- **FR-011**: Strategy list response MUST include for each strategy: strategy_id, strategy_name, strategy_type, template_name, edges_count, created_at, updated_at
- **FR-012**: System MUST load strategy data from both the strategy JSON file and the strategies_index.json for optimal performance (index for list view, full file for detail view)

**Strategy Instance Update**

- **FR-013**: System MUST provide PUT `/api/v1/control/strategies/{strategy_id}` endpoint accepting updated parameters and affected_edges
- **FR-014**: System MUST validate updated parameter values against the original template's schema (template_id cannot be changed after creation)
- **FR-015**: System MUST increment the `version` field and update `updated_at` timestamp on each successful update
- **FR-016**: System MUST preserve the original `created_at` and `created_by` metadata fields during updates

**Strategy Instance Deletion**

- **FR-017**: System MUST provide DELETE `/api/v1/control/strategies/{strategy_id}` endpoint that removes the strategy JSON file and updates the index
- **FR-018**: System SHOULD check if strategy is referenced by any plans (Phase 2 integration point) before deletion and return 409 Conflict if references exist
- **FR-019**: System MUST permanently remove deleted strategy files to keep the file system clean (soft delete/archive is out of scope for Phase 1C)
- **FR-020**: System MUST log all delete operations including strategy_id, strategy_name, deleted_by (system identifier), deleted_at for audit trail

**Parameter Validation**

- **FR-021**: System MUST implement frontend validation using the template's parameters_schema to provide immediate feedback before API submission
- **FR-022**: System MUST implement backend validation in `shared/control_tools/parameter_validator.py` with function `validate_strategy_parameters(template_schema, parameters)` returning validation errors if any
- **FR-023**: System MUST validate edge existence by querying the database for each edge_id in affected_edges array
- **FR-024**: System MUST validate time interval formats to match "HH:MM-HH:MM" pattern (e.g., "08:00-10:00")
- **FR-025**: System MUST validate array parameters to ensure they are non-empty when marked as required

**Frontend Strategy Management Interface**

- **FR-026**: System MUST extend Phase 1A's `/control/index.html` with a tabbed interface: "Strategy Templates" tab (existing Phase 1A content) and "Strategy Instances" tab (new Phase 1C content)
- **FR-027**: System MUST provide a strategy creation workflow within the "Strategy Instances" tab: Step 1 - Select template (link to Templates tab or dropdown), Step 2 - Select edges (Phase 1B integration), Step 3 - Fill parameters, Step 4 - Review and save
- **FR-028**: System MUST display a strategy list table with columns: Name, Type, Template, Edges Count, Created Date, Actions (View/Edit/Delete)
- **FR-029**: System MUST provide search box filtering strategies by name in real-time (client-side filter for current page)
- **FR-030**: System MUST provide strategy type filter dropdown (All/VSS/DHS/TEC) to narrow down the list
- **FR-031**: System MUST display strategy detail modal showing: Basic info (name, type, template), Parameter table (parameter name, value, unit), Affected edges table (edge_id, route, stake_range, length), Metadata (created date, last updated, version)
- **FR-032**: System MUST provide an edit form pre-populated with existing strategy values, allowing modification of strategy_name, parameters, and affected_edges
- **FR-033**: System MUST display confirmation dialog before deleting a strategy: "Are you sure you want to delete strategy '{strategy_name}'? This action cannot be undone."

**Error Handling and Edge Cases**

- **FR-034**: System MUST handle missing template gracefully by displaying "Template missing" badge on strategy list and preventing editing
- **FR-035**: System MUST validate edge_ids against the database and warn user if some edges no longer exist: "X of Y selected edges not found in network"
- **FR-036**: System MUST auto-create `control_data/strategies/` directory if it doesn't exist on first strategy creation
- **FR-037**: System MUST regenerate strategies_index.json automatically if it's missing or corrupted by scanning all .json files in the strategies directory
- **FR-038**: System MUST implement optimistic concurrency control by checking if `updated_at` timestamp changed between loading edit form and saving

**Logging & Observability**

- **FR-039**: System MUST implement standard operational logging including: error logging (exceptions, validation failures), key operation logging (strategy create/update/delete with strategy_id), performance metrics (API response times), and index regeneration events
- **FR-040**: System MUST log validation errors with details including: parameter name, invalid value, constraint violated, and error message shown to user
- **FR-041**: System MUST log performance warnings when operations exceed expected thresholds: API response >2 seconds, edge detail loading >2 seconds, index loading >1 second

**Integration Points**

- **FR-042**: System MUST integrate with Phase 1B edge selector: embed edge selector component in strategy creation Step 2, receive selected edge_ids array from edge selector
- **FR-043**: System MUST integrate with Phase 1A template system: extend `/control/index.html` with new "Strategy Instances" tab, load template details via GET `/api/v1/control/templates/{template_id}`, use template's parameters_schema for form generation
- **FR-044**: System SHOULD prepare for Phase 2 integration by including `is_used_in_plans` flag in strategy detail response (initially always false, Phase 2 will populate this). NOTE: This is SHOULD not MUST because the field is optional for Phase 1C functionality - all Phase 1C features work correctly without it. Including it now reduces future API changes but is not strictly required for current requirements.

### Key Entities

- **StrategyInstance**: Represents a concrete traffic control strategy configuration created from a template
  - Attributes: strategy_id (unique identifier), strategy_name (user-defined display name), template_id (reference to ControlTemplate), template_name (denormalized for performance), strategy_type (VSS/DHS/TEC enum, denormalized from template), parameters (JSON object with parameter_name: value pairs), affected_edges (array of edge_id strings), metadata (created_at, updated_at, created_by, version)
  - Relationships: Created from one ControlTemplate (Phase 1A), References multiple Road Edges (Phase 1B), Can be included in multiple Plans (Phase 2 future)

- **StrategyParameter**: Represents a configured parameter value within a strategy instance
  - Attributes: parameter_name (matches template schema), parameter_value (actual configured value), parameter_unit (from template schema for display)
  - Relationships: Belongs to one StrategyInstance, Definition comes from template's ParameterSchema

- **StrategyEdgeAssociation**: Represents the relationship between a strategy and affected road edges
  - Attributes: strategy_id, edge_id, edge_route_code (denormalized), edge_stake_range (denormalized), edge_length (denormalized)
  - Relationships: Links StrategyInstance to Road Edge entities from database

- **StrategyIndex**: Maintains searchable metadata for all strategies
  - Attributes: strategy_id, strategy_name, strategy_type, template_id, template_name, edges_count, created_at, updated_at, file_path (relative path to JSON file)
  - Relationships: One index entry per StrategyInstance, stored in strategies_index.json

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can create a complete strategy instance (template selection + edge selection + parameter configuration) in under 5 minutes
- **SC-002**: System validates all parameter inputs and displays error messages within 200 milliseconds of user input
- **SC-003**: Strategy list loads and displays within 1 second even with 100+ strategies (using index-based loading)
- **SC-004**: 95% of created strategies pass backend validation on first submission attempt (indicating effective frontend validation)
- **SC-005**: Strategy detail view loads complete edge information (route, stake, length) within 2 seconds
- **SC-006**: Users can successfully search and filter strategies to find a specific strategy within 10 seconds
- **SC-007**: Zero data corruption incidents in strategy JSON files during concurrent operations
- **SC-008**: 100% of invalid parameter values are caught by validation before reaching the file system
- **SC-009**: Strategy edit operations preserve 100% of metadata (created_at, created_by, original version history)
- **SC-010**: Users can successfully identify and fix configuration errors using validation error messages without requiring technical support

## Assumptions

1. **Phase 1A and 1B Complete**: Template system (Phase 1A) and edge selector (Phase 1B) are fully functional and tested. Their APIs are stable and available for integration.

2. **Template Schema Stability**: Template JSON files follow the schema defined in Phase 1A. The `parameters_schema` structure is stable and provides sufficient metadata for dynamic form generation.

3. **Edge Data Availability**: The database contains accurate and up-to-date edge information. Edge IDs returned from Phase 1B edge selector are valid and can be queried for detailed information.

4. **Single User Editing**: For Phase 1C, concurrent editing by multiple users is rare. Optimistic concurrency control (timestamp-based) is sufficient; pessimistic locking is not required.

5. **File System Performance**: The file system can handle 1000+ strategy JSON files with acceptable read/write performance. File-based storage is suitable until Phase 2 when database migration may be considered.

6. **User Expertise**: Users are traffic control engineers who understand the meaning of parameters like speed_limit, time_intervals, and can interpret validation error messages.

7. **No Multi-Language Support**: Strategy names and descriptions are in Chinese only for Phase 1C. English translation is deferred to future phases.

8. **No Version History UI**: While the system increments version numbers, displaying full version history (diff view, rollback capability) is out of scope for Phase 1C.

9. **No Collaboration Features**: Features like comments, approval workflows, or shared editing are not required in Phase 1C.

10. **Strategy Export/Import**: Exporting strategies to external formats (CSV, XML) or importing from external sources is deferred to Phase 1D or later.

11. **Backup & Disaster Recovery**: System relies on general OS-level or infrastructure-level backup procedures for the `control_data/strategies/` directory. Automated backup features are deferred to Phase 2.

## Dependencies

- **Phase 1A (Strategy Template System)**: Requires GET `/api/v1/control/templates/{template_id}` endpoint to load template details and parameters_schema. Templates must be created and validated before strategies can be created from them. Frontend extends the existing `/control/index.html` page with a new "Strategy Instances" tab alongside the "Strategy Templates" tab.

- **Phase 1B (Database Edge Selector)**: Requires edge selector frontend component to provide selected edge_ids. Requires database access to validate edge existence and retrieve edge details (route_code, stake_range, length).

- **File System Access**: Requires read/write access to `control_data/strategies/` directory for storing strategy JSON files and index.

- **Database Connection**: Requires PostgreSQL database access to validate edge_ids and retrieve edge details via `shared/data_access/edge_query.py`.

- **Frontend Framework**: Assumes existing frontend stack (HTML/CSS/JavaScript) from main OD_SIM system. Uses existing UI components and styling conventions.

- **Pydantic Models**: Requires Pydantic for request/response validation and data modeling in the API layer.

- **JSON Processing**: Requires Python's json module for reading/writing strategy files and index.

## Out of Scope

- **Strategy Versioning UI**: While version field is incremented, displaying version history, diff views, or rollback functionality is not included in Phase 1C.

- **Strategy Templates CRUD**: Creating, editing, or deleting templates through the UI is Phase 1A scope. Phase 1C only consumes existing templates.

- **SUMO Additional File Generation**: Converting strategies into SUMO XML Additional files is Phase 2 scope. Phase 1C stores strategy configurations but doesn't generate simulation files.

- **Plan Management**: Grouping strategies into plans and managing plan-strategy associations is Phase 2 scope.

- **Batch Operations**: Bulk creating, updating, or deleting multiple strategies at once is deferred to future enhancements.

- **Strategy Export/Import**: Exporting strategies to CSV/Excel or importing from external files is Phase 1D optional enhancement.

- **Strategy Sharing**: Sharing strategies between users, collaboration features, or approval workflows are future work.

- **Performance Optimization**: Advanced caching, lazy loading, or virtual scrolling for very large strategy lists (1000+) is deferred. Current implementation targets <500 strategies with acceptable performance.

- **Advanced Validation**: Cross-parameter validation (e.g., verifying that time intervals don't overlap) or SUMO-specific validation (e.g., checking if speed limit is compatible with edge type) is deferred to Phase 2.

- **Audit Log UI**: While delete operations are logged, a searchable audit log interface is not included in Phase 1C.

- **Strategy Duplication**: "Clone strategy" functionality to create a copy of an existing strategy for modification is a future enhancement.

- **Multi-select Edge Management**: Advanced edge selection features like bulk import, saved edge sets, or visual edge selection from network map are Phase 1D scope.
