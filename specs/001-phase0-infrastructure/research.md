# Research Document: Phase 0 Infrastructure Decisions

**Feature**: 交通管控仿真 - Phase 0 基础设施准备
**Date**: 2025-10-19
**Status**: Completed

## Research Tasks & Findings

### 1. Enum Location Decision

**Question**: Where to define StrategyType and BatchSimulationStatus enums?

**Options Evaluated**:
- **Option A**: Extend existing `api/models/enums.py` (centralized)
- **Option B**: Create new `api/models/control/enums.py` (isolated)

**Investigation**:
Examined `api/models/enums.py` which contains:
```python
class SimulationType(str, Enum):
    MICROSCOPIC = "microscopic"
    MESOSCOPIC = "mesoscopic"

class CaseStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    # ... more states

class AnalysisType(str, Enum):
    ACCURACY = "accuracy"
    MECHANISM = "mechanism"
    # ... more types
```

Pattern: Centralized enum file with domain-specific enums inheriting from `str, Enum` for FastAPI JSON serialization.

**Decision**: **Option A - Extend existing `api/models/enums.py`**

**Rationale**:
1. **Consistency**: Follows existing project pattern of centralized enums
2. **Import Simplicity**: Single import location `from api.models.enums import StrategyType, BatchSimulationStatus`
3. **No New Files**: Minimizes file proliferation in Phase 0
4. **Cross-Module Reuse**: Enums are used across models, routes, and services - centralized location avoids circular imports
5. **Discoverability**: Developers know to check enums.py for all system enumerations

**Implementation**:
Add to `api/models/enums.py`:
```python
class StrategyType(str, Enum):
    """管控策略类型枚举"""
    VSS = "vss"  # Variable Speed Sign (可变限速)
    DHS = "dhs"  # Dynamic Hard Shoulder (动态硬路肩)
    TEC = "tec"  # Toll Entrance Control (入口匝道控制)

class BatchSimulationStatus(str, Enum):
    """批量仿真状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

**Alternatives Considered**:
- Option B rejected: Creates unnecessary directory depth for 2 enums; breaks existing pattern

---

### 2. Database Query Best Practices

**Question**: How to structure read-only queries to dim schema for edge selection?

**Investigation**:
Examined `shared/data_access/gantry_loader.py` patterns:
- **Class-based loader**: `GantryDataLoader` with connection management
- **Raw SQL**: Uses psycopg2 cursor with parameterized queries
- **Result format**: Returns pandas DataFrame for data processing
- **Connection reuse**: Stores connection in instance variable `_conn`
- **Error handling**: Logs errors, returns empty DataFrame on failure

**Decision**: **Follow GantryDataLoader pattern for dim schema queries**

**Rationale**:
1. **Consistency**: Matches existing data access layer architecture
2. **Proven Pattern**: GantryDataLoader successfully handles production queries
3. **No New Dependencies**: Uses existing psycopg2 (no SQLAlchemy/ORM needed)
4. **Performance**: Raw SQL optimal for read-only analytical queries
5. **DataFrame Output**: Natural fit for road network data processing

**Implementation Plan** (Phase 1B):
Create `shared/data_access/edge_query.py`:
```python
class EdgeQueryLoader:
    """路段查询加载器：从dim schema查询路网数据"""

    def __init__(self):
        self._conn = None

    def _connect(self):
        # Reuse connection.py pattern

    def query_edges_with_filters(
        self,
        route_codes: List[str] = None,
        node_types: List[str] = None,
        # ... more filters
    ) -> pd.DataFrame:
        """查询dim.sim_network_edges with filters"""
        # Raw SQL query to dim schema
```

**Best Practices Applied**:
- ✅ Parameterized queries (SQL injection prevention)
- ✅ Connection pooling via instance reuse
- ✅ Logging for debugging
- ✅ Graceful error handling (empty DataFrame on failure)
- ✅ Type hints for query parameters

**Alternatives Considered**:
- SQLAlchemy ORM: Rejected - overhead for read-only queries
- Query builder library: Rejected - raw SQL more transparent for complex joins

---

### 3. Empty Route Response Format

**Question**: What data structure should stub routes return in Phase 0?

**Investigation**:
Examined `api/routes/template_routes.py`:
```python
@router.get("/templates/taz", response_model=List[TemplateInfo])
@handle_service_errors
async def get_taz_templates():
    """获取TAZ模板列表"""
    return await get_taz_templates_service()
```

Pattern: Typed responses with Pydantic response_model, service functions return data structures matching the model.

**Decision**: **Return empty list `[]` for list endpoints, empty dict `{}` for detail endpoints**

**Rationale**:
1. **Type Safety**: Empty list matches `response_model=List[...]` type
2. **Valid JSON**: `[]` and `{}` are valid JSON responses
3. **Client Compatibility**: Frontend can iterate empty list without errors
4. **FastAPI Validation**: Passes Pydantic validation (empty list is valid List)
5. **Semantic Clarity**: Empty list means "no data yet", not "error"

**Implementation**:
Phase 0 stub routes:
```python
@router.get("/strategies/", response_model=List[dict])
async def list_strategies():
    """获取策略列表 (Phase 0 stub)"""
    return []  # Empty list - no strategies yet

@router.get("/plans/", response_model=List[dict])
async def list_plans():
    """获取方案列表 (Phase 0 stub)"""
    return []  # Empty list - no plans yet
```

Phase 0 service:
```python
class ControlStrategyService:
    async def list_strategies(self):
        """Phase 0: Return empty list"""
        return []
