# Strategy Parameter Validation and XML Preview API

## Overview

This document describes the API endpoints for validating strategy parameters and generating SUMO XML previews. These endpoints support the OpenSpec feature: **Update Strategy Templates Based on SUMO Verification**.

## Table of Contents

- [Validation Endpoint](#validation-endpoint)
- [XML Preview Endpoint](#xml-preview-endpoint)
- [Parameter Types](#parameter-types)
- [Unit Conversions](#unit-conversions)
- [Examples](#examples)

---

## Validation Endpoint

### POST /api/v1/control/strategies/validate-params

Validates strategy parameters against template schema constraints.

**Purpose**: Ensure parameters are valid before XML generation or strategy creation

**Authentication**: None required

**Request**

```bash
curl -X POST "http://localhost:8000/api/v1/control/strategies/validate-params" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "vss_moderate",
    "parameters": {
      "affected_edges": ["edge1", "edge2"],
      "speed_steps": [
        {"time_hours": 7, "speed_kmh": 100},
        {"time_hours": 9, "speed_kmh": 80}
      ]
    }
  }'
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier (e.g., "vss_moderate", "dhs_peak_hours") |
| `parameters` | object | Yes | Strategy parameters matching template schema |

**Response - Success (200 OK)**

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    {
      "parameter": "speed_steps",
      "message": "Speed 130 km/h is at the upper limit. Consider 80-120 km/h for typical highways.",
      "constraint": {"speed_range": [30, 130]},
      "provided_value": 130
    }
  ],
  "converted_parameters": {
    "affected_edges": ["edge1", "edge2"],
    "speed_steps": [
      {"time_seconds": 25200, "speed_ms": 27.78},
      {"time_seconds": 32400, "speed_ms": 22.22}
    ]
  }
}
```

**Response - With Errors (200 OK)**

```json
{
  "valid": false,
  "errors": [
    {
      "parameter": "affected_edges",
      "message": "Required parameter 'affected_edges' not provided",
      "constraint": {"required": true},
      "provided_value": null
    },
    {
      "parameter": "speed_steps",
      "message": "Parameter 'speed_steps' requires at least 1 step(s)",
      "constraint": {"min_steps": 1},
      "provided_value": 0
    }
  ],
  "warnings": [],
  "converted_parameters": null
}
```

**Response - Template Not Found (404 Not Found)**

```json
{
  "error": "TEMPLATE_NOT_FOUND",
  "message": "Template 'invalid_template' not found"
}
```

**Response - Server Error (500 Internal Server Error)**

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Failed to validate parameters",
  "details": {"error_type": "ValueError"}
}
```

---

## XML Preview Endpoint

### POST /api/v1/control/strategies/generate-xml-preview

Generates a preview of the SUMO XML that will be created from strategy parameters.

**Purpose**: Show users the XML output before saving the strategy

**Authentication**: None required

**Request**

```bash
curl -X POST "http://localhost:8000/api/v1/control/strategies/generate-xml-preview" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "vss_moderate",
    "parameters": {
      "affected_edges": ["edge1", "edge2"],
      "speed_steps": [
        {"time_hours": 7, "speed_kmh": 100},
        {"time_hours": 9, "speed_kmh": 80}
      ]
    }
  }'
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | string | Yes | Template identifier |
| `parameters` | object | Yes | Strategy parameters |

**Response - Success (200 OK)**

```json
{
  "valid": true,
  "xml_content": "<variableSpeedSign id=\"strategy_001\" edges=\"edge1 edge2\"><step time=\"25200\" speed=\"27.78\"/><step time=\"32400\" speed=\"22.22\"/></variableSpeedSign>",
  "validation_message": "XML preview generated successfully",
  "errors": [],
  "warnings": []
}
```

**Response - Validation Failed (200 OK)**

```json
{
  "valid": false,
  "xml_content": null,
  "validation_message": "Parameters have validation errors. Fix errors before generating XML.",
  "errors": [
    {
      "parameter": "speed_steps",
      "message": "Speed 150 km/h is outside typical range 30-130 km/h"
    }
  ],
  "warnings": []
}
```

**Response - XML Generation Failed (200 OK)**

```json
{
  "valid": false,
  "xml_content": null,
  "validation_message": "Failed to generate XML: Invalid time step ordering",
  "errors": [
    {
      "parameter": "all",
      "message": "XML generation failed: Time steps must be in ascending order"
    }
  ],
  "warnings": []
}
```

---

## Parameter Types

### Primitive Types

#### integer
Integer values with optional min/max constraints.

```json
{
  "parameter_name": "hard_shoulder_lane_index",
  "parameter_type": "integer",
  "min_value": 0,
  "max_value": 7,
  "default_value": 3
}
```

#### number
Floating-point values with precision.

```json
{
  "parameter_name": "flow_rate",
  "parameter_type": "number",
  "min_value": 0.0,
  "max_value": 2000.0
}
```

#### string
Text values with optional length/pattern constraints.

```json
{
  "parameter_name": "description",
  "parameter_type": "string"
}
```

### Array Types

#### enum_array
Multiple selection from predefined values.

```json
{
  "parameter_name": "allowed_vehicle_types",
  "parameter_type": "enum_array",
  "enum_values": [
    {"value": "passenger", "label": "Passenger cars"},
    {"value": "bus", "label": "Buses"},
    {"value": "truck", "label": "Trucks"},
    {"value": "emergency", "label": "Emergency vehicles"}
  ],
  "default_value": ["passenger", "bus", "truck"]
}
```

#### edge_array
List of SUMO network edge IDs.

```json
{
  "parameter_name": "affected_edges",
  "parameter_type": "edge_array",
  "default_value": []
}
```

#### step_array
Time-dependent control steps (used by VSS).

```json
{
  "parameter_name": "speed_steps",
  "parameter_type": "step_array",
  "constraints": {"min_steps": 1, "max_steps": 10},
  "step_structure": {
    "time_display_unit": "hours",
    "time_sumo_unit": "seconds",
    "time_conversion_factor": 3600,
    "speed_display_unit": "km/h",
    "speed_sumo_unit": "m/s",
    "speed_conversion_factor": 0.277778,
    "speed_min": 30,
    "speed_max": 130
  },
  "default_value": [
    {"time_hours": 7, "speed_kmh": 100},
    {"time_hours": 9, "speed_kmh": 80}
  ]
}
```

#### flow_interval_array
Time-varying flow control intervals (used by TEC metering).

```json
{
  "parameter_name": "flow_intervals",
  "parameter_type": "flow_interval_array",
  "constraints": {"min_intervals": 1},
  "default_value": [
    {
      "begin_hours": 0,
      "end_hours": 6,
      "vehsPerHour": 480,
      "target_speed": 15
    }
  ]
}
```

---

## Unit Conversions

### Time Conversions

The validation endpoint automatically converts between display units (hours) and SUMO units (seconds):

- **Display to SUMO**: Hours × 3600 = Seconds
- **SUMO to Display**: Seconds ÷ 3600 = Hours

Example:
```
Input: {"time_hours": 7.5}
SUMO: 7.5 × 3600 = 27000 seconds
XML: <step time="27000" ... />
```

### Speed Conversions

Speed conversions between display units (km/h) and SUMO units (m/s):

- **Display to SUMO**: km/h ÷ 3.6 = m/s
- **SUMO to Display**: m/s × 3.6 = km/h

Example:
```
Input: {"speed_kmh": 100}
SUMO: 100 ÷ 3.6 = 27.78 m/s
XML: <step speed="27.78" ... />
```

### Reference Chart

| km/h | m/s |
|------|-----|
| 30   | 8.33 |
| 50   | 13.89 |
| 80   | 22.22 |
| 100  | 27.78 |
| 120  | 33.33 |
| 130  | 36.11 |

---

## Examples

### VSS (Variable Speed Sign) - Moderate Control

**Request**

```json
{
  "template_id": "vss_moderate",
  "parameters": {
    "affected_edges": ["edge_G4202_K0.0-K5.0", "edge_G4202_K5.0-K10.0"],
    "speed_steps": [
      {"time_hours": 0, "speed_kmh": 100},
      {"time_hours": 7, "speed_kmh": 100},
      {"time_hours": 9, "speed_kmh": 80},
      {"time_hours": 17, "speed_kmh": 100},
      {"time_hours": 19, "speed_kmh": 80},
      {"time_hours": 24, "speed_kmh": 100}
    ]
  }
}
```

**Response**

```json
{
  "valid": true,
  "xml_content": "<variableSpeedSign id=\"vss_moderate_001\" edges=\"edge_G4202_K0.0-K5.0 edge_G4202_K5.0-K10.0\"><step time=\"0\" speed=\"27.78\"/><step time=\"25200\" speed=\"27.78\"/><step time=\"32400\" speed=\"22.22\"/><step time=\"61200\" speed=\"27.78\"/><step time=\"68400\" speed=\"22.22\"/><step time=\"86400\" speed=\"27.78\"/></variableSpeedSign>",
  "validation_message": "XML preview generated successfully",
  "errors": [],
  "warnings": []
}
```

### DHS (Dynamic Hard Shoulder) - Peak Hours

**Request**

```json
{
  "template_id": "dhs_peak_hours",
  "parameters": {
    "affected_edges": ["edge_G4202_K0.0-K20.0"],
    "hard_shoulder_lane_index": 3,
    "intervals": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]
      },
      {
        "begin_hours": 7,
        "end_hours": 9,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
      },
      {
        "begin_hours": 9,
        "end_hours": 17,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]
      },
      {
        "begin_hours": 17,
        "end_hours": 19,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
      },
      {
        "begin_hours": 19,
        "end_hours": 24,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]
      }
    ]
  }
}
```

**Response**

```json
{
  "valid": true,
  "xml_content": "<rerouter id=\"dhs_peak_hours_001\" edges=\"edge_G4202_K0.0-K20.0\"><interval begin=\"0\" end=\"25200\"><closingLaneReroute id=\"3\" allow=\"\"/></interval><interval begin=\"25200\" end=\"32400\"><closingLaneReroute id=\"3\" allow=\"passenger bus truck emergency\"/></interval><interval begin=\"32400\" end=\"61200\"><closingLaneReroute id=\"3\" allow=\"\"/></interval><interval begin=\"61200\" end=\"68400\"><closingLaneReroute id=\"3\" allow=\"passenger bus truck emergency\"/></interval><interval begin=\"68400\" end=\"86400\"><closingLaneReroute id=\"3\" allow=\"\"/></interval></rerouter>",
  "validation_message": "XML preview generated successfully",
  "errors": [],
  "warnings": []
}
```

### TEC (Toll Entrance Control) - Metering

**Request**

```json
{
  "template_id": "tec_metering",
  "parameters": {
    "control_mode": "metering",
    "entrance_edge": "entrance_G4202_K0.0",
    "flow_intervals": [
      {
        "begin_hours": 0,
        "end_hours": 6,
        "vehsPerHour": 480,
        "target_speed": 15
      },
      {
        "begin_hours": 6,
        "end_hours": 9,
        "vehsPerHour": 180,
        "target_speed": 12
      },
      {
        "begin_hours": 9,
        "end_hours": 24,
        "vehsPerHour": 480,
        "target_speed": 15
      }
    ]
  }
}
```

**Response**

```json
{
  "valid": true,
  "xml_content": "<calibrator id=\"tec_metering_001\" edge=\"entrance_G4202_K0.0\" pos=\"0\"><flow begin=\"0\" end=\"21600\" vehsPerHour=\"480\" speed=\"15\"/><flow begin=\"21600\" end=\"32400\" vehsPerHour=\"180\" speed=\"12\"/><flow begin=\"32400\" end=\"86400\" vehsPerHour=\"480\" speed=\"15\"/></calibrator>",
  "validation_message": "XML preview generated successfully",
  "errors": [],
  "warnings": []
}
```

---

## Validation Rules by Parameter Type

### VSS (Variable Speed Sign)

| Parameter | Constraint | Error | Warning |
|-----------|-----------|-------|---------|
| `affected_edges` | Required, non-empty | Empty list | - |
| `speed_steps` | 1-10 steps | < 1 or > 10 | - |
| `speed_steps[].time_hours` | 0-24, ascending | Duplicate/descending | - |
| `speed_steps[].speed_kmh` | 30-130 | Out of range | > 120 or < 50 |
| `applicable_vehicle_types` | SUMO enum values | Invalid type | Non-standard type |

### DHS (Dynamic Hard Shoulder)

| Parameter | Constraint | Error | Warning |
|-----------|-----------|-------|---------|
| `affected_edges` | Required, non-empty | Empty list | - |
| `hard_shoulder_lane_index` | 0-7 | Out of range | - |
| `intervals` | 1+ intervals | < 1 interval | > 5 intervals |
| `intervals[].status` | "OPEN" or "CLOSED" | Invalid status | - |
| `intervals[].allowed_vehicle_types` | SUMO enum values | Invalid type | - |

### TEC (Toll Entrance Control)

| Parameter | Constraint | Error | Warning |
|-----------|-----------|-------|---------|
| `entrance_edge` or `entrance_edges` | Required | Empty | - |
| `flow_intervals[].vehsPerHour` | 0-2000 | Out of range | > 1500 |
| `flow_intervals[].target_speed` | 0-50 m/s | Out of range | - |
| `allowed_vehicle_types` | SUMO enum values | Invalid type | - |

---

## Error Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Valid (errors/warnings may be present) | Valid request processed |
| 400 | Bad request | Invalid JSON, missing required field |
| 404 | Template not found | Template ID doesn't exist |
| 500 | Server error | Unexpected exception during validation |
| 503 | Service unavailable | Database connection failed |

---

## Integration with Frontend

### Workflow

1. **Load Template**: GET `/api/v1/control/templates/{template_id}`
2. **Generate Form**: JavaScript renders form from template schema
3. **Validate on Change** (optional): Call validate endpoint for real-time feedback
4. **Generate XML Preview**: POST to generate-xml-preview endpoint
5. **Create Strategy**: Save strategy with validated/converted parameters

### JavaScript Integration

```javascript
// Load template and generate form
const template = await fetch(`/api/v1/control/templates/vss_moderate`);
const form = generateFormFromTemplate('vss_moderate');

// Validate parameters
const validation = await fetch('/api/v1/control/strategies/validate-params', {
  method: 'POST',
  body: JSON.stringify({
    template_id: 'vss_moderate',
    parameters: extractFormParameters(form)
  })
});

// Generate XML preview
const preview = await fetch('/api/v1/control/strategies/generate-xml-preview', {
  method: 'POST',
  body: JSON.stringify({
    template_id: 'vss_moderate',
    parameters: extractFormParameters(form)
  })
});
```

---

## Performance Characteristics

| Operation | Target | Typical |
|-----------|--------|---------|
| Parameter validation | < 200ms | 50-100ms |
| XML generation | < 150ms | 30-50ms |
| Full validation + preview | < 300ms | 100-150ms |

---

## Changelog

### v2.0 (2025-10-24)

- Initial release with VSS, DHS, TEC validation
- XML preview generation
- Automatic unit conversion (hours↔seconds, km/h↔m/s)
- SUMO-specific constraint validation
- Real-time error/warning feedback
