# Strategy Templates Update - Technical Design

## Context

**Background**: Initial strategy templates (Phase 1A) were created before comprehensive SUMO validation. They used abstract parameter definitions that didn't fully align with SUMO XML requirements. SUMO research (`docs/design/sumo_control_strategies_research.md`) now provides verified specifications showing:
- Exact XML element structures for VSS, DHS, TEC
- Time units are in seconds (0-86400 per day simulation)
- Speed values are in m/s in SUMO (displayed as km/h to users)
- Vehicle types use specific SUMO enum values

**Current Pain Points**:
1. Parameter validation incomplete - users can create invalid strategies
2. No UI guidance for SUMO-specific constraints - confusing units/ranges
3. No XML preview - users don't see impact until simulation fails
4. Parameter form is generic - doesn't guide users through SUMO requirements

**Stakeholders**:
- End users: Traffic engineers creating control strategies
- Phase 2: Plan management consumes these strategies
- Phase 3: Batch simulation executes plans from these strategies
- Developers: Maintaining template definitions

## Goals

### Primary Goals
1. **SUMO Alignment**: Templates accurately reflect SUMO v1.19 XML requirements
2. **User Guidance**: UI provides clear constraints, units, and real-time validation
3. **Error Prevention**: Catch parameter errors before XML generation
4. **Debuggability**: XML preview helps users understand their configurations

### Non-Goals
- Database storage for templates (file-based sufficient)
- Template versioning/history (single active template set)
- Automatic parameter optimization (Phase 4 feature)
- Cross-strategy constraint checking (e.g., time coordination between VSS and DHS)

## Technical Decisions

### Decision 1: Template Format and Structure

**Choice**: JSON templates with enhanced metadata for SUMO mapping

**Structure**:
```json
{
  "template_id": "vss_moderate",
  "template_name": "可变限速 - 中等控制",
  "description": "...",
  "strategy_type": "VSS",
  "version": "2.0",
  "parameters_schema": [
    {
      "parameter_name": "speed_steps",
      "parameter_type": "step_array",
      "sumo_element": "step",
      "display_unit": "hours",
      "sumo_unit": "seconds",
      "conversion_factor": 3600,
      "constraints": {...}
    }
  ]
}
```

**Rationale**:
- Extends current template format minimally
- Includes SUMO mapping metadata (`sumo_element`, `sumo_unit`, `conversion_factor`)
- Separates display representation from SUMO representation
- Enables automatic form generation and XML generation

**Alternatives Considered**:
- YAML for readability: JSON is already used throughout project
- SUMO schema validation: Too complex; lenient validation sufficient
- Database templates: File-based consistent with Phase 1

### Decision 2: Parameter Type System

**Choice**: Rich parameter types matching UI needs + SUMO constraints

**Types**:
- `integer`: Whole number with optional min/max
- `number`: Float with optional precision
- `enum`: Single choice from predefined list
- `enum_array`: Multiple choices from SUMO standard enums
- `time_range_array`: Array of [start_hour, end_hour] with automatic conversion
- `step_array`: Time-ordered speed steps (VSS specific)
- `flow_interval_array`: Time-varying flow parameters (TEC specific)
- `edge_array`: SUMO network edge IDs

**Rationale**:
- Enables automatic UI control generation (dropdown for enum, spinner for integer, etc.)
- Captures semantic meaning (time_range_array → time picker; step_array → table)
- Supports SUMO conversion (hours display → seconds for XML)
- Facilitates backend validation (check enum values, time ordering)

**Implementation in Form Generator**:
```javascript
const typeToInputControl = {
  'integer': 'input[type=number]',
  'enum': 'select',
  'enum_array': 'checkboxes',
  'time_range_array': 'timeRangePicker',
  'step_array': 'stepArrayEditor',
  'edge_array': 'edgeArrayInput'
}
```

### Decision 3: Unit Conversion Strategy

**Choice**: Display in user-friendly units, convert to SUMO units at generation time

