# Feature Specification: Strategy Template System (Phase 1A)

**Feature Branch**: `002-strategy-template-system`
**Created**: 2025-10-19
**Status**: Draft
**Input**: User description: "实现Phase 1A策略模板系统，包括：1. 创建3个基础策略模板JSON文件（VSS可变限速、DHS动态硬路肩、TEC入口匝道控制）2. 实现TemplateLoader工具类用于加载和验证模板3. 实现GET /control/templates/和GET /control/templates/{id}两个API端点4. 前端策略管理页面显示模板列表卡片"

## Clarifications

### Session 2025-10-19

- Q: What level of logging and monitoring is required for Phase 1A to ensure operational visibility and debugging capability? → A: Standard - Log errors plus key operational events (startup template load count, API endpoint access, template retrieval)
- Q: How should the template index file be maintained and synchronized with individual template files? → A: Auto-generated - Index automatically rebuilt from template directory scan at each startup
- Q: What format should API error responses use? → A: Structured JSON - Return JSON object with fields: error (code), message (description), details (optional context)
- Q: Which UI pattern should be used to display template details when a user clicks a template card? → A: Modal dialog - Overlay that appears centered, blocking background interaction until closed
- Q: How should bilingual (English/Chinese) content be structured in template JSON files? → A: Default language only - Store only Chinese text in Phase 1A, defer English translation to future phases
- Q: Should the spec include specific parameter examples for each strategy type (VSL/DHS/TEC) based on strategy_model_design.md? → A: Yes - Include 3-5 core parameters for each strategy type to ensure testability of SC-007 and provide clear implementation direction
- Q: How many strategy templates should Phase 1A create? Should there be multiple variants per strategy type? → A: 5 templates with variants - VSS 2 variants (moderate/strict), DHS 1 template, TEC 2 variants (truck_ban/entrance_close) per development_roadmap.md; provides realistic user choice scenarios

## User Scenarios & Testing

### User Story 1 - Browse Available Strategy Templates (Priority: P1)

Traffic engineers need to discover what traffic control strategies are available in the system before they can create specific control configurations. They should be able to quickly see all template options with basic information about each strategy type.

**Why this priority**: This is the entry point for the entire traffic control workflow. Without the ability to browse templates, users cannot proceed to create strategies. It delivers immediate value by providing visibility into available options.

**Independent Test**: Can be fully tested by accessing the strategy management page and verifying that all template cards are displayed with correct information (name, type, description). No other features need to be implemented.

**Acceptance Scenarios**:

1. **Given** the system has 5 strategy templates defined (VSS moderate, VSS strict, DHS peak hours, TEC truck ban, TEC entrance close), **When** user navigates to the strategy management page, **Then** user sees 5 template cards displaying template names, types, and brief descriptions
2. **Given** templates are stored in the templates directory, **When** the API server starts, **Then** all valid templates are loaded and available for listing
3. **Given** user is viewing the template list, **When** templates are displayed, **Then** templates are grouped by strategy type (VSS, DHS, TEC) for easy navigation, with multiple variants visible under each type

---

### User Story 2 - View Detailed Template Information (Priority: P2)

After identifying a template of interest, traffic engineers need to view detailed information including parameter definitions, valid ranges, default values, and usage guidelines to understand how to configure a strategy based on this template.

**Why this priority**: This enables informed decision-making about which template to use and how to configure it. Essential for users to understand template capabilities before creating strategies.

**Independent Test**: Can be fully tested by clicking a template card and verifying that a modal dialog displays complete template information including all parameters with their schemas, descriptions, and constraints.

**Acceptance Scenarios**:

1. **Given** user is viewing the template list, **When** user clicks on a template card, **Then** a modal dialog opens showing template name, description, strategy type, and all parameter definitions
2. **Given** user is viewing template details in the modal, **When** looking at parameter definitions, **Then** each parameter shows its name, data type, valid range or options, default value, and description
3. **Given** user is viewing template details in the modal, **When** user clicks the close button, **Then** the modal closes and user returns to the template list

---

### User Story 3 - System Loads and Validates Templates (Priority: P3)

The system must automatically discover, load, and validate all template files at startup to ensure only valid templates are available to users and to provide clear error messages if templates are misconfigured.

**Why this priority**: Ensures system reliability and data integrity. Prevents runtime errors from invalid templates. While critical for system health, it's lower priority than user-facing features because it's a background operation.

**Independent Test**: Can be fully tested by intentionally creating invalid template files (missing required fields, invalid JSON syntax) and verifying that the system logs appropriate errors, rejects invalid templates, and continues to operate with valid templates only.

**Acceptance Scenarios**:

1. **Given** template files exist in the templates directory, **When** the API server starts, **Then** all templates are loaded and validated, and any validation errors are logged with specific details
2. **Given** a template file has invalid JSON syntax, **When** the system loads templates, **Then** that template is rejected, an error is logged, and other valid templates load successfully
3. **Given** a template is missing required fields (id, name, type), **When** the system validates it, **Then** the template is rejected with a specific error message indicating which fields are missing

