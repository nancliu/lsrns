# Proposal: Validate Strategy XML Generation for SUMO Compatibility

## Why

Currently, the strategy management system generates `control.add.xml` files but lacks comprehensive validation to ensure they are **SUMO-compatible** (Simulation of Urban MObility v1.19+). The XML generation code in `additional_generator.py` creates XML content, but there are gaps:

1. **No SUMO Format Validation**: Generated XML elements may have incorrect attribute formats (e.g., wrong unit conversions, invalid edge references, malformed speed values)
2. **No Edge Existence Checks**: Strategies reference road edges that may not exist in the network topology
3. **No Cascade Updates**: When a strategy is updated, all plans referencing it are not automatically re-generated
4. **Incomplete Schema Validation**: Parameter validation doesn't comprehensively check all SUMO XML constraints (lane indices, vehicle type enums, time ordering)
5. **Missing Documentation**: No clear specification of how control.add.xml must be formatted for SUMO to parse correctly

This causes:
- ❌ Generated XML fails at simulation time (SUMO rejects malformed files)
- ❌ Silent failures (XML is created but not usable)
- ❌ Manual cleanup required when strategies change
- ❌ Developers unsure of XML requirements vs. UI requirements

## What Changes

### New Capabilities
- Add comprehensive **SUMO XML validation** to `additional_generator.py`
- Create **XML schema validation module** (`shared/control_tools/xml_validator.py`)
- Add **edge existence verification** during strategy configuration
- Implement **cascade XML regeneration** when strategies are updated

### Modified Capabilities
- **plan-management** spec: Add explicit SUMO format and validation requirements
- **strategy-templates** spec: Add XML attribute format constraints
- `control_plan_service.py`: Add XML validation and error reporting
- `strategy_instance_service.py`: Add cascade regeneration on update

### Modified Components
- `additional_generator.py`: Add post-generation validation
- `control_strategy_service.py`: Add edge existence verification
- `control_plan_routes.py`: Add validation error responses

### Breaking Changes
- ⚠️ **API Response Changes**: Plans with invalid XML will now return 400 error with validation details (instead of creating invalid files)
- ⚠️ **Strategy Updates**: Existing invalid strategies may need parameter correction before re-generation works

## Impact

**Affected Specs**:
- `openspec/specs/plan-management/spec.md` - Add Req 3 (SUMO validation)
- `openspec/specs/strategy-templates/spec.md` - Clarify XML format constraints

**Affected Code**:
- `shared/control_tools/additional_generator.py` (~50 lines added)
- `shared/control_tools/xml_validator.py` (new, ~200 lines)
- `api/services/control_plan_service.py` (~20 lines added)
- `api/services/strategy_instance_service.py` (~30 lines added)
- `api/models/control/responses/plan_response.py` (error response schema)

**Testing Impact**:
- Add unit tests for XML validator
- Add integration tests for strategy update cascade
- Verify generated XML with SUMO's command-line validator

**User Impact**:
- ✅ Plans now guaranteed to work with SUMO simulation
- ✅ Clear error messages when strategy parameters are invalid
- ✅ Automatic updates when strategies change (no manual XML re-creation)
