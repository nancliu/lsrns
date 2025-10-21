# Quickstart: Strategy Template System (Phase 1A)

**Purpose**: Get developers up and running with the strategy template system implementation in <30 minutes.

**Prerequisites**:
- Python 3.10+ installed
- OD_SIM repository cloned
- Conda/mamba environment activated (`od-sim`)
- FastAPI and Pydantic installed (check `requirements.txt`)

## 5-Minute Overview

**What we're building**: A read-only template browsing system with 5 traffic control strategy templates (VSS, DHS, TEC).

**Architecture**:
```
Frontend (JS) → API (FastAPI) → Service Layer → TemplateLoader (Shared)
                                                         ↓
                                                  JSON Files
```

**Key Components**:
1. **5 JSON template files** (`templates/control_strategies/`)
2. **TemplateLoader utility** (`shared/control_tools/template_loader.py`)
3. **API service** (`api/services/control_template_service.py`)
4. **API routes** (`api/routes/control_template_routes.py`)
5. **Frontend page** (`frontend/control/index.html`)

---

## Step 1: Create Template JSON Files (15 min)

### 1.1 Create Directory Structure

```powershell
# From project root
New-Item -ItemType Directory -Force -Path templates/control_strategies/variable_speed_sign
New-Item -ItemType Directory -Force -Path templates/control_strategies/dynamic_hard_shoulder
New-Item -ItemType Directory -Force -Path templates/control_strategies/toll_entrance_control
```

### 1.2 Create VSS Moderate Template

**File**: `templates/control_strategies/variable_speed_sign/vss_moderate.json`

```json
{
  "template_id": "vss_moderate",
  "template_name": "可变限速 - 中等控制",
  "description": "适用于高峰期的中等强度限速控制，限速值80-100 km/h，适合交通流量中等的高速路段。通过分时段调整限速，平滑车流，避免下游瓶颈堵塞。",
  "strategy_type": "VSS",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "array",
      "description": "受限速影响的路段列表，使用路段ID标识",
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
    },
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
    },
    {
      "parameter_name": "applicable_vehicle_types",
      "parameter_type": "array",
      "description": "受限速约束的车型列表，默认为空表示所有车型",
      "required": false,
      "default_value": [],
      "min_value": null,
      "max_value": null,
      "allowed_values": null,
      "unit": null
    }
  ],
  "version": "1.0",
  "created_at": "2025-10-19T00:00:00Z",
  "updated_at": "2025-10-19T00:00:00Z"
}
```

### 1.3 Create Remaining Templates

**Note**: Create 4 more templates following the same structure:
- `vss_strict.json` (speed_limit: 60-80 km/h)
- `dhs_peak_hours.json` (DHS strategy with opening_hours, closing_hours)
- `tec_truck_ban.json` (TEC strategy with control_mode="restrict", vehicle_type_restrictions)
- `tec_entrance_close.json` (TEC strategy with control_mode="close")

**Reference**: See `data-model.md` for full parameter schemas and `spec.md` Section "Strategy Type Parameter Examples" for details.

---

## Step 2: Implement TemplateLoader (20 min)

### 2.1 Create Pydantic Models

**File**: `api/models/control/entities/template.py`

```python
"""Control strategy template entities"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class StrategyType(str, Enum):
    """Supported traffic control strategy types"""
    VSS = "VSS"  # Variable Speed Signs
    DHS = "DHS"  # Dynamic Hard Shoulder
    TEC = "TEC"  # Toll Entrance Control

class ParameterSchema(BaseModel):
    """Schema for a configurable parameter"""
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
    """Traffic control strategy template"""
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
```

### 2.2 Create TemplateLoader Utility

**File**: `shared/control_tools/template_loader.py`

