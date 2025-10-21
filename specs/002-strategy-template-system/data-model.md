# Phase 1: Data Model - Strategy Template System

**Date**: 2025-10-19
**Feature**: Strategy Template System (Phase 1A)
**Status**: Designed

## Entity Overview

This feature introduces 3 core entities and 1 enumeration for managing traffic control strategy templates:

1. **ControlTemplate** - Root entity representing a strategy template
2. **ParameterSchema** - Embedded entity defining configurable parameters
3. **StrategyType** - Enumeration of supported strategy types
4. **TemplatesIndex** - Generated metadata for template discovery

## Entity Definitions

### 1. ControlTemplate

**Purpose**: Represents a traffic control strategy template that serves as a blueprint for creating strategy instances (Phase 1C).

**Storage**: File-based (`templates/control_strategies/{type}/{name}.json`)

**Attributes**:

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `template_id` | str | Yes | Unique identifier (e.g., "vss_moderate") | Lowercase alphanumeric + underscores, no spaces |
| `template_name` | str | Yes | Display name (Chinese) | 1-100 characters |
| `description` | str | Yes | Detailed explanation (Chinese) | 1-500 characters |
| `strategy_type` | StrategyType | Yes | Strategy category (VSS/DHS/TEC) | Must be valid StrategyType enum value |
| `parameters_schema` | List[ParameterSchema] | Yes | Array of parameter definitions | At least 1 parameter, max 20 parameters |
| `version` | str | Yes | Template version (e.g., "1.0") | Semantic versioning format "X.Y" or "X.Y.Z" |
| `created_at` | datetime | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | datetime | Yes | Last modification timestamp | ISO 8601 format, >= created_at |

**Relationships**:
- **Has many** ParameterSchema (1:N, embedded)
- **Serves as blueprint for** Strategy instances (1:N, Phase 1C future relationship)

**Uniqueness Constraints**:
- `template_id` must be globally unique across all templates
- No two templates can have identical `template_name` within the same `strategy_type`

**Lifecycle States**: N/A (templates are static read-only configuration)

**Example**:
```json
{
  "template_id": "vss_moderate",
  "template_name": "可变限速 - 中等控制",
  "description": "适用于高峰期的中等强度限速控制，限速值80-100 km/h，适合交通流量中等的高速路段",
  "strategy_type": "VSS",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "array",
      "description": "受限速影响的路段列表",
      "required": true,
      "default_value": [],
      "min_value": null,
      "max_value": null,
      "allowed_values": null,
      "unit": null
    },
    {
      "parameter_name": "speed_limit",
      "parameter_type": "integer",
      "description": "限速值（公里/小时）",
      "required": true,
      "default_value": 80,
      "min_value": 40,
      "max_value": 100,
      "allowed_values": null,
      "unit": "km/h"
    }
  ],
  "version": "1.0",
  "created_at": "2025-10-19T00:00:00Z",
  "updated_at": "2025-10-19T00:00:00Z"
}
```

---

### 2. ParameterSchema

**Purpose**: Defines a single configurable parameter within a template, including type, constraints, and default values.

**Storage**: Embedded within ControlTemplate JSON

**Attributes**:

| Attribute | Type | Required | Description | Validation Rules |
|-----------|------|----------|-------------|------------------|
| `parameter_name` | str | Yes | Parameter identifier | Lowercase letters, numbers, underscores only; 1-50 chars |
| `parameter_type` | str | Yes | Data type of parameter | Must be one of: integer, float, string, boolean, array |
| `description` | str | Yes | Parameter explanation (Chinese) | 1-200 characters |
| `required` | bool | Yes | Whether parameter is mandatory | true or false |
| `default_value` | Any | No | Default value if not specified | Type must match parameter_type |
| `min_value` | int\|float | No | Minimum value (numeric types) | Only for integer/float types; < max_value if both set |
| `max_value` | int\|float | No | Maximum value (numeric types) | Only for integer/float types; > min_value if both set |
| `allowed_values` | List[Any] | No | Enum values (for restricted choices) | Type of items must match parameter_type |
| `unit` | str | No | Display unit (e.g., "km/h", "seconds") | 1-20 characters; for numeric types only |

**Supported Parameter Types**:
- `integer`: Whole numbers (e.g., speed limits, vehicle counts)
- `float`: Decimal numbers (e.g., flow rates, percentages)
- `string`: Text values (e.g., edge IDs, descriptions)
- `boolean`: True/False flags (e.g., enable/disable)
- `array`: Lists of values (e.g., multiple edge IDs, time intervals)

**Relationships**:
- **Belongs to** ControlTemplate (N:1, embedded)

**Validation Rules**:
1. If `parameter_type` is `integer` or `float`, `min_value` and `max_value` are optional but recommended
2. If `allowed_values` is set, `default_value` must be one of the allowed values
3. If `required` is true, `default_value` may still be provided for UI convenience
4. `unit` field only makes sense for numeric types (integer/float)

