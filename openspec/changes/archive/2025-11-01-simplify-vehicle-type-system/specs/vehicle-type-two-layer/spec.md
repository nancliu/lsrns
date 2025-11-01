# Spec: Vehicle Type Two-Layer System

**Capability**: `vehicle-type-two-layer`
**Related Change**: `simplify-vehicle-type-system`
**Status**: Draft

## ADDED Requirements

### Requirement VT-001: Fixed Two-Layer Vehicle Type Model

**Priority**: P0
**Category**: Data Model

The system SHALL implement a fixed two-layer vehicle type model:
- **Layer 1 (User Interface)**: 3 high-level categories (客车/货车/特种车辆)
- **Layer 2 (SUMO Simulation)**: 6 detailed types (auto-mapped from categories)

#### Scenario: User selects passenger category
**Given** a user is configuring a DHS strategy
**And** the vehicle type selection UI is displayed
**When** the user checks the "客车 (passenger)" checkbox
**Then** the system SHALL automatically map to `["passenger_small", "passenger_large"]`
**And** both detailed types SHALL be used in SUMO simulation

#### Scenario: User selects multiple categories
**Given** a user is configuring a TEC strategy
**When** the user checks "客车 (passenger)" and "货车 (truck)"
**Then** the system SHALL expand to `["passenger_small", "passenger_large", "truck_small", "truck_large"]`
**And** the expansion SHALL occur on the backend before saving

#### Scenario: Category-to-detailed mapping is consistent
**Given** the vehicle type hierarchy is defined in `vehicle_types_enum.json`
**When** a category is expanded
**Then** the mapping SHALL always produce the same detailed types
**And** the mapping SHALL be:
- `passenger` → `["passenger_small", "passenger_large"]`
- `truck` → `["truck_small", "truck_large"]`
- `delivery` → `["special_small", "special_large"]`

---

### Requirement VT-002: Single Source of Truth - vehicle_types.json

**Priority**: P0
**Category**: Architecture

The SUMO vehicle configuration file (`templates/config_templates/vehicle_templates/vehicle_types.json`) SHALL be the single source of truth for all vehicle type definitions.

#### Scenario: Frontend loads vehicle types from API
**Given** the frontend strategy configuration page is loaded
**When** the vehicle type selection UI is rendered
**Then** the vehicle types SHALL be loaded from the template API's `enum_values` field
**And** NO hardcoded vehicle type lists SHALL exist in frontend code

#### Scenario: Enum definition references SUMO configuration
**Given** `vehicle_types_enum.json` defines the category-to-detailed mapping
**When** a new detailed vehicle type is added to `vehicle_types.json`
**Then** the corresponding category in `vehicle_types_enum.json` SHALL be updated
**And** the `includes` array SHALL contain all valid detailed types from `vehicle_types.json`

#### Scenario: Validation against SUMO configuration
**Given** a strategy instance is being created with vehicle types
**When** the backend expands categories to detailed types
**Then** all resulting detailed types SHALL exist in `vehicle_types.json`
**And** invalid types SHALL be rejected with a clear error message

---

### Requirement VT-003: Backend Auto-Expansion Logic

**Priority**: P0
**Category**: Business Logic

The backend SHALL automatically expand high-level vehicle type categories to detailed SUMO vehicle types when creating or updating strategy instances.

#### Scenario: Category expansion during strategy creation
**Given** a user submits a strategy instance with `allowed_vehicle_types: ["passenger"]`
**When** the backend processes the creation request
**Then** the backend SHALL call `expand_vehicle_types(["passenger"])`
**And** the resulting value SHALL be `["passenger_large", "passenger_small"]` (sorted)
**And** the expanded value SHALL be saved to the strategy instance

#### Scenario: Preserve user selection for reference
**Given** a user submits a strategy with `allowed_vehicle_types: ["passenger", "truck"]`
**When** the backend expands the categories
**Then** the system SHALL save two fields:
- `allowed_vehicle_types`: expanded detailed types (4 items)
- `allowed_vehicle_types_user_selection`: original user input (2 items)
**And** both fields SHALL be persisted in the strategy instance JSON

