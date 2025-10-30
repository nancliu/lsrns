# Code Cleanup & Refactoring Documentation

This folder contains comprehensive documentation about code quality analysis, deprecated code identification, and a structured cleanup plan for the OD_SIM project.

## Quick Navigation

### For Project Managers & Team Leads
Need an overview of what needs cleaning up?
- **[COMPREHENSIVE_CLEANUP_SUMMARY.md](COMPREHENSIVE_CLEANUP_SUMMARY.md)** - Executive summary with findings, timeline, and benefits
- **[CODE_CLEANUP_EXECUTION_PLAN.md](CODE_CLEANUP_EXECUTION_PLAN.md)** - 3-phase execution plan with timeline and resource allocation

### For Development Teams
Implementing cleanup tasks?
- **[CODE_CLEANUP_EXECUTION_PLAN.md](CODE_CLEANUP_EXECUTION_PLAN.md)** - Detailed execution plan with specific tasks and effort estimates
- **[BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md](BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md)** - Architecture analysis and specific code problems identified

### For Architects & Tech Leads
Understanding the overall architecture and design issues?
- **[BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md](BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md)** - Complete architecture analysis, waste code identification, and design improvements

### For Navigation
Getting lost in the documentation?
- **[CODE_CLEANUP_DOCUMENTATION_INDEX.md](CODE_CLEANUP_DOCUMENTATION_INDEX.md)** - Complete index with all topics, sections, and cross-references

## Key Findings

### Problems Identified: 22 Total
- **10 open_db_connection() calls** - Need migration to connection pooling
- **11 Large classes** - Exceed 300-line limit, need refactoring
- **1 Deprecated function** - generate_sumocfg() already handled

### Cleanup Timeline
- **Phase 0 (P0)**: 4 hours - Critical foundation work
- **Phase 1 (P1)**: 11 hours - Major refactoring
- **Phase 3 (P3)**: 23+ hours - Remaining classes and cleanup

### Total Effort: ~38 hours

## Document Overview

| Document | Size | Purpose | Audience |
|----------|------|---------|----------|
| COMPREHENSIVE_CLEANUP_SUMMARY.md | 11.3 KB | Executive summary | PMs, team leads, architects |
| CODE_CLEANUP_EXECUTION_PLAN.md | 11.6 KB | Detailed execution plan | Developers, team leads |
| BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md | 17.4 KB | Architecture & analysis | Architects, tech leads |
| CODE_CLEANUP_DOCUMENTATION_INDEX.md | 12.5 KB | Complete index | Everyone (navigation) |

## Phase Breakdown

### Phase 0: Foundation (4 hours) - CRITICAL
✓ Easy, high-impact work
- Migrate 10 open_db_connection() calls to get_pooled_connection()
- Mark deprecated directories with __init__.py files
- Update CLAUDE.md with migration guidance

### Phase 1: Major Refactoring (11 hours) - HIGH PRIORITY
- Refactor BatchOptimizationService (1193 lines)
  - Split into 3 smaller classes (~400, ~300, ~350 lines each)
  - Estimated effort: 8-10 hours
- Analyze other large classes (11 total)

### Phase 3: Complete Cleanup (23+ hours) - MEDIUM PRIORITY
- Refactor remaining 10 large classes
- Code style unification
- Deprecated directory deletion (before v1.0)

## Related Documentation

For incremental caching and performance work, see: `docs/code_quality/`

For tool scripts: `tools/`
- `cleanup_deprecated_code.py` - Code analysis and cleanup utilities
- `test_incremental_cache.py` - Cache testing suite

## Tool: cleanup_deprecated_code.py

A Python utility for analyzing and fixing deprecated code:

```bash
# Analyze the codebase
python tools/cleanup_deprecated_code.py --analyze

# Generate detailed report
python tools/cleanup_deprecated_code.py --report

# Fix deprecated code automatically (adds markers)
python tools/cleanup_deprecated_code.py --fix
```

### Features
- ✅ Detects deprecated directories (sim_scripts/, accuracy_analysis/)
- ✅ Finds all deprecated functions
- ✅ Identifies all open_db_connection() uses (10 found)
- ✅ Detects large classes exceeding 300 lines (11 found)
- ✅ Automatically adds deprecation markers

## Key Classes Requiring Refactoring

| Class | Lines | Methods | Priority | Effort |
|-------|-------|---------|----------|--------|
| BatchOptimizationService | 1193 | 19 | P0 | 8-10h |
| SimulationService | 850 | 14 | P1 | 6-8h |
| DataService | 780 | 12 | P1 | 6h |
| CaseService | 650 | 11 | P1 | 5h |
| TemplateService | 520 | 8 | P3 | 4h |
| (7 more classes) | 2500+ | - | P3 | 15h+ |

## Performance Impact

Cleanup work enables:
- ✅ Faster code navigation and understanding
- ✅ Easier testing and maintenance
- ✅ Better separation of concerns
- ✅ Reduced cognitive load for new developers
- ✅ Improved code quality metrics

## Getting Started

1. **Need overview?** → Read COMPREHENSIVE_CLEANUP_SUMMARY.md
2. **Planning execution?** → Read CODE_CLEANUP_EXECUTION_PLAN.md
3. **Understanding issues?** → Read BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md
4. **Need specific topic?** → Search CODE_CLEANUP_DOCUMENTATION_INDEX.md
5. **Running analysis?** → Use cleanup_deprecated_code.py tool

## Questions or Issues?

- Check the FAQ section in relevant documents
- Review the execution plan for specific task details
- Use cleanup_deprecated_code.py for automated analysis
- Search CODE_CLEANUP_DOCUMENTATION_INDEX.md for topics

## Next Steps

1. **Review Phase 0 tasks** in CODE_CLEANUP_EXECUTION_PLAN.md
2. **Run cleanup_deprecated_code.py --analyze** for current status
3. **Schedule Phase 0 work** (4 hours, high impact)
4. **Begin with open_db_connection() migration** (10 instances)

---

Last updated: 2025-10-30
