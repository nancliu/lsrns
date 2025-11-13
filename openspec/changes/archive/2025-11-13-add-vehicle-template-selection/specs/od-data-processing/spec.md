# od-data-processing Specification

## Purpose

Define requirements for OD (Origin-Destination) data processing functionality, including vehicle template selection for configurable simulation parameters.

## ADDED Requirements

### Requirement: Vehicle Template Selection in OD Processing Form

The OD data processing form SHALL provide a dropdown selector for choosing vehicle type configuration templates, allowing users to specify different vehicle simulation parameters for different cases.

#### Scenario: Display available vehicle templates

- **GIVEN** user is on the OD data processing page
- **WHEN** the page loads
- **THEN** the system SHALL fetch available vehicle template files from `templates/config_templates/vehicle_templates/` directory
- **THEN** a dropdown selector labeled "车型配置模板" SHALL be displayed
- **THEN** the dropdown SHALL list all available `.json` files from the vehicle templates directory
- **THEN** the dropdown SHALL default to `vehicle_types.json`

#### Scenario: Select custom vehicle template

- **GIVEN** user is filling out the OD data processing form
- **WHEN** user selects a different vehicle template from the dropdown (e.g., `vehicle_types_tj1.json`)
- **THEN** the selected template filename SHALL be included in the form submission
- **THEN** the system SHALL pass the selected template path to the ODProcessor
- **THEN** OD data processing SHALL use vehicle parameters from the selected template

#### Scenario: Handle missing vehicle template gracefully

- **GIVEN** user selects a vehicle template that no longer exists
- **WHEN** processing OD data
- **THEN** the system SHALL validate template file existence before processing
- **THEN** if template is missing, the system SHALL return error: "选择的车型配置文件不存在: {filename}"
- **THEN** processing SHALL be aborted without creating a case

### Requirement: Vehicle Template Backend API Support

The backend SHALL provide an API endpoint to list available vehicle templates and accept vehicle template selection in OD processing requests.

#### Scenario: List available vehicle templates

- **GIVEN** the API is running
- **WHEN** client requests GET `/api/v1/template/vehicle`
- **THEN** the system SHALL scan `templates/config_templates/vehicle_templates/` directory
- **THEN** the response SHALL include an array of available vehicle template files
- **THEN** each entry SHALL include: `{"filename": "vehicle_types.json", "path": "templates/config_templates/vehicle_templates/vehicle_types.json"}`

#### Scenario: Accept vehicle template in OD processing request

- **GIVEN** `TimeRangeRequest` model
- **WHEN** client submits OD data processing request
- **THEN** the request MAY include optional field `vehicle_template` (string, filename or path)
- **THEN** if `vehicle_template` is provided, the system SHALL use specified template
- **THEN** if `vehicle_template` is null or empty, the system SHALL default to `vehicle_types.json`

#### Scenario: Pass vehicle template to ODProcessor

- **GIVEN** data service receives OD processing request with `vehicle_template` specified
- **WHEN** creating ODProcessor instance
- **THEN** the system SHALL construct full path: `templates/config_templates/vehicle_templates/{vehicle_template}`
- **THEN** the system SHALL initialize ODProcessor with `vehicle_config_path` parameter
- **THEN** ODProcessor SHALL load vehicle types from the specified template

### Requirement: Store Vehicle Template Choice in Case Metadata

The case metadata SHALL record which vehicle template was used during OD data processing for traceability and reproducibility.

#### Scenario: Save vehicle template in case metadata

- **GIVEN** OD data processing completes successfully
- **WHEN** creating case metadata
- **THEN** the metadata `templates` section SHALL include field `vehicle_template`
- **THEN** `vehicle_template` value SHALL be the filename used (e.g., `vehicle_types.json`)
- **THEN** metadata SHALL be saved to `cases/{case_id}/metadata.json`

#### Scenario: Display vehicle template in case details

- **GIVEN** user views case details
- **WHEN** displaying case metadata
- **THEN** the UI SHALL show the vehicle template used: "车型配置: {vehicle_template}"
- **THEN** if vehicle_template is not present in metadata (legacy cases), the UI SHALL show "车型配置: vehicle_types.json (默认)"

### Requirement: Backward Compatibility with Existing Cases

The system SHALL maintain backward compatibility with existing cases created before vehicle template selection was introduced.

#### Scenario: Process cases without vehicle_template field

- **GIVEN** an existing case metadata file without `vehicle_template` field
- **WHEN** running simulations or analysis on this case
- **THEN** the system SHALL assume `vehicle_types.json` as default
- **THEN** no errors SHALL occur due to missing `vehicle_template` field
- **THEN** system SHALL continue to function normally