**Example** (embedded in ControlTemplate):
```json
{
  "parameter_name": "time_intervals",
  "parameter_type": "array",
  "description": "限速生效的时段列表，格式：[[7, 9], [17, 19]] 表示7-9点和17-19点",
  "required": true,
  "default_value": [[7, 9], [17, 19]],
  "min_value": null,
  "max_value": null,
  "allowed_values": null,
  "unit": null
}
```

---

### 3. StrategyType (Enumeration)

**Purpose**: Define supported traffic control strategy categories.

**Storage**: Python Enum in `api/models/control/entities/template.py`

**Values**:

| Code | Display Name (Chinese) | Description |
|------|----------------------|-------------|
| `VSS` | 可变限速 | Variable Speed Signs - Dynamic speed limit control on highway segments |
| `DHS` | 动态硬路肩 | Dynamic Hard Shoulder - Temporary opening of hard shoulder lanes during peak hours |
| `TEC` | 收费站入口管控 | Toll Entrance Control - Ramp metering or entrance closure for traffic flow regulation |

**Implementation**:
```python
from enum import Enum

class StrategyType(str, Enum):
    VSS = "VSS"  # Variable Speed Signs
    DHS = "DHS"  # Dynamic Hard Shoulder
    TEC = "TEC"  # Toll Entrance Control

    @property
    def display_name(self) -> str:
        names = {
            "VSS": "可变限速",
            "DHS": "动态硬路肩",
            "TEC": "收费站入口管控"
        }
        return names[self.value]

    @property
    def description(self) -> str:
        descriptions = {
            "VSS": "高速公路路段动态限速控制",
            "DHS": "高峰期临时开放硬路肩车道",
            "TEC": "匝道流量控制或入口关闭"
        }
        return descriptions[self.value]
```

**Extensibility**: Additional strategy types can be added in future phases (e.g., "VMS" for Variable Message Signs, "LCS" for Lane Control Signals).

---

### 4. TemplatesIndex

**Purpose**: Auto-generated metadata file for efficient template discovery and listing.

**Storage**: File-based (`templates/control_strategies/templates_index.json`)

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `templates` | List[TemplateIndexEntry] | Yes | Array of template summary entries |
| `generated_at` | datetime | Yes | Index generation timestamp |
| `total_count` | int | Yes | Total number of valid templates |
| `by_type` | Dict[str, int] | Yes | Count of templates per strategy type |

**TemplateIndexEntry**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | str | Yes | Unique template identifier |
| `template_name` | str | Yes | Display name |
| `strategy_type` | str | Yes | Strategy type code (VSS/DHS/TEC) |
| `description_preview` | str | Yes | First 100 characters of description |
| `file_path` | str | Yes | Relative path to template JSON file |

**Generation Logic**:
- Auto-generated at API startup by `template_loader.py`
- Scans `templates/control_strategies/` directory recursively
- Validates each template, includes only valid templates
- Overwrites existing index file on each startup (ensures consistency)

**Example**:
```json
{
  "templates": [
    {
      "template_id": "vss_moderate",
      "template_name": "可变限速 - 中等控制",
      "strategy_type": "VSS",
      "description_preview": "适用于高峰期的中等强度限速控制，限速值80-100 km/h，适合交通流量中等的高速路段...",
      "file_path": "variable_speed_sign/vss_moderate.json"
    },
    {
      "template_id": "vss_strict",
      "template_name": "可变限速 - 严格控制",
      "strategy_type": "VSS",
      "description_preview": "适用于拥堵严重时段的严格限速控制，限速值60-80 km/h，用于缓解下游瓶颈...",
      "file_path": "variable_speed_sign/vss_strict.json"
    }
  ],
  "generated_at": "2025-10-19T08:00:00Z",
  "total_count": 5,
  "by_type": {
    "VSS": 2,
    "DHS": 1,
    "TEC": 2
  }
}
```

---

## Entity Relationships

```
StrategyType (Enum)
    ↑
    |
    | (1:N)
    |
ControlTemplate
    |
    | (1:N, embedded)
    ↓
ParameterSchema

TemplatesIndex
    |
    | (references)
    ↓
ControlTemplate (summary only)
```

**Relationship Details**:
1. **StrategyType → ControlTemplate**: Each template belongs to one strategy type category (VSS/DHS/TEC)
2. **ControlTemplate → ParameterSchema**: Each template has 1-20 parameter definitions (embedded, not separate entities)
3. **TemplatesIndex → ControlTemplate**: Index references templates for fast lookup (generated metadata, not persistent relationship)

---

## Data Validation Rules

### Template-Level Validation