```python
"""Template loading and validation utilities"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pydantic import ValidationError

from api.models.control.entities.template import ControlTemplate, StrategyType

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates" / "control_strategies"
INDEX_FILE = TEMPLATES_DIR / "templates_index.json"

class TemplateLoader:
    """Load, validate, and manage strategy templates"""

    def __init__(self):
        self._templates: Dict[str, ControlTemplate] = {}
        self._index_generated = False

    def load_all_templates(self) -> Dict[str, ControlTemplate]:
        """Load all templates from templates directory"""
        if self._templates:
            return self._templates  # Return cached templates

        logger.info(f"Loading templates from {TEMPLATES_DIR}")

        for strategy_dir in TEMPLATES_DIR.iterdir():
            if not strategy_dir.is_dir() or strategy_dir.name.startswith('.'):
                continue

            for template_file in strategy_dir.glob("*.json"):
                if template_file.name == "templates_index.json":
                    continue

                template = self._load_template_file(template_file)
                if template:
                    self._templates[template.template_id] = template

        logger.info(f"Loaded {len(self._templates)} valid templates")
        return self._templates

    def _load_template_file(self, file_path: Path) -> Optional[ControlTemplate]:
        """Load and validate a single template file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            template = ControlTemplate(**data)
            logger.debug(f"Loaded template: {template.template_id}")
            return template

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Validation failed for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_template_by_id(self, template_id: str) -> Optional[ControlTemplate]:
        """Retrieve a template by ID"""
        if not self._templates:
            self.load_all_templates()
        return self._templates.get(template_id)

    def list_templates(self) -> List[ControlTemplate]:
        """Get list of all templates"""
        if not self._templates:
            self.load_all_templates()
        return list(self._templates.values())

    def generate_index(self) -> dict:
        """Generate templates index for fast lookup"""
        if not self._templates:
            self.load_all_templates()

        by_type = {}
        for template in self._templates.values():
            type_str = template.strategy_type.value
            by_type[type_str] = by_type.get(type_str, 0) + 1

        index = {
            "templates": [
                {
                    "template_id": t.template_id,
                    "template_name": t.template_name,
                    "strategy_type": t.strategy_type.value,
                    "description_preview": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                    "file_path": f"{t.strategy_type.value.lower()}/{t.template_id}.json"
                }
                for t in self._templates.values()
            ],
            "generated_at": datetime.now().isoformat(),
            "total_count": len(self._templates),
            "by_type": by_type
        }

        # Write index file
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info(f"Generated index with {len(self._templates)} templates")
        return index
```

---

## Step 3: Implement API Layer (15 min)

### 3.1 Create Service

**File**: `api/services/control_template_service.py`

```python
"""Control template management service"""
from typing import List, Optional
from shared.control_tools.template_loader import TemplateLoader
from api.models.control.entities.template import ControlTemplate

class ControlTemplateService:
    """Service for managing strategy templates"""

    def __init__(self):
        self.loader = TemplateLoader()

    def list_templates(self) -> dict:
        """List all available templates with summary"""
        return self.loader.generate_index()

    def get_template_by_id(self, template_id: str) -> Optional[dict]:
        """Get full template details by ID"""
        template = self.loader.get_template_by_id(template_id)
        if template:
            return template.dict()
        return None
```

### 3.2 Create Routes

**File**: `api/routes/control_template_routes.py`

```python
"""Control template API routes"""
from fastapi import APIRouter, HTTPException
from api.services.control_template_service import ControlTemplateService

router = APIRouter(prefix="/api/v1/control", tags=["control-templates"])

@router.get("/templates/")
async def list_templates():
    """List all available strategy templates"""
    service = ControlTemplateService()
    return service.list_templates()

@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get detailed information about a specific template"""
    service = ControlTemplateService()
    template = service.get_template_by_id(template_id)

    if not template:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "TEMPLATE_NOT_FOUND",
                "message": f"模板 '{template_id}' 未找到",
                "details": None
            }
        )

    return template
```

### 3.3 Register Routes in Main App

**File**: `api/main.py` (add this line)

```python
from api.routes import control_template_routes

# ... existing code ...

app.include_router(control_template_routes.router)
```

---

## Step 4: Create Frontend (20 min)

### 4.1 Create HTML Page

**File**: `frontend/control/index.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略模板管理</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>交通管控策略模板</h1>

        <div id="templateGrid" class="template-grid"></div>
    </div>

    <!-- Modal for template details -->
    <div id="templateModal" class="modal">
        <div class="modal-content">
            <span class="modal-close">&times;</span>
            <h2 id="modalTitle"></h2>
            <div id="modalBody"></div>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

### 4.2 Create JavaScript

**File**: `frontend/control/app.js`

```javascript
// Fetch and display templates
async function loadTemplates() {
    const response = await fetch('/api/v1/control/templates/');
    const data = await response.json();

    const grid = document.getElementById('templateGrid');
    grid.innerHTML = '';

    data.templates.forEach(template => {
        const card = createTemplateCard(template);
        grid.appendChild(card);
    });
}

function createTemplateCard(template) {
    const card = document.createElement('div');
    card.className = 'template-card';
    card.innerHTML = `
        <div class="card-header">
            <span class="strategy-type">${template.strategy_type}</span>
            <h3>${template.template_name}</h3>
        </div>
        <p class="card-description">${template.description_preview}</p>
    `;
    card.onclick = () => showTemplateDetail(template.template_id);
    return card;
}

async function showTemplateDetail(templateId) {
    const response = await fetch(`/api/v1/control/templates/${templateId}`);
    const template = await response.json();

    document.getElementById('modalTitle').textContent = template.template_name;
    document.getElementById('modalBody').innerHTML = renderTemplateDetail(template);
    document.getElementById('templateModal').style.display = 'block';
}