---

### Edge Cases

- What happens when the templates directory is empty or doesn't exist? (System should create default directory and log warning, API returns empty list)
- What happens when two templates have the same ID? (System should reject duplicate, log error, keep first valid occurrence)
- What happens when a template's parameters_schema contains unsupported data types? (Template should be rejected with validation error specifying unsupported types)
- What happens when the API is called for a non-existent template ID? (Return 404 with clear error message)
- What happens when template files are modified while the system is running? (Current version: changes require server restart; future: hot reload capability)

## Requirements

### Functional Requirements

- **FR-001**: System MUST create five initial strategy templates across three strategy types: VSS with 2 variants (moderate speed control, strict speed control), DHS with 1 template (peak hours shoulder opening), and TEC with 2 variants (truck ban, entrance closure); template variants demonstrate different parameter configurations for the same strategy type
- **FR-002**: System MUST store strategy templates as JSON files in a structured directory (`templates/control_strategies/{strategy_type}/{template_name}.json`)
- **FR-003**: System MUST auto-generate a templates index file (`templates/control_strategies/templates_index.json`) at startup by scanning the template directory, ensuring the index always reflects actual template files
- **FR-004**: Each template JSON file MUST include: template_id, template_name, description, strategy_type, parameters_schema (defining configurable parameters with types, ranges, defaults), and version; parameters_schema MUST include the core parameters defined in "Strategy Type Parameter Examples" section for the respective strategy type
- **FR-005**: System MUST provide a TemplateLoader utility class (in `shared/control_tools/`) with methods to load templates, list all templates, validate template structure, and retrieve template by ID
- **FR-006**: Template validation MUST check for required fields, valid JSON syntax, supported parameter data types (integer, float, string, boolean, array), and proper schema structure
- **FR-007**: System MUST provide GET `/api/v1/control/templates/` endpoint returning list of all valid templates with summary information (id, name, type, description)
- **FR-008**: System MUST provide GET `/api/v1/control/templates/{template_id}` endpoint returning complete template details including parameters_schema
- **FR-009**: API responses MUST return appropriate HTTP status codes: 200 for success, 404 when template not found, 500 for server errors; error responses MUST use structured JSON format with fields: error (error code string), message (human-readable description), details (optional contextual information)
- **FR-010**: Frontend MUST display templates as visual cards showing template name, strategy type icon/badge, and brief description (first 100 characters)
- **FR-011**: Frontend cards MUST be clickable to open a modal dialog showing complete template information; modal MUST block background interaction and provide a close button to dismiss
- **FR-012**: Template detail view MUST display all parameters in a readable format with parameter name, type, description, valid range, and default value
- **FR-013**: System MUST load and validate templates at API server startup, logging any validation errors with specific details
- **FR-014**: Invalid templates MUST be rejected and excluded from the available templates list, with errors logged but not causing system failure
- **FR-015**: System MUST implement standard logging that includes: error logging (template validation failures, API errors), operational events (startup template load count, successful template loading), and API access logging (endpoint invocations, template ID requests)
- **FR-016**: Template variants (multiple templates of the same strategy type) MUST differ in parameter values to demonstrate different use cases; for example, VSS moderate and strict variants use different speed_limit ranges, TEC variants use different control_mode values

### Key Entities

- **ControlTemplate**: Represents a strategy template definition
  - Attributes: template_id (unique identifier), template_name (display name), description (detailed explanation), strategy_type (VSS/DHS/TEC enum), parameters_schema (JSON schema defining configurable parameters), version (template version string), created_at, updated_at
  - Relationships: Template serves as blueprint for creating Strategies (Phase 1C)

- **ParameterSchema**: Defines a configurable parameter within a template
  - Attributes: parameter_name, parameter_type (integer/float/string/boolean/array), description, required (boolean), default_value, min_value (for numeric types), max_value (for numeric types), allowed_values (for enums), unit (display unit like "km/h", "seconds")
  - Relationships: Multiple ParameterSchemas belong to one ControlTemplate

- **StrategyType**: Enumeration of supported traffic control strategies
  - Values: VSS (Variable Speed Signs), DHS (Dynamic Hard Shoulder), TEC (Toll Entrance Control)
  - Attributes: type_code, display_name, icon_name (for frontend display), description

### Strategy Type Parameter Examples

Based on highway traffic control practices (reference: `docs/design/strategy_model_design.md`), each strategy type should include the following core parameters. Phase 1A will create 5 templates demonstrating parameter variants:
- **VSS**: 2 templates showing different strictness levels (moderate: 80-100 km/h, strict: 60-80 km/h)
- **DHS**: 1 template for peak hours shoulder opening
- **TEC**: 2 templates for different control modes (truck ban vs entrance closure)

**Core parameters for each strategy type**:

