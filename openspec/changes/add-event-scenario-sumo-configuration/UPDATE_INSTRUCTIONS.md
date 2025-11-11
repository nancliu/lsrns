# File Update Instructions - Architecture Changes

**Date**: 2025-11-11
**Purpose**: Instructions for updating proposal files with new architecture

---

## Files to Update

### 1. tasks.md

**Location to Insert**: After line 7 (after "## Overview")

**Content to Add**:
```markdown
## ⚠️ ARCHITECTURE UPDATE (2025-11-11)

**IMPORTANT**: Architecture has been revised to follow existing cases structure:
- ❌ Simulations removed from scenario library
- ✅ Simulations moved to cases branch
- ✅ English-only filenames (no Chinese)
- ✅ Per-scenario metadata + `no_control` type
- ✅ Relative paths only in sumocfg

📄 **Quick Reference**: See `ARCHITECTURE_SUMMARY.md`
📄 **Full Details**: See `ARCHITECTURE_CHANGES.md`

---
```

**Sections to Update**:

1. Line ~1219: "Architecture: Option A" section
   - Replace diagram with content from `ARCHITECTURE_SUMMARY.md`
   - Add note: "✏️ See ARCHITECTURE_SUMMARY.md for complete structure"

2. Line ~1249: "Data Flow & Workflow" section
   - Update scenario generation to show English filenames
   - Remove sumocfg generation step
   - Add note about per-scenario metadata

---

### 2. proposal.md

**Sections to Search and Update**:

1. Search for: "Option A" or "Architecture"
   - Add reference to `ARCHITECTURE_SUMMARY.md` at top
   - Update any architecture diagrams

2. Search for: "File Structure" or "Directory Structure"
   - Update with English directory names
   - Remove sumocfg references from scenario library

3. Search for: "Metadata"
   - Update to per-scenario metadata model
   - Add `scenario_metadata.json` schema

---

### 3. design.md

**Sections to Update**:

1. Search for: "File Organization"
   - Update directory structure
   - Add English naming convention table

2. Search for: "Scenario Library"
   - Remove sumocfg/results references
   - Add per-scenario metadata explanation

3. Search for: "Cases Integration"
   - Add 4 simulation types explanation
   - Add file copying requirements
   - Add relative path requirements

---

### 4. docs/scenarios_library/PROJECT_WORKFLOW.md

**Sections to Update**:

1. "Phase 1" or "Scenario Generation"
   - Update to show English filenames
   - Remove sumocfg generation
   - Add per-scenario metadata

2. "File Structure" or "Directory Layout"
   - Update with new architecture
   - Reference `ARCHITECTURE_SUMMARY.md`

3. "Simulation Workflow"
   - Add cases branch integration
   - Add 4 simulation types
   - Add file copying workflow

---

## Standard Header to Add

Add this to the top of each updated section:

```markdown
**📌 Architecture Updated 2025-11-11**:
- Scenario library: Read-only definitions (no simulations)
- Cases branch: Executable simulations
- See `ARCHITECTURE_SUMMARY.md` for structure

---
```

---

## Key Points to Emphasize

### In ALL Files:

1. **No Chinese in Filenames**
   - Before: `scenario_交通事故_vss_12547.add.xml`
   - After: `scenario_accident_vss_12547.add.xml`

2. **Per-Scenario Metadata**
   - Before: Global `scenario_metadata.json`
   - After: One `scenario_metadata.json` per scenario directory

3. **No Simulations in Scenario Library**
   - ❌ Remove: `simulation.sumocfg`, `results/`
   - ✅ Keep: `.add.xml`, JSON configs

4. **Cases Structure**
   - ✅ config/: OD + TAZ (no network.xml)
   - ✅ simulations/: 4 types per scenario
   - ✅ e1/: Detector outputs
   - ❌ No results/ subdirectory

5. **Relative Paths**
   - Network: `../../../../templates/network_files/*.net.xml`
   - Routes: `../../config/*.rou.xml`
   - Additional: Local filenames (copied)

---

## Event Type Translation Table

Include this table in all files:

| Chinese | English | Directory |
|---------|---------|-----------|
| 交通事故 | accident | 01_accident |
| 交通阻塞 | congestion | 02_congestion |
| 交通管制 | road_control | 03_road_control |
| 地质灾害 | geological | 04_geological |
| 车辆故障 | breakdown | 05_breakdown |
| 恶劣天气 | weather | 06_weather |

---

## Filename Convention

Include in all files:

```
scenario_{event_type}_{strategy}_{event_id}.add.xml

Examples:
- scenario_accident_vss_12547.add.xml
- scenario_accident_event_12547.add.xml (no_control)
- scenario_congestion_tec_98765.add.xml
```

---

## Quick Update Script

For each file, follow this process:

1. **Read the file**: Find existing architecture sections
2. **Add header**: Insert architecture update notice at top
3. **Update diagrams**: Replace with content from `ARCHITECTURE_SUMMARY.md`
4. **Update text**: Change Chinese to English, update paths
5. **Add references**: Link to `ARCHITECTURE_SUMMARY.md` and `ARCHITECTURE_CHANGES.md`
6. **Verify consistency**: All files should use same terminology

---

## Verification Checklist

After updating each file:

- [ ] Architecture update notice added
- [ ] Reference to `ARCHITECTURE_SUMMARY.md` included
- [ ] No Chinese in filenames/examples
- [ ] Per-scenario metadata mentioned
- [ ] `no_control` type explained
- [ ] Cases structure follows existing pattern
- [ ] Relative paths emphasized
- [ ] Event type translation table included
- [ ] Filename convention documented
- [ ] All examples use English names

---

**Status**: Ready for implementation
**Next**: Update files manually or wait for file stability