function renderTemplateDetail(template) {
    let html = `<p><strong>策略类型：</strong>${template.strategy_type}</p>`;
    html += `<p><strong>说明：</strong>${template.description}</p>`;
    html += `<h3>参数配置</h3><ul>`;

    template.parameters_schema.forEach(param => {
        html += `<li><strong>${param.parameter_name}</strong>: ${param.description}`;
        if (param.required) html += ' (必填)';
        if (param.default_value !== null) html += ` [默认: ${JSON.stringify(param.default_value)}]`;
        html += `</li>`;
    });

    html += `</ul>`;
    return html;
}

// Modal close
document.querySelector('.modal-close').onclick = () => {
    document.getElementById('templateModal').style.display = 'none';
};

// Load templates on page load
loadTemplates();
```

### 4.3 Create CSS

**File**: `frontend/control/styles.css`

```css
.template-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.template-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: box-shadow 0.2s;
}

.template-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.strategy-type {
    background: #007bff;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
}

.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.4);
}

.modal-content {
    background-color: #fff;
    margin: 5% auto;
    padding: 2rem;
    border-radius: 8px;
    width: 80%;
    max-width: 600px;
}

.modal-close {
    float: right;
    font-size: 1.5rem;
    cursor: pointer;
}
```

---

## Step 5: Test (10 min)

### 5.1 Start Server

```powershell
python api/main.py
```

### 5.2 Test API Endpoints

```powershell
# Test list endpoint
curl http://localhost:8000/api/v1/control/templates/

# Test detail endpoint
curl http://localhost:8000/api/v1/control/templates/vss_moderate
```

### 5.3 Test Frontend

Navigate to: `http://localhost:8000/control/index.html`

**Expected**:
- See 5 template cards
- Click card → modal opens with details
- Click X → modal closes

---

## Step 6: Write Tests (15 min)

### 6.1 Unit Test

**File**: `tests/unit/shared/test_template_loader.py`

```python
import pytest
from shared.control_tools.template_loader import TemplateLoader

def test_load_all_templates():
    loader = TemplateLoader()
    templates = loader.load_all_templates()
    assert len(templates) == 5  # Phase 1A has 5 templates

def test_get_template_by_id():
    loader = TemplateLoader()
    template = loader.get_template_by_id("vss_moderate")
    assert template is not None
    assert template.template_id == "vss_moderate"
    assert template.strategy_type.value == "VSS"

def test_generate_index():
    loader = TemplateLoader()
    index = loader.generate_index()
    assert index["total_count"] == 5
    assert index["by_type"]["VSS"] == 2
    assert index["by_type"]["DHS"] == 1
    assert index["by_type"]["TEC"] == 2
```

### 6.2 Integration Test

**File**: `tests/integration/api/test_control_template_routes.py`

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_list_templates():
    response = client.get("/api/v1/control/templates/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 5
    assert len(data["templates"]) == 5

def test_get_template_by_id():
    response = client.get("/api/v1/control/templates/vss_moderate")
    assert response.status_code == 200
    data = response.json()
    assert data["template_id"] == "vss_moderate"
    assert "parameters_schema" in data

def test_get_template_not_found():
    response = client.get("/api/v1/control/templates/invalid_id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
```

### 6.3 Run Tests

```powershell
pytest tests/unit/shared/test_template_loader.py -v
pytest tests/integration/api/test_control_template_routes.py -v
```

---

## Common Issues & Fixes

### Issue 1: Templates not loading
**Symptom**: API returns empty list
**Fix**: Check templates directory path in `template_loader.py`, verify JSON files exist

### Issue 2: Validation errors
**Symptom**: Template rejected at startup
**Fix**: Check JSON syntax, required fields, parameter types match schema

### Issue 3: Modal not opening
**Symptom**: Click card, nothing happens
**Fix**: Check browser console for JS errors, verify fetch URL is correct

### Issue 4: CORS errors
**Symptom**: Frontend can't fetch API
**Fix**: Add CORS middleware in `api/main.py`

---

## Next Steps

1. **Phase 1B**: Implement edge selector (database-driven road segment selection)
2. **Phase 1C**: Implement strategy CRUD (create/edit/delete strategies based on templates)
3. **Add more templates**: Follow the JSON structure to add new template variants

---

## Reference

- **Spec**: `spec.md` - Full feature specification
- **Data Model**: `data-model.md` - Entity definitions
- **API Contract**: `contracts/control-templates-api.yaml` - OpenAPI spec
- **Research**: `research.md` - Technical decisions
