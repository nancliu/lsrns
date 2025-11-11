# Architecture Update Package - README

**Date**: 2025-11-11
**Status**: Documentation Complete, Ready for Manual Application
**Version**: 2.0

---

## 📦 Package Contents

This package contains all documentation needed to update the event scenario system architecture. Due to file modification conflicts, manual application is required.

### Core Documentation Files

1. **`ARCHITECTURE_CHANGES.md`** (English, Complete)
   - Full architectural specification
   - Before/after comparisons
   - Implementation steps (6 hours)
   - Code changes required
   - **Target Audience**: Developers

2. **`ARCHITECTURE_SUMMARY.md`** (English, Quick Reference)
   - Condensed architecture overview
   - File structures
   - Naming conventions
   - Critical requirements checklist
   - **Target Audience**: All team members

3. **`ARCHITECTURE_SUMMARY_ZH.md`** (Chinese, Quick Reference)
   - Chinese translation of architecture summary
   - Same content as ARCHITECTURE_SUMMARY.md
   - **Target Audience**: Chinese-speaking team members

4. **`UPDATE_INSTRUCTIONS.md`** (English, Manual Update Guide)
   - Step-by-step instructions for updating each file
   - Specific line numbers and sections
   - Content to insert
   - Verification checklist
   - **Target Audience**: Documentation maintainers

5. **`ARCHITECTURE_UPDATE_README.md`** (This file)
   - Package overview
   - Usage instructions
   - File relationships
   - **Target Audience**: Project managers, team leads

---

## 🎯 Key Changes Summary

### What Changed

| Aspect | Before | After |
|--------|--------|-------|
| **Filenames** | Chinese allowed | English only |
| **Metadata** | Global file | Per-scenario file |
| **Scenario Types** | With control only | Added `no_control` |
| **Simulations** | In scenario library | In cases branch |
| **Directory Structure** | Nested (vss/dhs/tec) | Flattened |
| **Paths in sumocfg** | Absolute allowed | Relative only |
| **Results Location** | `results/` subdir | Directly in `sim_xxx/` |
| **Detector Outputs** | No specific location | `e1/` directory |

### Why Changed

1. **SUMO Compatibility**: Chinese filenames can cause errors
2. **Code Reuse**: Cases branch uses existing infrastructure
3. **Migration**: Relative paths prevent breakage when moving
4. **Organization**: Per-scenario metadata improves independence
5. **Consistency**: Follows existing cases framework structure

---

## 📋 Files That Need Manual Updates

### 1. OpenSpec Proposal Files

**Directory**: `openspec/changes/add-event-scenario-sumo-configuration/`

- [ ] **`tasks.md`** (Line ~1219: Architecture section)
  - Add architecture update notice at top
  - Update "Architecture: Option A" diagram
  - Update "Data Flow & Workflow" section
  - **Instructions**: See `UPDATE_INSTRUCTIONS.md` Section 1

- [ ] **`proposal.md`** (Search: "Option A", "Architecture")
  - Add reference to ARCHITECTURE_SUMMARY.md
  - Update architecture diagrams
  - Update metadata sections
  - **Instructions**: See `UPDATE_INSTRUCTIONS.md` Section 2

- [ ] **`design.md`** (Search: "File Organization")
  - Update file structure examples
  - Add English naming convention
  - Update cases integration section
  - **Instructions**: See `UPDATE_INSTRUCTIONS.md` Section 3

### 2. Project Documentation

**Directory**: `docs/scenarios_library/`

- [ ] **`PROJECT_WORKFLOW.md`** (Line ~391: "场景库结构")
  - Add architecture update notice (Chinese)
  - Update scenario library structure diagram
  - Add English event type mapping table
  - Update simulation workflow section
  - **Instructions**: See `UPDATE_INSTRUCTIONS.md` Section 4

---

## 🔧 Manual Update Process

### Step 1: Review Architecture Documents