**Examples**:
- User enters: "7:00 AM" → Display as "7" (hours) → Convert to 25200 (seconds) for SUMO
- User enters: "80 km/h" → Display as "80" (km/h) → Convert to ~22.22 m/s for SUMO XML
- User enters: "180 vehicles/hour" → Store and display as 180 → SUMO uses directly

**Conversion Points**:
1. **UI Input**: User enters friendly units
2. **Parameter Validation**: Validate in display units (hour 7 vs second 25200)
3. **XML Generation**: Convert to SUMO units using `conversion_factor`
4. **Storage**: Store original display values in strategy JSON (preserve user intent)

**Rationale**:
- Users think in hours/km/h; SUMO uses seconds/m/s
- Converting at generation time prevents data loss
- Validation feedback clearer in user units ("speed 150 km/h exceeds 130" vs "41.67 m/s exceeds 36.1")
- Stored values remain interpretable by humans reading strategy JSON files

**Alternatives Considered**:
- Store in SUMO units always: Confusing for users reading strategy files
- Pre-convert on input: Hard to validate ("25200" doesn't mean much to user)
- Chosen: Display-first, convert-at-generation

### Decision 4: Form Generation and Validation Flow

**Choice**: Backend schema → Frontend form generation + Real-time validation

**Flow**:
```
1. User selects template
2. GET /api/v1/control/templates/{id} → fetch full schema with constraints
3. Frontend generates form controls based on parameter types
4. On blur/change: Validate locally (quick feedback)
5. Before submit: POST /api/v1/control/strategies/validate-params → backend validation
6. If valid: Generate XML preview, allow strategy save
7. If invalid: Show errors, prevent save
```

**Rationale**:
- Single source of truth: Backend schema definition
- Fast UX: Local validation on every field change
- Robust: Backend validation catches edge cases before XML generation
- Decoupled: UI doesn't need hardcoded validation rules

**Validation Rules (Backend)**:
- SUMO enum values: passenger, bus, truck, emergency
- Speed range: 30-130 km/h (realistic highway)
- Time range: 0-86400 seconds (24-hour day)
- Edge existence: Check against network graph
- Time ordering: Steps must be in ascending time order
- Continuous segments: DHS edges should form connected path

### Decision 5: XML Preview Implementation

**Choice**: Backend-generated XML preview shown in UI during form editing

**Approach**:
- Separate endpoint: `POST /api/v1/control/strategies/generate-xml-preview`
- Called on form changes (with debouncing to avoid spam)
- Returns generated XML fragment (not full strategy)
- Shown in read-only code viewer with syntax highlighting

**Rationale**:
- Users see impact of parameter choices in real-time
- Catches XML generation errors before strategy save
- Helps users understand SUMO element structure
- Enables debugging ("why doesn't my speed change work?")

**Performance Considerations**:
- Debounce preview generation (200ms delay after last change)
- Cache recent previews to avoid repeated generation
- Preview only if form passes local validation

**Alternatives Considered**:
- Generate XML client-side: Requires JavaScript XML generation library, harder to keep in sync
- Show preview only on save: Too late to fix issues
- Chosen: Backend generation with client-side debouncing

### Decision 6: Template Versioning

**Choice**: Single active template set (v2.0), preserve old strategy instances, allow optional upgrade

**Strategy**:
- Current templates: v2.0 (SUMO-verified)
- Existing strategies: v1.0 (still valid, preserved)
- New strategies: v2.0 only
- Upgrade path: User can "upgrade to v2.0" which recreates strategy with new schema

**Rationale**:
- Backward compatibility: Existing simulations still valid
- Forward compatibility: New features available for new strategies
- No forced migration: Users can upgrade on their schedule
- Data safety: Old strategies never overwritten

**Alternatives Considered**:
- Force upgrade all strategies: Risky, may lose user customizations
- Support both v1.0 and v2.0 in parallel: Complex, confusing
- Chosen: Preserve + optional upgrade

### Decision 7: Parameter Validation Depth

**Choice**: Lenient validation with helpful warnings; don't block valid but unusual configs

**Examples**:
- Overlapping time intervals: Warn but allow (user might want 6-10 AM coverage in early AM rush)
- Unusual speed 150 km/h: Warn but allow (might be special case)
- Discontinuous DHS edges: Warn but allow (might be intentional multi-segment)

**Rationale**:
- Users have domain expertise; may know edge cases
- Warnings guide users without blocking them
- Clear error vs warning distinction:
  - Error: Prevents save (invalid SUMO XML)
  - Warning: Allows save but alerts user

**Alternatives Considered**:
- Strict validation: Too restrictive, frustrates advanced users
- No validation: Users create broken strategies
- Chosen: Three-tier (error, warning, info)

### Decision 8: Parameter Default Values

**Choice**: Sensible defaults based on typical highway control scenarios

**Examples**:
- VSS speed: 80 km/h (moderate control, no disruption)
- VSS intervals: [[7, 9], [17, 19]] (morning/evening peaks)
- DHS hard shoulder lane: 3 (rightmost for 4-lane highway)
- DHS vehicles: [passenger, bus, truck] (exclude emergency for standard operation)
- TEC metering rate: 480 vehicles/hour base, 180 vehicles/hour peak

**Rationale**:
- Reduces user input burden
- Reflects Chinese highway operating practices
- Can be overridden by user
- Helps users understand typical values

### Decision 9: Supplementary Templates from SUMO Research

**Choice**: Expand beyond base 5 templates to include 8 supplementary templates derived from SUMO research and real-world use cases

**Supplementary Templates Rationale**:

Based on comprehensive review of `docs/design/sumo_control_strategies_research.md`, the initial 5 templates cover basic scenarios. The research document provides concrete real-world examples that justify 8 additional specialized templates:

**VSS Category (3 additional)**:
1. **Weather-Based Progressive Limiting** (from fog example in research)
   - Research example: "K10-K20雾天渐进式限速" with 6-step progression
   - 120→100→80→60→100→120 km/h pattern reflecting fog development and clearing
   - Suitable for adverse weather conditions (fog, rain, snow)

2. **Upstream Warning Speed Control** (from upstream example in research)
   - Research example: "K8-K10上游预警限速" with 5-minute early slowdown
   - Coordinated with downstream DHS opening to prevent emergency braking
   - Enables smooth traffic flow management

3. **Lane-Differentiated Speed Control** (from lane differentiation example in research)
   - Different speeds for truck lanes vs. car lanes (80 vs 100 km/h)
   - Requires multi-VSS strategy generation per lane group
   - Improves traffic class separation and reduces conflicts

**DHS Category (2 additional)**:
4. **Passenger-Only Hard Shoulder** (from vehicle restriction example in research)
   - Restricts hard shoulder to passenger + bus only
   - Bans trucks and delivery vehicles
   - Real scenario: Separate management for freight vs. passenger flow

5. **Peak-Hour Multi-Interval Management** (from multi-interval example in research)
   - 5+ intervals per day: Night(closed)→Morning peak(open)→Midday(closed)→Evening peak(open)→Night(closed)
   - Full 24-hour coverage pattern matching actual highway operations
   - Prevents gaps or overlaps in control logic

**TEC Category (3 additional)**:
6. **Ramp Metering with Time-Varying Flow Rates** (from metering example in research)
   - 5 flow intervals: 480→180→480→300→480 vehsPerHour
   - Matches actual demand patterns (low night → high morning peak → lower evening)
   - Each interval includes entry speed calibration

7. **Truck Ban During Peak Hours** (from restriction example in research)
   - 1-3 entrance edges per toll station
   - Disallow truck+trailer during morning (7-9) and evening (17-19) peaks
   - Reflects actual highway management policies in China

8. **Full Entrance Closure** (from closure example in research)
   - Complete blockage (allowed_types empty = all vehicles blocked)
   - Supports reason field (maintenance, emergency, congestion relief)
   - 1-4 hour typical duration

**Implementation Strategy**:
- Each supplementary template follows same v2.0 schema as base templates
- Parameter validation rules consistent across all templates
- UI generation handles all parameter types uniformly
- Backward compatibility maintained (v1.0 strategies unaffected)

**Total Template Count**: 13 templates (5 base + 8 supplementary)
- VSS: 5 templates
- DHS: 3 templates
- TEC: 5 templates

**Rationale for Supplementary Approach**:
- Research document provides validated examples with concrete parameter values
- Real-world scenarios justify specialized template support
- Reduces user configuration burden for common patterns
- Enables advanced users to implement sophisticated control strategies
- Does not break existing functionality or strategy instances

## Architecture Diagram

```
┌─ API Layer ──────────────────────────────────────────┐
│                                                       │
│  ┌─ control_strategy_routes.py                     │
│  │   GET /api/v1/control/templates/                │
│  │   GET /api/v1/control/templates/{id}            │
│  │   POST /api/v1/control/strategies/validate-params
│  │   POST /api/v1/control/strategies/generate-xml  │
│  └─→ Calls control_strategy_service                │
│                                                       │
└─────────────────────────────────────────────────────┘
          ↓
┌─ Service Layer ──────────────────────────────────────┐
│                                                       │
│  ┌─ control_strategy_service.py                    │
│  │   - load_template(template_id)                  │
│  │   - validate_parameters(template_id, params)    │
│  │   - generate_strategy_xml(params)               │
│  │   - convert_parameters_to_sumo(params)          │
│  └─→ Calls parameter_validator                    │
│  └─→ Calls additional_generator                    │
│                                                       │
└─────────────────────────────────────────────────────┘
          ↓
┌─ Utility Layer ───────────────────────────────────────┐
│                                                       │
│  ┌─ template_parser.py (enhanced)                   │
│  │   - load_template_with_schema()                  │
│  │   - parse_parameter_schema()                     │
│  │   - get_template_list()                          │
│  │                                                  │
│  ├─ parameter_validator.py (new)                    │
│  │   - validate_parameter_value(param, value)      │
│  │   - validate_parameter_set(template, params)    │
│  │   - check_constraints(param_type, value)        │
│  │   - convert_display_to_sumo(value, param)      │
│  │                                                  │
│  └─ additional_generator.py (enhanced)             │
│      - generate_vss_xml(strategy)                  │
│      - generate_dhs_xml(strategy)                  │
│      - generate_tec_xml(strategy)                  │
│      (now with SUMO-verified conversions)          │
│                                                       │
└─────────────────────────────────────────────────────┘
          ↓
┌─ Frontend Layer ──────────────────────────────────────┐
│                                                       │
│  ┌─ parameter_form.js (enhanced)                    │
│  │   - generateFormFromSchema(template)             │
│  │   - renderParameterControl(param)                │
│  │   - validateParameterOnChange(param, value)      │
│  │   - generateXMLPreview(params)                   │
│  │                                                  │
│  ├─ UI Components:                                 │
│  │   - TimeRangePicker (hours display)              │
│  │   - StepArrayEditor (speed steps table)          │
│  │   - FlowIntervalEditor (flow rates)              │
│  │   - VehicleTypeMultiSelect (SUMO enums)          │
│  │   - XMLViewer (syntax highlighted)               │
│  │                                                  │
│  └─ Strategy Page (frontend/control/strategies.html)
│      Form generation → Validation → XML preview   │
│                                                       │
└─────────────────────────────────────────────────────┘
```

## Parameter Schema Example

```json
{
  "parameter_name": "speed_steps",
  "parameter_type": "step_array",
  "display_name": "Speed Control Steps",
  "description": "Time-dependent speed limits. Each step specifies speed limit valid from that time onward.",
  "required": true,

  "array_constraints": {
    "min_items": 1,
    "max_items": 10,
    "unique_keys": ["time_seconds"]
  },

  "item_schema": {
    "time_seconds": {
      "parameter_type": "integer",
      "display_name": "Time (hours for display)",
      "display_unit": "hours",
      "sumo_unit": "seconds",
      "conversion_factor": 3600,
      "min_value": 0,
      "max_value": 24,
      "step": 0.5,
      "constraint": "must be in ascending order"
    },
    "speed_kmh": {
      "parameter_type": "number",
      "display_name": "Speed Limit",
      "display_unit": "km/h",
      "sumo_unit": "m/s",
      "conversion_formula": "speed_ms = speed_kmh / 3.6",
      "min_value": 30,
      "max_value": 130,
      "step": 5,
      "description": "Realistic highway speeds"
    }
  },

  "default_value": [
    {"time_seconds": 0, "speed_kmh": 100},
    {"time_seconds": 25200, "speed_kmh": 80},
    {"time_seconds": 32400, "speed_kmh": 100}
  ]
}
```

## Migration Plan

### Pre-Update State
- Templates v1.0 in `templates/control_strategies/`
- Strategy instances using v1.0 templates

### During Update
1. Create new template files with v2.0 schemas (parallel to existing)
2. Implement new parameter validator
3. Implement new parameter form generator
4. Test with new templates

### Post-Update
- v2.0 templates available for new strategies
- Existing v1.0 strategies remain valid
- Users can opt to upgrade strategies to v2.0

### Rollback Plan
- Keep v1.0 template files intact
- UI can fall back to old form generation
- No data loss (templates only updated, not deleted)

## Testing Strategy

### Unit Tests
- Parameter validation: 20 tests for each parameter type
- Unit conversion: Time/speed/flow conversions
- Schema parsing: Template loading and parsing
- XML generation: Each strategy type with various parameter combinations

### Integration Tests
- Full workflow: Select template → fill form → validate → generate XML
- Backward compatibility: Load old v1.0 strategies
- Template versioning: Upgrade v1.0 → v2.0

### E2E Tests
- User creates VSS strategy: Select template → pick edges → set speed steps → see XML preview
- Form validation: Invalid values show errors
- Time interval editor: Create multiple time ranges with proper display

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Load template with schema | <100ms | Single file read |
| Validate parameters | <200ms | Network round-trip |
| Generate XML preview | <150ms | Local generation |
| Form generation | <50ms | DOM rendering |

## Risk Assessment

### High Risks
1. **SUMO Unit Conversion Bugs**: Wrong speed/time conversion breaks simulation
   - Mitigation: Comprehensive unit tests, compare generated XML against reference
2. **Form Validation Inconsistency**: Frontend/backend validation differ
   - Mitigation: Shared validation rules, E2E tests cover both paths

### Medium Risks
1. **Performance Degradation**: XML preview generation slows form
   - Mitigation: Debouncing, preview caching, async generation if needed
2. **User Confusion**: New parameter types (step_array, time_range_array) unclear
   - Mitigation: Clear UI labels, help text, visual guides

### Low Risks
1. **Backward Compatibility**: Old strategies become incompatible
   - Mitigation: Thorough testing, preserve v1.0 templates, version metadata

## Success Criteria

- [ ] All 5 strategy templates updated to v2.0 with SUMO verification
- [ ] Parameter schemas include all SUMO constraints (units, ranges, enums)
- [ ] Form generation works for all parameter types
- [ ] Real-time validation catches errors before save
- [ ] XML preview shows during strategy creation
- [ ] Existing v1.0 strategies remain loadable
- [ ] All unit tests pass (>90% coverage for parameter validation)
- [ ] E2E tests pass (template → strategy → XML workflow)
- [ ] Performance targets met (all operations <200ms)
- [ ] Users report clearer guidance during strategy creation (UX test)
