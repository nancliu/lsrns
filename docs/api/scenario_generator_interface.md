# Scenario Generator Interface Contract

**Version**: 1.0
**Date**: 2025-11-14
**Status**: Official

---

## Overview

This document defines the interface contract between scenario generation scripts and the core `ScenarioGenerator` class. It ensures consistency across all scenario types and provides clear expectations for parameter formats.

---

## ScenarioGenerator API

### Class: `ScenarioGenerator`

**Location**: `shared/control_tools/scenario_generator.py`

**Purpose**: Generate complete scenario bundles (XML, config files, event descriptions) for SUMO traffic simulations with optional control strategies.

###Constructor

```python
ScenarioGenerator(network_file: str, output_base_dir: str = "output/scenarios")
```

**Parameters**:
- `network_file` (str): Path to SUMO network file (.net.xml)
- `output_base_dir` (str): Base directory for scenario output

**Example**:
```python
generator = ScenarioGenerator(
    network_file='templates/network_files/sichuan202508v7.net.xml',
    output_base_dir='output/scenarios'
)
```

### Method: `generate_scenario()`

```python
def generate_scenario(
    event_data: Dict[str, Any],
    strategy_type: str = None,
    control_params: Dict[str, Any] = None
) -> Dict[str, Path]
```

**Purpose**: Generate a complete scenario bundle with event data and optional control strategy.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_data` | dict | Yes | Event information (see Event Data Format) |
| `strategy_type` | str | No | Control strategy type: 'VSS', 'TEC', 'DHS', or None for NO_CONTROL |
| `control_params` | dict | No | Strategy-specific parameters (see Control Parameters) |

**Returns**:
```python
{
    'add_xml': Path,                      # SUMO additional file (.add.xml)
    'event_description': Path,            # Event description JSON
    'traffic_config': Path,               # Traffic input configuration JSON
    'control_strategy_config': Path       # Control strategy configuration JSON (if strategy_type provided)
}
```

---

## Event Data Format

### Required Fields

```python
event_data = {
    # Core identification
    'report_id': str,           # Unique event ID
    'event_type': str,          # Event type (Chinese, e.g., '交通事故', '流量激增')
    'event_description': str,   # Detailed description

    # Location information
    'road': str,                # Road name (e.g., 'G76厦蓉高速')
    'direction': str,           # Direction ('双向', '上行', '下行')
    'mileage': str,             # Mileage marker (e.g., 'K1850+000') or empty string
    'edge_id': str,             # SUMO edge ID
    'junction_id': str,         # SUMO junction ID or empty string

    # Time information
    'start_time': str,          # Event start (format: 'YYYY-MM-DD HH:MM:SS')
    'end_time': str,            # Event end (format: 'YYYY-MM-DD HH:MM:SS')

    # Impact information
    'affected_lanes': list,     # List of affected lane IDs (e.g., ['-3734_0', '-3734_1'])
}
```

### Example

```python
event_data = {
    'report_id': '10754',
    'event_type': '交通事故',
    'event_description': '单车撞护栏事故，占用第一车道',
    'road': 'G76厦蓉高速',
    'direction': '双向',
    'mileage': 'K1850+000',
    'edge_id': '-3734',
    'junction_id': '-3734',
    'start_time': '2025-06-10 10:43:48',
    'end_time': '2025-06-10 11:19:50',
    'affected_lanes': ['-3734_0']
}
```

---

## Control Parameters Format

### VSS (Variable Speed Sign)

**Purpose**: Apply speed limits to road segments

#### Complete Format

```python
control_params = {
    'affected_edges': list[str],        # Required: Edges to apply VSS
    'speed_steps': list[dict],          # Speed control steps
    'response_delay_seconds': int,      # Delay before activation (default: 300)
    'recovery_period_seconds': int,     # Duration after event (default: 600)
    'affected_lanes': list[str]         # Optional: Specific lanes (default: all)
}
```

**speed_steps format**:
```python
{
    'speed_kmh': float,          # Required: Speed limit in km/h
    'time_seconds': int,         # Optional: Activation time (auto-calculated if omitted)
    'begin': int,                # Optional: Begin time (auto-calculated)
    'end': int                   # Optional: End time (auto-calculated)
}
```

#### Simplified Format (Recommended)

```python
control_params = {
    'affected_edges': ['-3734'],
    'speed_limit_kmh': 70,              # Single speed limit (no steps)
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}
```

**Auto-calculated timing**:
- `time_seconds` = event_start + response_delay - simulation_start
- `begin` = time_seconds
- `end` = event_end + recovery_period - simulation_start

#### Example

```python
# Simplified (recommended for most cases)
control_params = {
    'affected_edges': ['-3734'],
    'speed_steps': [{'speed_kmh': 70}],
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}

