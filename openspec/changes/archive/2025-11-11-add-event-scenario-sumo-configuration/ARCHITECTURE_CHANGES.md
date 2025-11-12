# Architectural Changes: Move Simulations to Cases Branch

**Date**: 2025-11-11 (Updated)
**Change ID**: `add-event-scenario-sumo-configuration`
**Status**: ARCHITECTURAL REVISION REQUIRED
**Version**: 2.0 - Following Existing Cases Framework

---

## Summary

**Problem**: Current design stores simulations (`simulation.sumocfg` and `results/`) in the scenario library (`output/scenarios/`), which creates issues:
- Cannot reuse previous implementations effectively
- Simulations should be associated with cases, not stored in read-only library
- Need better separation between scenario definitions and simulation results
- Absolute paths in sumocfg cause migration issues

**Solution**: Move simulation execution to the cases branch while keeping scenario library as read-only definitions, **strictly following existing cases framework structure**.

---

## Updated Architecture

### Before (Original Design - INCORRECT)

```
output/scenarios/
├── 01_交通事故/
│   ├── vss/
│   │   └── scenario_12547_vss/
│   │       ├── scenario_交通事故_vss_12547.add.xml  ❌ (Chinese in filename)
│   │       ├── event_description.json
│   │       ├── traffic_input_config.json
│   │       ├── control_strategy_config.json
│   │       ├── simulation.sumocfg  ❌ (remove)
│   │       └── results/  ❌ (remove)
│   ├── dhs/
│   └── tec/
└── scenario_index.json  ❌ (global metadata)
```

### After (New Design - CORRECT)

#### Scenario Library (Read-Only, No Simulations)

```
output/scenarios/
├── 01_accident/  ✏️ (English directory names)
│   ├── scenario_12547_vss/  ✏️ (flattened structure)
│   │   ├── scenario_accident_vss_12547.add.xml  ✏️ (no Chinese)
│   │   ├── event_description.json
│   │   ├── traffic_input_config.json
│   │   ├── control_strategy_config.json
│   │   └── scenario_metadata.json  ✏️ NEW (per-scenario metadata)
│   ├── scenario_12547_dhs/
│   │   ├── scenario_accident_dhs_12547.add.xml
│   │   ├── event_description.json
│   │   ├── traffic_input_config.json
│   │   ├── control_strategy_config.json
│   │   └── scenario_metadata.json
│   ├── scenario_12547_tec/
│   └── scenario_12547_no_control/  ✏️ NEW (event only, no control)
│       ├── scenario_accident_event_12547.add.xml  ✏️ (event only)
│       ├── event_description.json
│       ├── traffic_input_config.json
│       └── scenario_metadata.json
└── scenario_index.json  ✏️ (updated format)
```

#### Cases Branch (Following Existing Structure - CORRECTED)

**⚠️ IMPORTANT**: Use flat structure to maintain compatibility with existing simulation listing functionality.

```
cases/
├── case_morning_peak_20251111/
│   ├── metadata.json
│   ├── config/  ✏️ (following existing structure)
│   │   ├── dwd_od_weekly_*.od.xml
│   │   ├── dwd_od_weekly_*.rou.xml
│   │   └── TAZ_6.add.xml
│   ├── analysis/
│   └── simulations/
│       ├── sim_1028_093903_micro/  ← Existing regular simulations
│       ├── scenario_12547_baseline/  ✏️ NEW (event scenario: baseline)
│       │   ├── simulation.sumocfg  ✏️ (relative paths only)
│       │   ├── simulation_metadata.json  ✏️ (with scenario_group: "12547")
│       │   ├── TAZ_6.add.xml  ✏️ (copied here)
│       │   ├── e1/  ✏️ (e1 detector outputs)
│       │   ├── summary.xml
│       │   ├── tripinfo.xml
│       │   └── progress.json
│       ├── scenario_12547_with_event/  ✏️ NEW (event only, no control)
│       │   ├── simulation.sumocfg  ✏️ (relative paths)
│       │   ├── scenario_accident_event_12547.add.xml  ✏️ (copied)
│       │   ├── TAZ_6.add.xml  ✏️ (copied)
│       │   ├── e1/
│       │   ├── summary.xml
│       │   └── tripinfo.xml
│       ├── scenario_12547_vss/  ✏️ NEW (event + VSS control)
│       │   ├── simulation.sumocfg
│       │   ├── scenario_accident_vss_12547.add.xml  ✏️ (copied)
│       │   ├── TAZ_6.add.xml
│       │   ├── e1/
│       │   └── ...
│       └── scenario_12547_dhs/  ✏️ NEW (event + DHS control)
│           ├── simulation.sumocfg
│           ├── scenario_accident_dhs_12547.add.xml
│           ├── TAZ_6.add.xml
│           ├── e1/
│           └── ...
```

