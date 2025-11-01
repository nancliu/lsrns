# Change: Simplify Vehicle Type System

**Change ID**: `simplify-vehicle-type-system`
**Status**: Draft
**Created**: 2025-11-01

## Quick Summary

Unifies vehicle type definitions to a two-layer model:
- **Layer 1**: 3 user-friendly categories (客车/货车/特种车辆)
- **Layer 2**: 6 SUMO simulation types (auto-mapped)

Eliminates three unsynchronized sources, removes frontend hardcoding.

## Files

- [proposal.md](./proposal.md) - Why and what changes
- [design.md](./design.md) - Architecture decisions
- [tasks.md](./tasks.md) - Implementation checklist
- [specs/vehicle-type-two-layer/spec.md](./specs/vehicle-type-two-layer/spec.md) - Requirements

## Key Changes

| Component | Change |
|-----------|--------|
| `vehicle_types_enum.json` | Simplify to 3 categories with `includes` mapping |
| `vehicle_types.json` | Add `category` field to detailed types |
| `templates.html` | Remove hardcoded vehicle list (lines 890-902) |
| `strategy_instance_service.py` | Add auto-expansion logic |
| `vehicle_type_utils.py` | **NEW** - Expansion utilities |

## Timeline

- **Implementation**: 3-4 days
- **Testing**: 1 day
- **Documentation**: 0.5 days
- **Total**: 5-6 days

## Dependencies

- **Requires**: `refactor-strategy-parameter-configuration` Phase 1-10 completed
- **Blocks**: None

## Validation Status

- [x] Proposal complete
- [x] Design documented
- [x] Tasks defined
- [x] Specs written
- [ ] Implementation
- [ ] Tests passing
- [ ] Deployed

## Quick Start

1. Read [proposal.md](./proposal.md) for context
2. Review [design.md](./design.md) for architecture
3. Follow [tasks.md](./tasks.md) for implementation
4. Test against [spec.md](./specs/vehicle-type-two-layer/spec.md) scenarios