**VSS (Variable Speed Signs) - 可变限速**:
- `affected_edges` (array of strings) - Road segments where speed limits apply; identifies which highway sections are under speed control
- `speed_limit` (integer, km/h) - Speed limit value to enforce; typical range 40-120 km/h
- `time_intervals` (array of time ranges) - Time periods when speed limit is active; supports peak hour and off-peak configurations
- `speed_levels` (optional array) - Graduated speed control levels (e.g., high/medium/low) for progressive speed reduction
- `applicable_vehicle_types` (optional array) - Vehicle categories subject to speed limit; defaults to all vehicles if not specified

**DHS (Dynamic Hard Shoulder) - 动态硬路肩**:
- `affected_segments` (array of strings) - Highway segments where hard shoulder can be opened; defines eligible road sections
- `opening_hours` (array of time ranges) - Time periods when hard shoulder is open to traffic; typically aligned with peak congestion hours
- `closing_hours` (array of time ranges) - Time periods when hard shoulder is closed; ensures emergency access during off-peak
- `safety_conditions` (optional object) - Prerequisites for shoulder opening (e.g., downstream capacity, incident clearance)
- `lane_usage_rules` (optional string) - Restrictions on shoulder lane use (e.g., vehicle types, speed limits)

**TEC (Toll Entrance Control) - 收费站入口管控**:
- `entrance_ids` (array of strings) - Toll entrance ramps subject to control; identifies which on-ramps are managed
- `control_mode` (enum: close/throttle/restrict) - Type of control applied: complete closure, flow rate limiting, or vehicle type restriction
- `vehicle_type_restrictions` (optional array) - Vehicle categories allowed or prohibited; used when control_mode is 'restrict'
- `time_intervals` (array of time ranges) - Time periods when entrance control is active; supports time-based traffic management
- `flow_limit` (optional integer, vehicles/hour) - Maximum entry flow rate; used when control_mode is 'throttle'

**Note**: The planning phase will refine these parameters based on SUMO capabilities and may add additional parameters as needed. These examples ensure templates are testable and provide clear implementation direction.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can view all available templates within 1 second of navigating to the strategy management page
- **SC-002**: Template detail information loads and displays within 500 milliseconds of clicking a template card
- **SC-003**: System successfully loads and validates all templates at startup within 2 seconds
- **SC-004**: Template validation correctly identifies and rejects 100% of templates with missing required fields or invalid JSON syntax during testing
- **SC-005**: API endpoints respond with correct status codes and data structure for all test scenarios (valid requests, invalid IDs, server errors)
- **SC-006**: Frontend displays all template information accurately with no missing or incorrect data compared to source template files
- **SC-007**: Users can independently identify the purpose and parameters of each template without requiring additional documentation or support

## Assumptions

- Template files will be manually created initially; automated template generation is out of scope for Phase 1A
- Template hot-reloading (detecting file changes without restart) is deferred to future phases; server restart is acceptable for template updates
- Template versioning will use simple string format (e.g., "1.0"); complex version management is out of scope
- Templates will use Chinese text only in Phase 1A; English translations and full internationalization are deferred to future phases
- Five initial templates (VSS: 2 variants, DHS: 1 template, TEC: 2 variants) are sufficient for Phase 1A to demonstrate template selection and variant comparison; additional templates can be added by following the same JSON structure
- Template icons/badges will use simple text labels initially; custom icon assets may be added later
- No authentication/authorization for viewing templates; all users can view all templates (access control deferred to Phase 1C for strategy creation)
- Templates are read-only via API; no create/update/delete endpoints for templates in Phase 1A (manual file editing only)

## Dependencies

- **Project Infrastructure**: Requires Phase 0 to be complete (directory structure, API framework, data models defined)
- **Strategy Model Design**: Template parameters based on highway traffic control practices documented in `docs/design/strategy_model_design.md`; core parameters for each strategy type (VSS/DHS/TEC) are derived from this reference
- **SUMO Knowledge**: Template parameters must align with SUMO traffic control capabilities (VSS, DHS, TEC mapping to SUMO elements)
- **Database Schema**: No database dependencies for Phase 1A (file-based storage only); future phases may migrate to database storage
- **Frontend Framework**: Assumes existing frontend stack (HTML/CSS/JavaScript) from main OD_SIM system
- **File System Access**: Requires read access to templates directory; write access not needed for runtime (only for initial template creation)

## Out of Scope

- Creating or editing templates through the UI (Phase 1A is view-only; template CRUD via UI is future work)
- Template versioning and migration (simple version strings only, no migration logic)
- Template validation beyond structural checks (e.g., validating that parameter combinations are meaningful for SUMO is deferred)
- Generating SUMO Additional files from templates (Phase 2 scope)
- Associating templates with actual road network edges (Phase 1B edge selector scope)
- Strategy instance creation from templates (Phase 1C scope)
- Multi-language support (Phase 1A uses Chinese only; English and other languages are future work)
- Template search and filtering (deferred until template count grows significantly)
- Template categories or tags beyond strategy_type
- Template preview/simulation (showing effect of template on sample network)
- Expanding template library beyond 5 initial templates (additional templates can be manually added post-Phase 1A by creating JSON files following the established structure; systematic template expansion is future work)