#### Scenario: Mixed input support (category + detailed)
**Given** a user provides `allowed_vehicle_types: ["passenger", "truck_small"]`
**When** the backend expands the input
**Then** the result SHALL be `["passenger_large", "passenger_small", "truck_small"]`
**And** duplicate types SHALL be removed

#### Scenario: Invalid vehicle type rejection
**Given** a user provides `allowed_vehicle_types: ["bus", "invalid_type"]`
**When** the backend validates the input
**Then** the system SHALL raise a `ValueError` with message "Invalid vehicle types: ['bus', 'invalid_type']"
**And** the strategy instance SHALL NOT be created

---

### Requirement VT-004: Frontend Vehicle Type Selection UI

**Priority**: P1
**Category**: User Interface

The frontend SHALL display exactly 3 vehicle type checkboxes with clear descriptions of the included detailed types.

#### Scenario: Render 3 category checkboxes only
**Given** a user navigates to Step 3 of strategy configuration
**When** the vehicle type selection UI is rendered
**Then** exactly 3 checkboxes SHALL be displayed
**And** the labels SHALL be: "客车", "货车", "特种车辆"
**And** no detailed vehicle type checkboxes (e.g., "passenger_small") SHALL be displayed

#### Scenario: Display included types hint
**Given** the vehicle type selection UI is rendered
**When** a user hovers over the "客车 (passenger)" checkbox
**Then** a tooltip SHALL display: "包含: 小型客车, 大型客车\n示例ID: k1, k2, k3, k4"
**And** the label SHALL show "(2种)" to indicate the number of included types

#### Scenario: Load enum values from API
**Given** the template API returns `enum_values` for `allowed_vehicle_types`
**When** the frontend renders the vehicle type selection
**Then** the checkboxes SHALL be generated from `template.parameters_schema[].enum_values`
**And** if `enum_values` is missing, a default 3-category fallback SHALL be used

#### Scenario: Submit selected categories to backend
**Given** a user selects "客车" and "货车"
**When** the user clicks "创建策略"
**Then** the frontend SHALL submit `allowed_vehicle_types: ["passenger", "truck"]`
**And** the backend SHALL handle the expansion

---

### Requirement VT-005: API Response Format

**Priority**: P1
**Category**: API Contract

The template API (`GET /api/v1/control/templates/{template_id}`) SHALL return vehicle type enum values in the `parameters_schema[].enum_values` field.

#### Scenario: Template API includes enum_values
**Given** a client requests `GET /api/v1/control/templates/dhs_peak_hours`
**When** the API processes the request
**Then** the response SHALL include:
```json
{
  "parameters_schema": [
    {
      "parameter_name": "allowed_vehicle_types",
      "parameter_type": "enum_array",
      "enum_name": "vehicle_types_category",
      "enum_values": [
        {
          "value": "passenger",
          "label": "客车",
          "includes": ["passenger_small", "passenger_large"],
          "example_ids": ["k1", "k2", "k3", "k4"],
          "color": "yellow"
        },
        ...
      ]
    }
  ]
}
```

#### Scenario: Enum values loaded from configuration file
**Given** the template parameter references `enum_name: "vehicle_types_category"`
**When** the API builds the response
**Then** it SHALL load enum values from `control_data/templates/common/vehicle_types_enum.json`
**And** the `enums.vehicle_types_category.values` array SHALL be returned as `enum_values`

---

### Requirement VT-006: Data Consistency Validation

**Priority**: P1
**Category**: Quality Assurance

The system SHALL enforce consistency between `vehicle_types.json` and `vehicle_types_enum.json`.

#### Scenario: Enum includes matches SUMO configuration
**Given** `vehicle_types_enum.json` defines `passenger.includes: ["passenger_small", "passenger_large"]`
**When** the system validates the configuration
**Then** both "passenger_small" and "passenger_large" SHALL exist in `vehicle_types.json`
**And** both SHALL have `category: "passenger"`

#### Scenario: No orphaned detailed types
**Given** `vehicle_types.json` defines 6 detailed types
**When** all categories in `vehicle_types_enum.json` are checked
**Then** every detailed type SHALL be referenced in exactly one category's `includes` array