**Naming Convention** ✏️:
- Regular simulations: `sim_{timestamp}_{type}/` (existing pattern)
- Event scenario simulations: `scenario_{event_id}_{variant}/`
  - `scenario_{id}_baseline` - No event, no control (baseline comparison)
  - `scenario_{id}_with_event` - Event only, no control
  - `scenario_{id}_{strategy}` - Event + control strategy (vss/dhs/tec)

**Benefits** ✅:
- ✅ Flat structure maintains compatibility with existing simulation listing
- ✅ Naming convention clearly distinguishes scenario simulations
- ✅ `simulation_metadata.json` includes `scenario_group` field to link related simulations
- ✅ No changes needed to existing API/UI code

**Key Principles** ✅:
1. ✅ **No Chinese in .add.xml filenames** (SUMO compatibility)
2. ✅ **No results/ subdirectory** (files directly in sim_xxx/)
3. ✅ **e1/ directory** for detector outputs
4. ✅ **.add.xml files copied** to simulation directories
5. ✅ **Relative paths only** in sumocfg files
6. ✅ **Following existing cases structure** (config/ with OD/TAZ, no network.xml)

---

## Key Changes

### 1. Scenario Library Changes

**File Naming** ✏️:
- ❌ **Before**: `scenario_交通事故_vss_12547.add.xml` (Chinese)
- ✅ **After**: `scenario_accident_vss_12547.add.xml` (English only)

**Directory Structure** ✏️:
- ❌ **Before**: `01_交通事故/vss/scenario_12547_vss/`
- ✅ **After**: `01_accident/scenario_12547_vss/` (flattened, English)

**Metadata** ✏️:
- ❌ **Before**: Global `scenario_metadata.json` at root
- ✅ **After**: Per-scenario `scenario_metadata.json` in each scenario directory

**New Scenario Type** ✏️:
- ✅ `scenario_{id}_no_control/` - Event only, no control strategy (for baseline comparison)

**Removed**:
- ❌ `simulation.sumocfg` files
- ❌ `results/` directories
- ❌ `vss/`, `dhs/`, `tec/` subdirectories

### 2. Cases Branch Changes (Following Existing Structure)

**Directory Structure** ✅:
```
cases/case_xxx/
├── metadata.json
├── config/  ✏️ (OD files, TAZ files - NO network.xml)
│   ├── *.od.xml
│   ├── *.rou.xml
│   └── TAZ_*.add.xml
├── analysis/
└── simulations/
    ├── sim_baseline/
    ├── sim_with_event/
    └── ...
```

**Simulation Directory Structure** ✅:
```
simulations/sim_xxx/
├── simulation.sumocfg  ✏️ (relative paths only)
├── simulation_metadata.json
├── TAZ_6.add.xml  ✏️ (copied from config/)
├── scenario_*.add.xml  ✏️ (copied from scenario library)
├── e1/  ✏️ (e1 detector outputs)
│   └── e1_output.xml
├── summary.xml  ✏️ (directly here, no results/)
├── tripinfo.xml
├── vehroute.xml
└── progress.json
```