```

**Alternatives Considered**:
- Return 404 Not Found: Rejected - implies endpoint doesn't exist
- Return null: Rejected - type mismatch with List response_model
- Raise NotImplementedError: Rejected - causes 500 error, not appropriate for scaffolding

---

### 4. Frontend Asset Loading

**Question**: How to ensure `frontend/control/` is accessible via static file mount?

**Investigation**:
Examined `api/main.py`:
```python
# Mount static files
app.mount("/cases", StaticFiles(directory="cases", html=True), name="cases")
app.mount("/templates", StaticFiles(directory="templates", html=True), name="templates")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

**Finding**: FastAPI's `StaticFiles` with `directory="frontend"` serves ALL subdirectories recursively.

**Decision**: **No configuration changes needed - existing mount covers `frontend/control/`**

**Verification**:
- URL pattern: `http://localhost:8000/control/index.html`
- Maps to file: `frontend/control/index.html`
- StaticFiles directory mount: `/` → `frontend/` (includes all subdirectories)

**Rationale**:
1. **Zero Changes**: No modifications to main.py required
2. **Existing Pattern**: Same mechanism serves `frontend/index.html` currently
3. **Directory Transparency**: StaticFiles recursively serves subdirectories by default
4. **URL Mapping**: `/control/index.html` naturally maps to `frontend/control/index.html`

**Implementation**:
Simply create files in `frontend/control/` - no server config needed.

**Alternatives Considered**:
- Dedicated mount point: Rejected - unnecessary complexity, existing mount works
- Nginx reverse proxy: Rejected - not needed for development/deployment

---

### 5. Directory Creation Approach

**Question**: Script-based or manual directory creation?

**Options Evaluated**:
- **Option A**: PowerShell script (`.ps1` for Windows)
- **Option B**: Python script (`create_dirs.py`)
- **Option C**: Manual creation with documentation

**Investigation**:
- Searched for existing automation: Found `start_api.ps1` (startup script only)
- Project has `.gitkeep` files in existing directories (manual creation pattern)
- No existing directory scaffolding scripts in project

**Decision**: **Option C - Manual creation with `.gitkeep` files and documentation**

**Rationale**:
1. **Project Pattern**: Existing directories (cases/, templates/) created manually
2. **One-Time Task**: Only 7 directories to create - automation overhead not justified
3. **Cross-Platform**: Manual `mkdir` works on Windows/Linux/Mac
4. **Git Tracking**: Empty directories tracked via `.gitkeep` files
5. **Transparency**: Developers see exactly what's created

**Implementation**:
Provide bash/PowerShell commands in `quickstart.md`:

**Windows (PowerShell)**:
```powershell
# Create directory structure
mkdir templates\control_strategies
mkdir control_data\strategies
mkdir control_data\plans
mkdir control_data\optimizations
mkdir api\models\control\entities
mkdir api\services\control
mkdir shared\control_tools
mkdir frontend\control

# Create .gitkeep for empty directories
New-Item templates\control_strategies\.gitkeep -ItemType File
New-Item control_data\strategies\.gitkeep -ItemType File
New-Item control_data\plans\.gitkeep -ItemType File
New-Item control_data\optimizations\.gitkeep -ItemType File
```

**Linux/Mac (bash)**:
```bash
# Create directory structure
mkdir -p templates/control_strategies
mkdir -p control_data/{strategies,plans,optimizations}
mkdir -p api/models/control/entities
mkdir -p api/services/control
mkdir -p shared/control_tools
mkdir -p frontend/control

# Create .gitkeep
touch templates/control_strategies/.gitkeep
touch control_data/{strategies,plans,optimizations}/.gitkeep
```

**Alternatives Considered**:
- Option A (PowerShell): Rejected - adds script maintenance burden, cross-platform issues
- Option B (Python): Rejected - overkill for 7 directories

---

## Technology Stack Summary

Based on research findings, Phase 0 will use:

| Component | Technology | Decision Basis |
|-----------|-----------|----------------|
| **Data Models** | Pydantic 2.0+ BaseModel | Existing project standard |
| **Enums** | Python Enum (str, Enum) in centralized enums.py | Matches existing pattern |
| **API Routes** | FastAPI router with typed responses | Existing route pattern |
| **Database Access** | psycopg2 + raw SQL (read-only) | GantryDataLoader pattern |
| **Frontend** | Native HTML/CSS/JavaScript | Project standard (no React/Vue) |
| **Static Serving** | FastAPI StaticFiles | Existing main.py configuration |
| **Directory Creation** | Manual mkdir + .gitkeep | Project convention |
| **Testing** | pytest (unit) + FastAPI TestClient (integration) | Project standard |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Database connection failure to dim schema | Medium | High | Create test script early (FR-024); verify .env config |
| Enum naming conflicts | Low | Low | Use descriptive prefixes (StrategyType not just Type) |
| Frontend route conflicts | Low | Medium | Use dedicated /control/* prefix |
| Directory creation errors (permissions) | Low | Medium | Document Windows admin rights requirement if needed |

---

## Next Steps

With research complete, proceed to **Phase 1: Design & Contracts**:
1. Create `data-model.md` - detailed Pydantic model definitions
2. Create `contracts/openapi-control-routes.yaml` - API contract specifications
3. Create `quickstart.md` - developer setup guide
4. Update agent context files

All NEEDS CLARIFICATION markers from Technical Context are now resolved.

**Status**: ✅ Research complete - ready for Phase 1 design