#### Scenario: Category field consistency
**Given** a detailed type `passenger_small` in `vehicle_types.json`
**When** its `category` field is validated
**Then** the category value SHALL match a key in `vehicle_types_enum.json`
**And** the type SHALL appear in that category's `includes` array

---

## MODIFIED Requirements

### Requirement VT-MOD-001: Strategy Template Vehicle Type Parameters

**Change Type**: Specification Refinement

**Before**:
Strategy templates MAY include vehicle type parameters with any enum definition.

**After**:
All strategy templates with vehicle type parameters SHALL use the `vehicle_types_category` enum exclusively.

#### Scenario: DHS template uses category enum
**Given** the DHS strategy template defines `allowed_vehicle_types` parameter
**When** the template JSON is loaded
**Then** the parameter SHALL specify `enum_name: "vehicle_types_category"`
**And** NOT `enum_name: "vehicle_types_detailed"` or any other enum

#### Scenario: Default value uses categories
**Given** a strategy template defines a vehicle type parameter
**When** the `default_value` is specified
**Then** it SHALL use category values (e.g., `["passenger", "truck"]`)
**And** NOT detailed type values (e.g., `["passenger_small"]`)

---

## REMOVED Requirements

### Requirement VT-REM-001: Support for bus/emergency/authority Types

**Reason**: Not used in this project (fixed 3-category model)

**Before**:
The system SHALL support 6 vehicle type categories: passenger, truck, delivery, bus, emergency, authority.

**After**:
The system SHALL support exactly 3 vehicle type categories: passenger, truck, delivery.

#### Scenario: Reject unsupported vehicle types
**Given** a user attempts to select "bus" or "emergency"
**When** the backend validates the input
**Then** the system SHALL reject the request with error "Vehicle type 'bus' is not supported"

---

### Requirement VT-REM-002: Frontend Hardcoded Vehicle Type Lists

**Reason**: Violates single source of truth principle

**Before**:
The frontend MAY define a fallback hardcoded list of vehicle types in `templates.html`.

**After**:
The frontend SHALL NOT contain any hardcoded vehicle type lists. All vehicle types SHALL be loaded from the API.

#### Scenario: No hardcoded lists in frontend code
**Given** a code review of `frontend/control/templates.html`
**When** searching for hardcoded vehicle type arrays
**Then** NO arrays like `const vehicleTypes = [...]` SHALL exist in lines 890-902
**And** vehicle types SHALL be loaded from `template.parameters_schema[].enum_values`

---

## Non-Functional Requirements

### NFR-001: Performance

**Priority**: P1

The vehicle type expansion logic SHALL complete in less than 10ms for up to 10 categories.

#### Scenario: Fast expansion for typical input
**Given** a strategy instance with `allowed_vehicle_types: ["passenger", "truck", "delivery"]`
**When** the backend calls `expand_vehicle_types()`
**Then** the function SHALL return within 10ms
**And** the result SHALL contain all 6 detailed types

---

### NFR-002: Backward Compatibility

**Priority**: P0

Existing strategy instances with detailed vehicle types SHALL remain valid and functional.

#### Scenario: Load existing strategy with detailed types
**Given** an existing strategy instance created before this change
**And** it has `allowed_vehicle_types: ["passenger_small", "truck_large"]`
**When** the system loads and displays the strategy
**Then** the vehicle types SHALL be displayed correctly
**And** the strategy SHALL be editable
**And** the types SHALL remain unchanged unless the user modifies them

---

## Cross-Reference

**Related Capabilities**:
- `strategy-parameter-configuration` (depends on this)
- `template-management` (provides enum values)

**Related Changes**:
- `refactor-strategy-parameter-configuration` (Phase 1-10) - prerequisite

---

## Validation Checklist

- [ ] All ADDED requirements have at least one scenario
- [ ] All MODIFIED requirements explain before/after state
- [ ] All REMOVED requirements justify the removal
- [ ] Scenarios are testable and specific
- [ ] No hardcoded implementation details in requirements
- [ ] Cross-references to related capabilities are complete
