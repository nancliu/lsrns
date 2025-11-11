# Architecture Summary - Event Scenario System

**Version**: 2.0 (Updated 2025-11-11)
**Status**: Approved Architecture

---

## Quick Reference

### Scenario Library Structure (Read-Only)

```
output/scenarios/
├── 01_accident/
│   ├── scenario_12547_vss/
│   │   ├── scenario_accident_vss_12547.add.xml  ✏️ (English only)
│   │   ├── event_description.json
│   │   ├── traffic_input_config.json
│   │   ├── control_strategy_config.json
│   │   └── scenario_metadata.json  ✏️ (per-scenario)
│   ├── scenario_12547_no_control/  ✏️ NEW
│   │   ├── scenario_accident_event_12547.add.xml
│   │   └── scenario_metadata.json
│   └── scenario_12547_dhs/
└── scenario_index.json
```

**❌ No**: `simulation.sumocfg`, `results/`, Chinese filenames
**✅ Yes**: English names, per-scenario metadata, `no_control` type

### Cases Structure (With Simulations)

```
cases/case_xxx/
├── metadata.json
├── config/  ✏️ (OD + TAZ, NO network.xml)
│   ├── *.od.xml
│   ├── *.rou.xml
│   └── TAZ_*.add.xml
├── analysis/
└── simulations/
    └── scenario_sim_12547/  ✏️ NEW
        ├── sim_baseline/
        │   ├── simulation.sumocfg (relative paths)
        │   ├── TAZ_6.add.xml (copied)
        │   ├── e1/ (detector outputs)
        │   ├── summary.xml (no results/)
        │   └── tripinfo.xml
        ├── sim_with_event/
        │   ├── simulation.sumocfg
        │   ├── scenario_accident_event_12547.add.xml (copied)
        │   └── e1/
        ├── sim_with_implemented_control/
        └── sim_with_option_control_vss/
```

**Key Features**:
- ✅ Files directly in `sim_xxx/` (no `results/`)
- ✅ `e1/` directory for detector outputs
- ✅ `.add.xml` files copied to simulation directory
- ✅ Relative paths only in sumocfg

---

## File Naming Convention

### Event Types (English)

| Chinese | English | Directory |
|---------|---------|-----------|
| 交通事故 | accident | 01_accident |
| 交通阻塞 | congestion | 02_congestion |
| 交通管制 | road_control | 03_road_control |
| 地质灾害 | geological | 04_geological |
| 车辆故障 | breakdown | 05_breakdown |
| 恶劣天气 | weather | 06_weather |

### Filename Template

```
scenario_{event_type}_{strategy}_{event_id}.add.xml

Examples:
- scenario_accident_vss_12547.add.xml
- scenario_accident_event_12547.add.xml (no_control)
- scenario_congestion_tec_98765.add.xml
```

---

## SUMO Config Paths (Relative Only)

```xml
<configuration>
    <input>
        <!-- ✅ Network (4 levels up) -->
        <net-file value="../../../../templates/network_files/sichuan202508v7.net.xml"/>

        <!-- ✅ Routes (2 levels up to config) -->
        <route-files value="../../config/*.rou.xml"/>

        <!-- ✅ Additional (local, copied) -->
        <additional-files value="TAZ_6.add.xml,scenario_accident_vss_12547.add.xml"/>
    </input>
</configuration>
```

**❌ NO absolute paths**: `D:/projects/OD_SIM/...`

---

## Metadata Models

### Per-Scenario Metadata

**Location**: `output/scenarios/01_accident/scenario_12547_vss/scenario_metadata.json`

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
  "applied_to_cases": [
    {
      "case_id": "case_morning_peak_20251111",
      "simulation_dir": "scenario_sim_12547",
      "simulation_types": ["sim_baseline", "sim_with_event", "sim_with_option_control_vss"],
      "created_date": "2025-11-11",
      "status": "completed"
    }
  ]
}
```

### Scenario Index

**Location**: `output/scenarios/scenario_index.json`

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
  }
}
```

---

## 4 Simulation Types

1. **`sim_baseline/`**: No event, no control (baseline traffic)
2. **`sim_with_event/`**: Event only (impact without control)
3. **`sim_with_implemented_control/`**: Event + actual control used
4. **`sim_with_option_control_{strategy}/`**: Event + alternative control

---

## Critical Requirements Checklist

- [ ] ✅ No Chinese in .add.xml filenames
- [ ] ✅ Per-scenario metadata (not global)
- [ ] ✅ `no_control` scenarios included
- [ ] ✅ Following existing cases structure
- [ ] ✅ No `results/` subdirectory
- [ ] ✅ `e1/` directory for detector outputs
- [ ] ✅ `.add.xml` files copied to sim directories
- [ ] ✅ Relative paths only in sumocfg

---

**Full Details**: See `ARCHITECTURE_CHANGES.md` for complete documentation.