# Complete (when manual timing control needed)
control_params = {
    'affected_edges': ['-3734'],
    'speed_steps': [
        {'time_seconds': 2100, 'speed_kmh': 80},
        {'time_seconds': 3600, 'speed_kmh': 90}
    ],
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}
```

---

### TEC (Toll Entrance Control)

**Purpose**: Control traffic flow at entrance points

#### Complete Format

```python
control_params = {
    'entrance_edges': list[str],         # Required: Entrance edges
    'flow_intervals': list[dict],        # Flow control intervals
    'response_delay_seconds': int,       # Delay before activation (default: 300)
    'recovery_period_seconds': int,      # Duration after event (default: 600)
}
```

**flow_intervals format**:
```python
{
    'flow_coefficient': float,    # Required: Flow multiplier (0.8 = 80% of baseline)
    'vehsPerHour': int,           # Optional: Explicit flow rate (vehicles/hour)
    'begin_seconds': int,         # Optional: Begin time (auto-calculated)
    'end_seconds': int            # Optional: End time (auto-calculated)
}
```

#### Simplified Format (Recommended)

```python
control_params = {
    'entrance_edges': ['-3734'],
    'flow_reduction': 0.2,               # Reduce flow by 20% (baseline 3600 veh/h)
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}
```

**Auto-calculated values**:
- `vehsPerHour` = 3600 * (1 - flow_reduction)  # For simplified format
- `begin_seconds` = event_start + response_delay - simulation_start
- `end_seconds` = event_end + recovery_period - simulation_start

#### Example

```python
# Simplified (recommended)
control_params = {
    'entrance_edges': ['-3734'],
    'flow_intervals': [{'flow_coefficient': 0.9}],  # 90% of normal flow
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}