**Critical Requirements** ✏️:
1. ✅ **Files directly in sim_xxx/** (no results/ subdirectory)
2. ✅ **e1/ directory** for detector outputs
3. ✅ **.add.xml files copied** to simulation directory (lower path error risk)
4. ✅ **Relative paths** in sumocfg (migration-friendly)

---

## Metadata Models

### Per-Scenario `scenario_metadata.json`

Located at: `output/scenarios/01_accident/scenario_12547_vss/scenario_metadata.json`

```json
{
  "scenario_id": "12547_vss",
  "event_id": "12547",
  "event_type": "accident",
  "event_type_zh": "交通事故",
  "strategy": "VSS",
  "created_date": "2025-11-10T12:00:00Z",
  "scenario_files": {
    "add_xml": "scenario_accident_vss_12547.add.xml",
    "event_description": "event_description.json",
    "traffic_input_config": "traffic_input_config.json",
    "control_strategy_config": "control_strategy_config.json"
  },
  "event": {
    "location": "G5京昆高速K1576+000",
    "start_time": "2025-07-14 01:53:49",
    "end_time": "2025-07-14 03:22:39",
    "duration_hours": 1.48
  },
  "applied_to_cases": [
    {
      "case_id": "case_morning_peak_20251111",
      "simulation_dir": "scenario_sim_12547",
      "simulation_types": [
        "sim_baseline",
        "sim_with_event",
        "sim_with_option_control_vss"
      ],
      "created_date": "2025-11-11",
      "status": "completed"
    }
  ]
}
```

### Updated `scenario_index.json`

Located at: `output/scenarios/scenario_index.json`

```json
{
  "version": "2.0",
  "generated_date": "2025-11-10",
  "total_scenarios": 40,
  "by_event_type": {
    "accident": 18,
    "congestion": 12,
    "road_control": 6,
    "geological": 4
  },
  "by_strategy": {
    "VSS": 15,
    "TEC": 15,
    "DHS": 4,
    "no_control": 6
  },
  "scenarios": [
    {
      "scenario_id": "12547_vss",
      "event_id": "12547",
      "event_type": "accident",
      "strategy": "VSS",
      "directory": "01_accident/scenario_12547_vss/",
      "files": {
        "add_xml": "scenario_accident_vss_12547.add.xml",
        "event_description": "event_description.json",
        "traffic_input_config": "traffic_input_config.json",
        "control_strategy_config": "control_strategy_config.json",
        "scenario_metadata": "scenario_metadata.json"
      }
    },
    {
      "scenario_id": "12547_no_control",
      "event_id": "12547",
      "event_type": "accident",
      "strategy": "no_control",
      "directory": "01_accident/scenario_12547_no_control/",
      "files": {
        "add_xml": "scenario_accident_event_12547.add.xml",
        "event_description": "event_description.json",
        "traffic_input_config": "traffic_input_config.json",
        "scenario_metadata": "scenario_metadata.json"
      }
    }
  ]
}
```

---

## SUMO Configuration (sumocfg) - Relative Paths Only

### Example: `simulation.sumocfg` with Relative Paths

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <!-- ✅ Relative path to network (4 levels up to templates) -->
        <net-file value="../../../../templates/network_files/sichuan202508v7.net.xml"/>

        <!-- ✅ Relative path to routes (2 levels up to config) -->
        <route-files value="../../config/dwd_od_weekly_20250901080000_20250901090000.rou.xml"/>

        <!-- ✅ Local files (copied to simulation directory) -->
        <additional-files value="TAZ_6.add.xml,scenario_accident_vss_12547.add.xml"/>
    </input>
    <output>
        <!-- ✅ Local paths (in current directory) -->
        <summary-output value="summary.xml"/>
        <tripinfo-output value="tripinfo.xml"/>
    </output>

    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>

    <processing>
        <ignore-route-errors value="true"/>
        <collision.action value="warn"/>
    </processing>
</configuration>
```

**Path Rules** ✅:
1. ✅ **Network**: `../../../../templates/network_files/*.net.xml` (relative from sim_xxx/)
2. ✅ **Routes**: `../../config/*.rou.xml` (relative to config/)
3. ✅ **Additional files**: Local filenames only (files copied to sim_xxx/)
4. ❌ **NO absolute paths** (e.g., `D:/projects/OD_SIM/...`)

---

## Event Type Mapping (English Names)

| Chinese | English | Directory |
|---------|---------|-----------|
| 交通事故 | accident | 01_accident |
| 交通阻塞 | congestion | 02_congestion |
| 交通管制 | road_control | 03_road_control |
| 地质灾害 | geological | 04_geological |
| 车辆故障 | breakdown | 05_breakdown |
| 恶劣天气 | weather | 06_weather |

**File Naming Convention** ✏️:
```
scenario_{event_type}_{strategy}_{event_id}.add.xml

Examples:
- scenario_accident_vss_12547.add.xml
- scenario_accident_event_12547.add.xml (no_control)
- scenario_congestion_tec_98765.add.xml
- scenario_road_control_event_45678.add.xml
```

---

## Implementation Steps

### Step 1: Update File Naming (1 hour)

- [ ] Update `scenario_generator.py` to use English names
- [ ] Map Chinese event types to English
- [ ] Update filename generation:
  ```python
  event_type_map = {
      '交通事故': 'accident',
      '交通阻塞': 'congestion',
      '交通管制': 'road_control',
      '地质灾害': 'geological',
      '车辆故障': 'breakdown',
      '恶劣天气': 'weather'
  }
  ```

### Step 2: Update Metadata Structure (1 hour)

- [ ] Change from global to per-scenario `scenario_metadata.json`
- [ ] Update `scenario_index.json` format
- [ ] Add `no_control` scenario generation

### Step 3: Update Cases Integration (2 hours)

- [ ] Follow existing cases structure (config/, analysis/, simulations/)
- [ ] Copy .add.xml files to simulation directories
- [ ] Create e1/ directories
- [ ] Remove results/ subdirectories (files go directly in sim_xxx/)

### Step 4: Update SUMO Config Generation (1 hour)

- [ ] Enforce relative paths only
- [ ] Network: `../../../../templates/network_files/*.net.xml`
- [ ] Routes: `../../config/*.rou.xml`
- [ ] Additional: Local filenames (files copied locally)

### Step 5: Update Tests (1 hour)

- [ ] Update E2E tests for new structure
- [ ] Test path resolution
- [ ] Test file copying logic

---

## Critical Fixes from User Feedback

### ✅ 1. No Chinese in Filenames
- **Before**: `scenario_交通事故_vss_12547.add.xml`
- **After**: `scenario_accident_vss_12547.add.xml`
- **Reason**: SUMO compatibility issues

### ✅ 2. Per-Scenario Metadata
- **Before**: Global `output/scenarios/scenario_metadata.json`
- **After**: Per-scenario `output/scenarios/01_accident/scenario_12547_vss/scenario_metadata.json`
- **Reason**: Better organization and independence

### ✅ 3. No_Control Scenarios
- **Added**: `scenario_{id}_no_control/` directories
- **Purpose**: Event-only scenarios for baseline comparison

### ✅ 4. Following Existing Cases Structure
- **config/**: OD files, TAZ files (NO network.xml)
- **simulations/sim_xxx/**: Files directly here (NO results/ subdirectory)
- **e1/**: E1 detector outputs
- **.add.xml**: Copied to simulation directory

### ✅ 5. Relative Paths Only
- **Network**: Relative from sim_xxx/ to templates/
- **Routes**: Relative from sim_xxx/ to config/
- **Additional**: Local filenames (files copied)
- **NO absolute paths**: Migration-friendly

---

## Approval Checklist

- [ ] ✅ No Chinese in .add.xml filenames
- [ ] ✅ Per-scenario metadata (not global)
- [ ] ✅ `no_control` scenarios added
- [ ] ✅ Following existing cases structure
- [ ] ✅ No results/ subdirectory
- [ ] ✅ e1/ directory for detector outputs
- [ ] ✅ .add.xml files copied to sim directories
- [ ] ✅ Relative paths only in sumocfg
- [ ] Architecture changes reviewed
- [ ] Implementation steps approved
- [ ] Timeline acceptable (6 hours total)

---

**Next Steps**: After approval, proceed with Step 1 (file naming updates) then implement all changes systematically.
