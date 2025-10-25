# Strategy Templates Update Based on SUMO Verification

## OpenSpec Change Proposal

**Change ID**: `update-strategy-templates-sumo-verified`
**Status**: Draft (Awaiting Approval)
**Created**: 2025-10-24
**Related to**: Phase 1C Complete, Phase 2 Preparation

## Overview

This proposal updates strategy templates and parameter configuration based on comprehensive SUMO v1.19 verification results. The update aligns templates with actual SUMO XML requirements and provides enhanced UI guidance for parameter configuration.

## Quick Summary

### What This Enables

Users can now:
- **SUMO-Aligned Configuration**: Templates match SUMO v1.19 actual XML structure
- **Proper Unit Handling**: Hours display → Seconds in SUMO, km/h display → m/s in SUMO
- **Real-Time Guidance**: Dynamic form generation with SUMO constraints
- **Validation Before Save**: Parameter validation prevents invalid SUMO XML generation
- **XML Preview**: See generated SUMO XML while configuring parameters

### Key Changes

| Component | From | To |
|-----------|------|-----|
| **Templates** | v1.0 (abstract) | v2.0 (SUMO-aligned) |
| **Parameter Schema** | Generic types | Rich types + SUMO metadata |
| **Form Generation** | Basic inputs | Dynamic controls by parameter type |
| **Validation** | Minimal | Comprehensive + real-time |
| **XML Preview** | None | Real-time during configuration |
| **Time Units** | Ambiguous | Hours (display) ↔ Seconds (SUMO) |
| **Speed Units** | Ambiguous | km/h (display) ↔ m/s (SUMO) |

### Deliverables

| Component | Details |
|-----------|---------|
| **Templates** | 5 updated templates (VSS moderate/strict, DHS, TEC metering/closure) with v2.0 schema |
| **Backend** | Parameter validator, XML preview endpoint, template schema enhancements |
| **Frontend** | Dynamic form generation, real-time validation UI, XML preview panel |
| **Tests** | 20+ unit tests, 5+ E2E tests, integration tests |
| **Documentation** | API guide, template reference, developer guide updates |

## File Structure

```
openspec/changes/update-strategy-templates-sumo-verified/
├── README.md              # This file
├── proposal.md            # Why, what, impact (2.5 KB)
├── design.md              # Technical decisions (15 KB)
├── tasks.md               # Implementation checklist (20+ KB)
└── specs/
    └── strategy-templates/
        └── spec.md        # 30+ Requirements & Scenarios (20 KB)
```

## Key Technical Decisions

### 1. SUMO Unit Conversion
**Decision**: Display in user-friendly units, convert to SUMO units at generation time
- Users enter "7:00 AM" → Display as "7" hours → SUMO receives 25200 seconds
- Users enter "80 km/h" → Display as "80" → SUMO receives ~22.22 m/s
- Clear conversion factors in template schema

### 2. Rich Parameter Types
**Decision**: Parameter types match UI needs + SUMO constraints
- `integer`, `number`, `enum`, `enum_array`
- `time_range_array`, `step_array`, `flow_interval_array`, `edge_array`
- Enables automatic form control generation

### 3. Real-Time Validation
**Decision**: Local validation (fast) + Backend validation (thorough)
- User gets immediate feedback on input
- Server validates complete parameter set before strategy save
- Three-tier: Error (blocks save), Warning (alerts), Info

### 4. XML Preview
**Decision**: Backend-generated, shown in UI during configuration
- Users see impact of parameters in real SUMO XML
- Debounced to avoid spam
- Helps users understand SUMO element structure

### 5. Template Versioning
**Decision**: v2.0 templates only for new strategies, preserve existing v1.0 strategies
- No forced migration
- Backward compatibility maintained
- Optional upgrade path for users

## Parameter Enhancements

### New Parameter Types

| Type | Display | SUMO | Example |
|------|---------|------|---------|
| `integer` | Spinner | Int | Lane index: 3 |
| `number` | Text input | Float | Speed: 80 km/h |
| `enum` | Dropdown | Enum | Control mode: "metering" |
| `enum_array` | Checkboxes | Array | Vehicles: [passenger, bus] |
| `time_range_array` | Time picker | Seconds | 7:00-9:00 → 25200-32400 |
| `step_array` | Table | Ordered objects | Speed steps over time |
| `flow_interval_array` | Table | Flow objects | Time-varying flow rates |
| `edge_array` | Multi-input | String array | Network edges |

### SUMO Constraints in Schema

