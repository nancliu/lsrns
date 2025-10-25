# Proposal: Enhance Strategy Parameter Configuration

**Change ID**: enhance-strategy-parameter-configuration
**Status**: Draft
**Created**: 2025-10-25
**Author**: System

## Problem Statement

The current strategy parameter configuration page (Step 3 in the strategy creation workflow) has several critical usability and functionality issues that prevent users from successfully creating strategy instances:

### Current Issues

1. **Missing Parameter Input Functionality**
   - Some parameter types (especially complex arrays like `time_intervals`, `speed_steps`) cannot be properly filled in
   - Array inputs lack clear guidance on format (JSON vs newline-separated vs comma-separated)
   - No visual editors for complex structured data (time-speed pairs, flow intervals)

2. **Insufficient Edge Selection Display**
   - Selected edge list only shows `edge_id`
   - Missing critical context: route code, section code, stake range, lane count, direction
   - Users cannot verify they selected correct edges without returning to Step 2

3. **Manual Strategy Naming**
   - Users must manually create strategy names, leading to:
     - Inconsistent naming conventions
     - Difficulty in identifying strategies later
     - Missing key context (location, parameters, time periods)

4. **Manual Strategy Description**
   - Strategy descriptions must be manually written
   - Templates provide description templates but users must adapt them
   - Descriptions often omit critical parameter details

5. **Personnel Information in Configuration**
   - Current design may include personnel/OA fields
   - Project does not integrate with business OA system
   - Personnel fields should be removed from configuration

## Proposed Solution

Enhance the parameter configuration page (Step 3) with:

1. **Smart Parameter Input Components**
   - Visual editors for complex parameter types (time-speed pairs, intervals, flow rates)
   - Clear format hints and examples based on parameter type
   - Real-time validation with SUMO constraint checking
   - Support for all template parameter types (including new v2.0 types)

2. **Enhanced Edge Selection Display**
   - Show comprehensive edge information table with:
     - Edge ID, route code, section code
     - Stake range (start/end km markers)
     - Lane count, direction, node type
     - Length, demonstration segment status
   - Allow inline editing/removal of selected edges
   - Show edge continuity warnings for DHS strategies

3. **Automatic Strategy Name Generation**
   - Generate names based on template rules:
     - **VSS**: `{Route}-{Section} 限速{Speed}km/h ({Time})`
     - **DHS**: `{Route}-{Section} 应急车道开放 ({Time})`
     - **TEC**: `{Entrance} 入口管控 ({Type})`
   - Allow user override with suggested name pre-filled
   - Ensure name uniqueness with automatic suffix

4. **Automatic Strategy Description Generation**
   - Generate descriptions from template + parameters:
     - Strategy type and purpose
     - Affected locations (routes, sections, stakes)
     - Key parameters (speeds, times, vehicle types)
     - Generated SUMO elements count
   - Allow user to edit generated description
   - Save description to strategy metadata

5. **Remove Personnel Fields**
   - No personnel/OA integration fields in configuration form
   - Strategy metadata tracks creation/modification timestamps only
   - Future: If OA integration needed, add separate module

## Benefits

1. **Improved Success Rate**: Users can successfully fill all parameter types
2. **Better Verification**: Users can verify edge selection before saving
3. **Consistent Naming**: Automatic naming ensures findability
4. **Self-Documenting**: Auto-generated descriptions capture intent
5. **Simplified UX**: Remove unnecessary personnel fields

## Scope

### In Scope

- Enhanced parameter input components for all v2.0 template parameter types
- Comprehensive edge selection display table with all relevant attributes
- Automatic strategy name generation with configurable rules
- Automatic description generation from template + parameters
- Removal of personnel/OA fields from configuration form
- Frontend validation improvements
- UX refinements to Step 3 (Configuration Parameters)

### Out of Scope

- Changes to Step 1 (Template Selection) or Step 2 (Edge Selection) workflows
- Backend API changes (existing `/api/v1/control/strategy-instances` endpoints sufficient)
- Template schema modifications (use existing v2.0 templates)
- OA system integration (future enhancement)
- Multi-language support (Chinese only for now)

## Dependencies

- Existing strategy template v2.0 schemas (`openspec/specs/strategy-templates/spec.md`)
- Edge selector database schema (`dim.sim_network_edges` table)
- Strategy workflow UX design (`docs/design/strategy_workflow_ux.md`)
- Strategy manager module (`frontend/control/js/strategy_manager.js`)

## Success Criteria

1. **All parameter types are fillable**: Users can successfully input values for every template parameter type
2. **Edge information is comprehensive**: Selected edges display shows all 8+ attributes (ID, route, section, stakes, lanes, direction, type, length)
3. **Names are auto-generated**: 90%+ of strategies use auto-generated names without modification
4. **Descriptions are helpful**: Generated descriptions contain sufficient detail for strategy identification
5. **No personnel fields**: Configuration form contains zero personnel/OA-related inputs
6. **Validation is clear**: Users receive actionable error messages for invalid inputs
7. **Preview works**: XML preview reflects all configured parameters accurately

## Implementation Phases

### Phase 1: Parameter Input Enhancement (Priority: P0)
- Implement visual editors for complex types (time-speed pairs, intervals)
- Add format hints and examples to array inputs
- Enhance validation feedback with SUMO constraints

### Phase 2: Edge Display Enhancement (Priority: P0)
- Create comprehensive edge information table
- Add inline edit/remove functionality
- Implement continuity checking for DHS

### Phase 3: Auto-Generation Features (Priority: P1)
- Implement name generation rules per strategy type
- Implement description generation from template
- Add user override capability

### Phase 4: Cleanup & Polish (Priority: P1)
- Remove personnel fields
- Refine UX based on testing
- Update documentation

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex parameter editors are difficult to implement | High | Start with simple array inputs, progressively enhance |
| Auto-generated names don't meet user needs | Medium | Allow full user override, gather feedback |
| Edge table performance with many selected edges | Low | Use virtual scrolling for >50 edges |
| Breaking changes to existing strategies | High | Ensure backward compatibility with v1.0 strategies |

## Open Questions

1. **Parameter Editor Complexity**: Should we implement full visual editors (drag timelines, graphical speed curves) or start with enhanced text inputs?
   - **Recommendation**: Start with enhanced text inputs with clear examples, add visual editors in Phase 2

2. **Edge Table Interaction**: Should users be able to reorder selected edges in the table (important for DHS continuity)?
   - **Recommendation**: Yes, add drag-to-reorder capability for DHS strategies

3. **Name Generation Rules**: Should name generation be configurable per organization or use fixed rules?
   - **Recommendation**: Use fixed rules initially, make configurable if demand arises

4. **Description Templates**: Should templates provide description generation rules or use generic format?
   - **Recommendation**: Templates provide description templates with parameter placeholders

## References

- [Strategy Workflow UX Design](../../docs/design/strategy_workflow_ux.md)
- [Strategy Template Analysis](../../docs/design/strategy_template_analysis_and_recommendations.md)
- [Strategy Templates Spec](../../specs/strategy-templates/spec.md)
- [Edge Selector Design](../../docs/design/edge_selector_database_design.md)