1. **Unique IDs**: No two templates can share the same `template_id`
2. **Strategy Type Consistency**: All templates under `templates/control_strategies/variable_speed_sign/` must have `strategy_type="VSS"`
3. **Parameter Count**: Each template must have at least 1 parameter, maximum 20 parameters
4. **Version Format**: Version string must match pattern `\d+\.\d+(\.\d+)?` (e.g., "1.0", "1.2.3")
5. **Timestamps**: `updated_at` >= `created_at`

### Parameter-Level Validation

1. **Type Consistency**: `default_value` type must match `parameter_type`
2. **Range Constraints**: If both `min_value` and `max_value` are set, `min_value` < `max_value`
3. **Allowed Values**: If `allowed_values` is set, `default_value` (if present) must be in `allowed_values`
4. **Required Parameters**: If `required=true`, parameter must be provided when creating strategy instances (Phase 1C)
5. **Unit Applicability**: `unit` field should only be present for `integer` or `float` types

### Cross-Entity Validation

1. **Index Consistency**: TemplatesIndex must reference only valid templates (no orphan references)
2. **File Path Consistency**: Template `file_path` in index must match actual file location
3. **Count Accuracy**: `total_count` in index must equal length of `templates` array

---

## Data Migration and Versioning

**Phase 1A**: No migration needed (new feature, no existing data)

**Future Considerations**:
- **Template Schema Changes**: If ParameterSchema structure changes, use version-specific loaders
- **Strategy Type Additions**: Add new enum values without breaking existing templates
- **Backward Compatibility**: Maintain support for older template versions (v1.0, v1.1, etc.)

---

## Performance Considerations

1. **Startup Loading**: All templates loaded into memory at startup (~5KB per template, 25KB total for Phase 1A)
2. **Index Caching**: Index generated once at startup, cached in memory for subsequent requests
3. **File I/O**: Template files read once at startup, not on every API request
4. **Scalability**: If template count exceeds 50, consider lazy loading or database migration

**Estimated Data Volumes**:
- Phase 1A: 5 templates (~25KB JSON total)
- Phase 1B-1D: ~15-20 templates (~75-100KB)
- Long-term (Phase 2+): ~50-100 templates (~250-500KB)

---

## Testing Data Model

**Test Fixtures**:
- Valid templates (vss_moderate, vss_strict, dhs_peak_hours, tec_truck_ban, tec_entrance_close)
- Invalid templates (missing required fields, invalid types, duplicate IDs)
- Edge cases (empty parameters_schema, extreme values, special characters)

**Unit Tests** (`tests/unit/shared/test_template_loader.py`):
- `test_load_valid_template()` - Verify correct template loading
- `test_validate_template_missing_field()` - Reject invalid templates
- `test_generate_index()` - Verify index generation logic
- `test_unique_id_constraint()` - Reject duplicate template IDs

**Integration Tests** (`tests/integration/api/test_control_template_routes.py`):
- `test_get_templates_returns_all()` - API returns all valid templates
- `test_get_template_by_id()` - API returns full template details
- `test_get_template_invalid_id_returns_404()` - API handles missing templates

---

## Pydantic Models

**Implementation** (`api/models/control/entities/template.py`):

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class StrategyType(str, Enum):
    VSS = "VSS"
    DHS = "DHS"
    TEC = "TEC"

class ParameterSchema(BaseModel):
    parameter_name: str = Field(..., min_length=1, max_length=50, regex="^[a-z0-9_]+$")
    parameter_type: str = Field(..., regex="^(integer|float|string|boolean|array)$")
    description: str = Field(..., min_length=1, max_length=200)
    required: bool
    default_value: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    unit: Optional[str] = Field(None, max_length=20)

    @validator('max_value')
    def max_greater_than_min(cls, v, values):
        if v is not None and 'min_value' in values and values['min_value'] is not None:
            if v <= values['min_value']:
                raise ValueError('max_value must be greater than min_value')
        return v

class ControlTemplate(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=50, regex="^[a-z0-9_]+$")
    template_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    strategy_type: StrategyType
    parameters_schema: List[ParameterSchema] = Field(..., min_items=1, max_items=20)
    version: str = Field(..., regex=r"^\d+\.\d+(\.\d+)?$")
    created_at: datetime
    updated_at: datetime

    @validator('updated_at')
    def updated_after_created(cls, v, values):
        if 'created_at' in values and v < values['created_at']:
            raise ValueError('updated_at must be >= created_at')
        return v

class TemplateIndexEntry(BaseModel):
    template_id: str
    template_name: str
    strategy_type: str
    description_preview: str = Field(..., max_length=100)
    file_path: str

class TemplatesIndex(BaseModel):
    templates: List[TemplateIndexEntry]
    generated_at: datetime
    total_count: int
    by_type: dict[str, int]
```

---

## Summary

The data model is **fully defined and ready for implementation**. All entities have:
- Clear attributes with types and validation rules
- Documented relationships
- Pydantic models for type safety
- Test scenarios for validation

**Next Phase**: Generate API contracts (OpenAPI specs) based on these entities.