```json
{
  "parameter_name": "speed_steps",
  "parameter_type": "step_array",
  "sumo_element": "step",           // Maps to <step> XML element
  "display_unit": "hours",          // User sees hours
  "sumo_unit": "seconds",           // SUMO receives seconds
  "conversion_factor": 3600,        // Multiply by this to convert
  "min_steps": 1,
  "max_steps": 10,
  "constraints": { "ordered": true } // Time-ordered steps
}
```

## Verification Against SUMO Research

This proposal aligns with findings in `docs/design/sumo_control_strategies_research.md`:

✅ **VSS**: Uses SUMO 1.18+ `<variableSpeedSign>` with `<step>` elements
✅ **DHS**: Uses `<rerouter>` + `<closingLaneReroute>` within intervals
✅ **TEC**: Uses `<calibrator>` for metering or `<rerouter>` for closure
✅ **Time Units**: Verified to use seconds (0-86400 per simulation day)
✅ **Vehicle Types**: SUMO enums (passenger, bus, truck, emergency)

## Related Documents

- **SUMO Research**: `docs/design/sumo_control_strategies_research.md` (verification basis)
- **Development Roadmap**: `docs/design/development_roadmap.md` (Phase 1C complete)
- **Phase 2 Plan**: `openspec/changes/add-control-plan-management/` (related)
- **Project Context**: `openspec/project.md` (conventions, constraints)

## Implementation Phases

### Phase 1: Template Regeneration (1 day)
- Update 5 templates with v2.0 schema
- Add SUMO metadata (element names, unit conversions)
- Create template index

### Phase 2: Backend Enhancement (2 days)
- Implement `parameter_validator.py` module
- Add validation and XML preview API endpoints
- Enhance `additional_generator.py` with unit conversions

### Phase 3: Frontend Implementation (2 days)
- Create dynamic form generation from parameter schemas
- Implement real-time validation UI
- Add XML preview panel with syntax highlighting

### Phase 4: Testing (1-2 days)
- Unit tests for validator and XML generation
- E2E tests for full workflow
- Performance testing (target <200ms for all operations)

### Phase 5: Documentation & Review (1 day)
- Update API documentation
- Update developer guide
- Code review and sign-off

## Next Steps

### For Approval
1. **Review proposal.md** - Understand the business case
2. **Review design.md** - Confirm technical approach
3. **Skim spec.md** - Review 30+ requirements and scenarios
4. **Provide feedback** - Request changes or approve

### For Implementation (After Approval)
1. Follow **tasks.md** sequentially
2. Update TODO checklist as you complete tasks
3. Run tests after each major section
4. Request code review before archiving

## FAQ

### Q: Will this break existing strategies?
**A**: No. Existing v1.0 strategies remain fully valid. New strategies use v2.0 templates. Users can optionally upgrade old strategies.

### Q: Do I need to understand SUMO XML?
**A**: No. The UI handles SUMO complexity. The form validates parameters and shows XML preview so users understand impact.

### Q: Why separate display units from SUMO units?
**A**: Users think in hours/km/h. SUMO uses seconds/m/s. Converting at generation time preserves user intent while ensuring SUMO compatibility.

### Q: How does real-time validation work?
**A**: As you type, the UI validates locally (fast). Before saving, it sends parameters to the server for comprehensive validation including XML generation.

### Q: Will the proposal affect Phase 2?
**A**: Yes, positively. Phase 2 (Plan Management) consumes strategies from these templates. Updated templates mean Plan Management gets better, validated strategies.

## Verification Checklist

Before approval, ensure:
- [ ] Proposal aligns with SUMO verification findings
- [ ] Design decisions are documented and justified
- [ ] Spec requirements are complete (each has ≥1 scenario)
- [ ] Task breakdown is realistic (7-9 days, 1-2 weeks)
- [ ] No conflicts with Phase 2 Plan Management
- [ ] API design follows project conventions
- [ ] Parameter validation approach is sound
- [ ] Backward compatibility strategy is clear
- [ ] Performance targets are achievable
- [ ] Testing strategy covers all scenarios

## Questions?

Refer to:
- **Architecture questions**: See design.md (Technical Decisions section)
- **Requirement details**: See spec.md (30+ scenarios)
- **Task breakdown**: See tasks.md (implementation steps)
- **SUMO mapping**: See docs/design/sumo_control_strategies_research.md

---

**Proposer**: Claude Code
**Target Phase**: Pre-Phase 2 enhancement (Phase 1 supplement)
**Estimated Duration**: 7-9 days (1-2 weeks)
**Status**: Draft - Awaiting stakeholder feedback