# With explicit flow rate
control_params = {
    'entrance_edges': ['-3734'],
    'flow_intervals': [
        {'vehsPerHour': 2880}  # Explicit flow rate
    ],
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}
```

---

### DHS (Dynamic Hard Shoulder)

**Purpose**: Open hard shoulder during peak periods

#### Format

```python
control_params = {
    'shoulder_segments': list[str],      # Required: Edge segments for shoulder
    'activation_schedule': list[dict],   # Required: Time-based activation
    'response_delay_seconds': int,       # Default: 0 (pre-scheduled)
    'recovery_period_seconds': int       # Default: 0 (pre-scheduled)
}
```

**activation_schedule format**:
```python
{
    'begin': int,                        # Required: Begin time (simulation seconds)
    'end': int,                          # Required: End time (simulation seconds)
    'allowed_vehicle_types': list[str]   # Optional: ['passenger'] (default: all)
}
```

#### Example

```python
control_params = {
    'shoulder_segments': [
        '-12854', '-12856', '-12858', '-12874', '-12876'
    ],
    'activation_schedule': [{
        'begin': 3300,                    # 7:30 AM (if sim starts at 6:25)
        'end': 10500,                     # 9:30 AM
        'allowed_vehicle_types': ['passenger']
    }],
    'response_delay_seconds': 0,          # Pre-scheduled, no delay
    'recovery_period_seconds': 0
}
```

---

## Generated Configuration Files

### 1. control_strategy_config.json

**Location**: `{scenario_dir}/control_strategy_config.json`

**Format**:
```json
{
  "strategy_type": "VSS|TEC|DHS",
  "strategy_name": "可变限速标志|收费站管控|动态硬路肩",
  "parameters": {
    "affected_edges": [...],
    "speed_steps": [...],      // VSS only
    "entrance_edges": [...],   // TEC only
    "flow_intervals": [...],   // TEC only
    "shoulder_segments": [...],// DHS only
    "activation_schedule": [...], // DHS only
    "response_delay_seconds": 300,
    "recovery_period_seconds": 600
  },
  "timing": {
    "activation_time": "YYYY-MM-DD HH:MM:SS",
    "deactivation_time": "YYYY-MM-DD HH:MM:SS",
    "response_delay_minutes": 5.0,
    "recovery_period_minutes": 10.0
  }
}
```

### 2. event_description.json

**Location**: `{scenario_dir}/event_description.json`

**Format**:
```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "event_description": "...",
  "location": {
    "road": "G76厦蓉高速",
    "direction": "双向",
    "mileage": "K1850+000",
    "junction_id": "-3734",
    "edge_id": "-3734"
  },
  "time": {
    "start_time": "2025-06-10 10:43:48",
    "end_time": "2025-06-10 11:19:50",
    "duration_hours": 0.6
  },
  "impact": {
    "affected_lanes": ["第一车道"],
    "lane_ids": ["-3734_0"]
  }
}
```

### 3. traffic_input_config.json

**Location**: `{scenario_dir}/traffic_input_config.json`

**Format**:
```json
{
  "simulation_start_time": "2025-06-10 10:13:48",
  "simulation_end_time": "2025-06-10 11:49:50",
  "simulation_duration_hours": 1.6,
  "od_table": "baseline.sheng_nei_od_hour_09",
  "taz_file": "sichuan.taz.xml",
  "network_file": "sichuan202508v7.net.xml"
}
```

---

## Field Name Reference

### Time-related Fields

| Usage | scenario_generator generates | additional_generator expects | Status |
|-------|----------------------------|----------------------------|--------|
| VSS activation time | `time_seconds`, `begin`, `end` | `time_seconds` or `time_hours` | ✅ Compatible |
| TEC begin time | `begin_seconds`, `begin` | `begin_seconds` or `begin_hours` | ✅ Compatible |
| TEC end time | `end_seconds`, `end` | `end_seconds` or `end_hours` | ✅ Compatible |
| VSS speed | `speed_kmh` | `speed_kmh` or `speed_ms` | ✅ Compatible |
| TEC flow | `flow_coefficient`, `vehsPerHour` | `flow_coefficient`, `vehsPerHour` | ✅ Compatible |

### Simplified vs Complete Format

| Strategy | Simplified Field | Complete Field | Auto-conversion |
|----------|-----------------|----------------|-----------------|
| VSS | `speed_limit_kmh` | `speed_steps` | ✅ Yes |
| TEC | `flow_reduction` | `flow_intervals` | ✅ Yes |
| DHS | N/A | `activation_schedule` | N/A (always complete) |

---

## Validation Rules

### VSS Parameters

- ✅ `affected_edges` must be non-empty list
- ✅ `speed_kmh` must be 30-130 km/h
- ✅ `time_seconds` must be 0-86400 (if provided)
- ⚠️ Warning if `speed_steps` is empty and `speed_limit_kmh` not provided

### TEC Parameters

- ✅ `entrance_edges` must be non-empty list
- ✅ `flow_coefficient` must be 0.1-1.0 (if provided)
- ✅ `vehsPerHour` must be > 0 (if provided)
- ⚠️ Warning if `flow_intervals` is empty and `flow_reduction` not provided

### DHS Parameters

- ✅ `shoulder_segments` must be non-empty list
- ✅ `activation_schedule` must have at least one entry
- ✅ `begin` < `end` for each schedule entry

---

## Time Calculation Logic

### Automatic Timing (Recommended)

When `begin`/`end`/`time_seconds` are **not provided**:

1. **Read simulation time range** from `traffic_input_config.json`
2. **Calculate control activation time**:
   ```
   activation_time = event_start + response_delay
   ```
3. **Calculate control deactivation time**:
   ```
   deactivation_time = event_end + recovery_period
   ```
4. **Convert to simulation seconds** (relative to sim_start):
   ```
   begin_seconds = max(0, (activation_time - sim_start).total_seconds())
   end_seconds = min((deactivation_time - sim_start).total_seconds(), sim_duration)
   ```
5. **Populate all time fields**:
   - VSS: `time_seconds`, `begin`, `end`
   - TEC: `begin_seconds`, `end_seconds`, `begin`, `end`

### Manual Timing (Advanced)

When `begin`/`end`/`time_seconds` are **provided**:
- Use provided values directly
- Skip automatic calculation
- Validate against simulation duration

---

## Best Practices

### DO ✅

1. **Use simplified format for common cases**:
   ```python
   {'affected_edges': [...], 'speed_steps': [{'speed_kmh': 70}]}
   ```
2. **Let scenario_generator calculate timing automatically**
3. **Validate edge IDs exist in network before generation**
4. **Use consistent response_delay and recovery_period**
5. **Provide clear event_description**

### DON'T ❌

1. **Don't manually calculate `begin`/`end` unless necessary**
2. **Don't use pipe-separated edge IDs** (`-3734|-1234`)
3. **Don't provide both simplified and complete format** (choose one)
4. **Don't use hardcoded absolute times** (use relative timing)
5. **Don't skip required fields** in event_data

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-14 | Initial interface contract documentation |

---

## Related Documents

- `CRITICAL_ISSUES_FIX_COMPLETE.md` - Phase 1 completion report
- `FLOWSURGE_REFACTORING_COMPLETE.md` - Phase 2 completion report
- `shared/control_tools/scenario_generator.py` - Implementation
- `shared/control_tools/additional_generator.py` - XML generation

---

**Maintained by**: OD_SIM Development Team
**Contact**: See CLAUDE.md for project guidelines