1. Read `ARCHITECTURE_SUMMARY.md` (or `ARCHITECTURE_SUMMARY_ZH.md` for Chinese)
2. Understand the key changes
3. Review `ARCHITECTURE_CHANGES.md` for full details

### Step 2: Apply Updates to Each File

For each file listed above:

1. Open `UPDATE_INSTRUCTIONS.md`
2. Find the section for that file
3. Locate the specified line numbers or section headers
4. Insert the provided content
5. Verify consistency with architecture documents

### Step 3: Verify Updates

Use the checklist in each section of `UPDATE_INSTRUCTIONS.md`:

- [ ] Architecture update notice added
- [ ] Reference to ARCHITECTURE_SUMMARY.md included
- [ ] No Chinese in filenames/examples
- [ ] Per-scenario metadata mentioned
- [ ] `no_control` type explained
- [ ] Cases structure follows existing pattern
- [ ] Relative paths emphasized
- [ ] Event type translation table included
- [ ] Filename convention documented
- [ ] All examples use English names

---

## 📖 File Relationships

```
ARCHITECTURE_UPDATE_README.md  ← You are here
├── Points to all other documents
└── Provides overview

ARCHITECTURE_CHANGES.md
├── Complete specification
├── Referenced by: UPDATE_INSTRUCTIONS.md
└── Source of truth for all changes

ARCHITECTURE_SUMMARY.md (English)
├── Quick reference
├── Referenced by: All proposal files
└── Condensed version of ARCHITECTURE_CHANGES.md

ARCHITECTURE_SUMMARY_ZH.md (Chinese)
├── Quick reference (Chinese)
├── Referenced by: PROJECT_WORKFLOW.md
└── Translation of ARCHITECTURE_SUMMARY.md

UPDATE_INSTRUCTIONS.md
├── Step-by-step update guide
├── References: ARCHITECTURE_CHANGES.md
└── Used by: Documentation maintainers
```

---

## ✅ Implementation Timeline

**Total**: 6 hours

1. **Step 1: File Naming** (1 hour)
   - Update scenario_generator.py
   - Add English event type mapping
   - Update filename generation

2. **Step 2: Metadata Structure** (1 hour)
   - Change to per-scenario metadata
   - Update scenario_index.json format
   - Add no_control scenario generation

3. **Step 3: Cases Integration** (2 hours)
   - Follow existing cases structure
   - Copy .add.xml files to sim directories
   - Create e1/ directories
   - Remove results/ subdirectories

4. **Step 4: SUMO Config** (1 hour)
   - Enforce relative paths only
   - Update path generation logic

5. **Step 5: Tests** (1 hour)
   - Update E2E tests
   - Test path resolution
   - Test file copying

---

## 🚀 Next Steps

### Immediate Actions

1. **Review**: Read ARCHITECTURE_SUMMARY.md
2. **Approve**: Confirm changes are acceptable
3. **Schedule**: Allocate 6 hours for implementation

### Implementation Order

1. Update documentation files (this package)
2. Update code files (scenario_generator.py, etc.)
3. Run tests
4. Generate new scenarios with updated structure

---

## 📞 Support

### Questions?

Refer to:
- **Quick questions**: ARCHITECTURE_SUMMARY.md
- **Detailed questions**: ARCHITECTURE_CHANGES.md
- **How to update files**: UPDATE_INSTRUCTIONS.md

### Issues During Updates?

1. Check if all architecture documents are consistent
2. Verify file paths and line numbers
3. Ensure English naming is used throughout
4. Confirm relative paths in all sumocfg examples

---

## 📝 Version History

- **v2.0 (2025-11-11)**: Architecture revision approved
  - Simulations moved to cases branch
  - English-only filenames
  - Per-scenario metadata
  - Relative paths enforced

- **v1.0 (2025-11-10)**: Original architecture
  - Simulations in scenario library (deprecated)

---

**Status**: ✅ Documentation Complete
**Next**: Manual application of updates to proposal files
**Estimated Time**: 30 minutes to update all files manually
