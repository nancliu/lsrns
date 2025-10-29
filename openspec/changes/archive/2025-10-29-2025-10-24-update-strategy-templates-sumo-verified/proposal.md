# Update Strategy Templates Based on SUMO Verification

## Why

**Problem**: Current strategy templates were created before comprehensive SUMO validation. They contain abstract parameter definitions that don't fully reflect SUMO's actual XML element requirements and constraints. This causes friction during strategy instance creation and Additional file generation.

**Evidence from SUMO Verification** (`docs/design/sumo_control_strategies_research.md`):
- VSS uses SUMO 1.18+ `<variableSpeedSign>` with speed steps defined as `<step time="X" speed="Y"/>`
- DHS uses `<closingLaneReroute>` within `<rerouter>` intervals with vehicle type restrictions
- TEC uses `<calibrator>` with flow intervals defining vehicle counts and speeds (not just percentage-based)
- Time values in XML are in seconds (simulation time), not hours
- Vehicle types in SUMO use specific enum values, not arbitrary strings

**Opportunity**: Align templates with SUMO's actual requirements to:
- Reduce parameter validation errors during strategy creation
- Improve UI guidance with proper parameter types and units
- Enable better real-time XML preview during configuration
- Support advanced features (speed steps, vehicle type filtering) that are now verified

## What Changes

### New Capabilities
- **SUMO-Aligned Templates**: 5 strategy templates refined based on SUMO v1.19 verification
- **Enhanced Parameter Schema**: Parameter definitions now include SUMO-specific constraints:
  - Time unit conversion helpers (hours ↔ seconds)
  - Vehicle type enum validation
  - Speed value ranges based on SUMO testing
  - Lane index specifications for hard shoulder operations
- **Improved UI Parameter Form**: Dynamic form generation with:
  - Time interval visual editor (graphical time range picker)
  - Vehicle type multi-select with SUMO standard names
  - Real-time validation with SUMO-specific error messages
  - Speed step editor for VSS (add/remove steps, preview)
- **Parameter Validation Rules**: Enhanced validation to prevent invalid XML generation

### Modified Capabilities
- **Existing Templates**: VSS, DHS, TEC templates regenerated with SUMO parameters
- **Strategy Creation UI**: Form generation now supports advanced parameter types

### Technical Details
- **Template Versions**: Updated from v1.0 → v2.0 with SUMO validation results
- **Parameters now include**:
  - Explicit time unit (seconds for SUMO, hours for display)
  - SUMO vehicle type enum: passenger, bus, truck, emergency
  - Speed step arrays for VSS (not single speed limit)
  - Lane indices for DHS (e.g., lane 3 for hard shoulder)
  - Flow rate in vehicles/hour for TEC (not percentage)
- **Backward Compatibility**: Existing strategy instances remain valid; only new creations use updated templates

## Impact

- **Affected Specs**: New `strategy-configuration` capability; Extends Phase 1B `control-strategies`
- **Affected Code**:
  - Backend: `shared/control_tools/template_parser.py`, `api/services/control_strategy_service.py`
  - Frontend: `frontend/control/js/parameter_form.js`, UI component updates
- **Data Model**: Parameter schema enriched with SUMO-specific metadata
- **API Surface**: New parameter validation endpoint (optional); GET `/api/v1/control/templates/{id}/validate-params`
- **Database Schema**: No changes (file-based storage)
- **Breaking Changes**: None for existing strategies; only affects new template-based instances
- **Testing**: 15+ unit tests for parameter validation; 10+ E2E tests for form behavior
- **Dependencies**: Aligns with Phase 2 Plan Management (which consumes these templates)
