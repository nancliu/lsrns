# Quick Start: Phase 0 基础设施准备

**Feature**: 交通管控仿真 - Phase 0 Infrastructure
**Target Audience**: Backend/Frontend developers
**Estimated Time**: 2-3 hours
**Prerequisites**: Python 3.10+, Git, Text editor

## Overview

Phase 0 establishes the foundation for the traffic control simulation optimization module. You'll create:
- ✅ 4 data models (ControlTemplate, Strategy, Plan, BatchSimulation)
- ✅ 7 directory structures
- ✅ API skeleton (empty routes + services)
- ✅ Frontend skeleton (navigation + placeholder pages)
- ✅ Database connection test script

**Important**: Phase 0 creates **scaffolding only**. No business logic implementation yet.

---

## Step 1: Create Directory Structure (5 minutes)

### Windows (PowerShell)

```powershell
# Navigate to project root
cd D:\projects\OD_SIM

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

### Linux/Mac (bash)

```bash
# Navigate to project root
cd /path/to/OD_SIM

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

### Verification

```powershell
# Check directories exist
ls templates\control_strategies
ls control_data
ls api\models\control
ls api\services\control
ls shared\control_tools
ls frontend\control
```

Expected output: All directories should list successfully (may show `.gitkeep` file).

---

## Step 2: Define Enums (10 minutes)

### File: `api/models/enums.py`

Add the following enums to the existing `enums.py` file (append at the end):

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

### Verification

```python
# Test import
python -c "from api.models.enums import StrategyType, BatchSimulationStatus; print('✅ Enums imported successfully')"
```

---

## Step 3: Create Data Models (30 minutes)

### 3.1 Create `__init__.py` files

```powershell
# Create empty __init__.py files
New-Item api\models\control\__init__.py -ItemType File
New-Item api\models\control\entities\__init__.py -ItemType File
```

### 3.2 File: `api/models/control/entities/template.py`

<details>
<summary>Click to expand full code</summary>

```python
"""
管控策略模板实体模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ...enums import StrategyType


class ControlTemplate(BaseModel):
    """管控策略模板模型"""

    template_id: str = Field(
        ...,
        description="模板唯一标识符",
        examples=["vss_moderate_001", "dhs_peak_hours_001"]
    )

    template_name: str = Field(
        ...,
        description="模板名称（用户可读）",
        examples=["可变限速-中等强度", "动态硬路肩-高峰时段"]
    )

    strategy_type: StrategyType = Field(
        ...,
        description="管控策略类型（VSS/DHS/TEC）"
    )

    parameters_schema: Dict[str, Any] = Field(
        ...,
        description="参数JSON Schema定义（类型、范围、默认值）"
    )

    description: Optional[str] = Field(
        None,
        description="模板详细说明（使用场景、注意事项）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "vss_moderate_001",
                "template_name": "可变限速-中等强度",
                "strategy_type": "vss",
                "parameters_schema": {
                    "speed_limit": {
                        "type": "integer",
                        "minimum": 40,
                        "maximum": 120,
                        "default": 80
                    }
                },
                "description": "适用于高峰时段流量疏导"
            }
        }
```
</details>

### 3.3 File: `api/models/control/entities/strategy.py`

<details>
<summary>Click to expand full code</summary>

```python
"""
管控策略实例实体模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime


class Strategy(BaseModel):
    """管控策略实例模型"""

    strategy_id: str = Field(..., description="策略唯一标识符")
    strategy_name: str = Field(..., description="策略名称（用户自定义）")
    template_id: str = Field(..., description="关联的模板ID（外键）")
    parameters: Dict[str, Any] = Field(..., description="参数值字典")
    target_edges: List[str] = Field(..., description="目标路段ID列表（SUMO edge_id）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间戳")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strategy_20251019_001",
                "strategy_name": "G4202分流点限速80",
                "template_id": "vss_moderate_001",
                "parameters": {"speed_limit": 80, "active_hours": [7, 8, 9]},
                "target_edges": ["edge_e789012", "edge_e789013"],
                "created_at": "2025-10-19T10:30:00",
                "updated_at": "2025-10-19T10:30:00"
            }
        }
```
</details>

### 3.4 File: `api/models/control/entities/plan.py`

<details>
<summary>Click to expand full code</summary>

```python
"""
控制方案实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Plan(BaseModel):
    """控制方案模型"""

    plan_id: str = Field(..., description="方案唯一标识符")
    plan_name: str = Field(..., description="方案名称（用户自定义）")
    description: Optional[str] = Field(None, description="方案详细描述")
    strategy_ids: List[str] = Field(default_factory=list, description="包含的策略ID列表")
    additional_file_path: Optional[str] = Field(None, description="生成的SUMO Additional文件路径")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间戳")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan_20251019_001",
                "plan_name": "高峰时段综合管控方案A",
                "description": "结合限速和入口控制",
                "strategy_ids": ["strategy_001", "strategy_002"],
                "additional_file_path": "control_data/plans/plan_20251019_001/control.add.xml",
                "created_at": "2025-10-19T11:00:00",
                "updated_at": "2025-10-19T11:00:00"
            }
        }
```
</details>

### 3.5 File: `api/models/control/entities/batch_simulation.py`

<details>
<summary>Click to expand full code</summary>

```python
"""
批量仿真任务实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
from ...enums import BatchSimulationStatus


class BatchSimulation(BaseModel):
    """批量仿真任务模型"""

    batch_id: str = Field(..., description="批次唯一标识符")
    batch_name: str = Field(..., description="批次名称（用户自定义）")
    case_id: str = Field(..., description="关联的案例ID（外键）")
    plan_ids: List[str] = Field(..., description="待测试的方案ID列表", min_length=1)
    status: BatchSimulationStatus = Field(
        default=BatchSimulationStatus.PENDING,
        description="批次状态"
    )
    progress: Dict[str, int] = Field(
        default_factory=lambda: {"total": 0, "completed": 0, "failed": 0},
        description="进度统计"
    )
    simulation_ids: List[str] = Field(default_factory=list, description="生成的仿真ID列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间戳")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251019_001",
                "batch_name": "高峰时段方案对比测试",
                "case_id": "case_20251015_baseline",
                "plan_ids": ["plan_baseline", "plan_001"],
                "status": "running",
                "progress": {"total": 2, "completed": 1, "failed": 0},
                "simulation_ids": ["sim_001_plan_baseline"],
                "created_at": "2025-10-19T14:00:00",
                "updated_at": "2025-10-19T14:15:00"
            }
        }
```
</details>

### 3.6 Update `api/models/control/entities/__init__.py`

```python
"""
控制模块实体模型导出
"""

from .template import ControlTemplate
from .strategy import Strategy
from .plan import Plan
from .batch_simulation import BatchSimulation

__all__ = [
    "ControlTemplate",
    "Strategy",
    "Plan",
    "BatchSimulation"
]
```

### 3.7 Update `api/models/control/__init__.py`

```python
"""
控制模块数据模型导出
"""

from .entities import ControlTemplate, Strategy, Plan, BatchSimulation

__all__ = [
    "ControlTemplate",
    "Strategy",
    "Plan",
    "BatchSimulation"
]
```

### Verification

```python
# Test model imports
python -c "from api.models.control import ControlTemplate, Strategy, Plan, BatchSimulation; print('✅ All models imported')"

# Test type checking (optional, requires mypy)
mypy api/models/control/
```

---

## Step 4: Create API Routes (20 minutes)

### File: `api/routes/control_strategy_routes.py`

```python
"""
交通管控策略路由
"""

from fastapi import APIRouter
from typing import List, Dict, Any

# 创建控制策略路由器
router = APIRouter()


# ==================== 策略模板 Templates ====================
@router.get("/templates/", response_model=List[Dict[str, Any]])
async def list_control_templates():
    """获取所有策略模板列表 (Phase 0 stub)"""
    return []


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_control_template(template_id: str):
    """获取指定模板详情 (Phase 0 stub)"""
    return {}


# ==================== 控制策略 Strategies ====================
@router.get("/strategies/", response_model=Dict[str, Any])
async def list_strategies():
    """获取所有策略列表 (Phase 0 stub)"""
    return {"total": 0, "items": []}


@router.post("/strategies/", status_code=501)
async def create_strategy():
    """创建新策略 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.get("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy(strategy_id: str):
    """获取策略详情 (Phase 0 stub)"""
    return {}


@router.put("/strategies/{strategy_id}", status_code=501)
async def update_strategy(strategy_id: str):
    """更新策略 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.delete("/strategies/{strategy_id}", status_code=501)
async def delete_strategy(strategy_id: str):
    """删除策略 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


# ==================== 控制方案 Plans ====================
@router.get("/plans/", response_model=List[Dict[str, Any]])
async def list_plans():
    """获取所有方案列表 (Phase 0 stub)"""
    return []


@router.post("/plans/", status_code=501)
async def create_plan():
    """创建新方案 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.get("/plans/{plan_id}", response_model=Dict[str, Any])
async def get_plan(plan_id: str):
    """获取方案详情 (Phase 0 stub)"""
    return {}


# ==================== 批量仿真 Batch Simulations ====================
@router.get("/batch_simulations/", response_model=List[Dict[str, Any]])
async def list_batch_simulations():
    """获取批量仿真任务列表 (Phase 0 stub)"""
    return []


@router.post("/batch_simulations/", status_code=501)
async def create_batch_simulation():
    """创建批量仿真任务 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.get("/batch_simulations/{batch_id}", response_model=Dict[str, Any])
async def get_batch_simulation(batch_id: str):
    """获取批量仿真任务详情 (Phase 0 stub)"""
    return {}
```

### Register routes in `api/routes/__init__.py`

Add the following import and registration (append to existing file):

```python
# Add import at top
from .control_strategy_routes import router as control_router

# Add registration after existing routers
router.include_router(control_router, prefix="/control", tags=["交通管控"])
```

### Verification

```bash
# Start API server
python api/main.py

# Test routes (in another terminal)
curl http://localhost:8000/api/v1/control/strategies/
# Expected: {"total": 0, "items": []}

curl http://localhost:8000/api/v1/control/templates/
# Expected: []

# Check API docs
# Visit: http://localhost:8000/docs
# Look for "交通管控" tag with control endpoints
```

---

## Step 5: Create API Service (10 minutes)

### File: `api/services/control/__init__.py`

```python
"""
控制模块服务导出
"""

from .control_strategy_service import ControlStrategyService

__all__ = ["ControlStrategyService"]
```

### File: `api/services/control/control_strategy_service.py`

```python
"""
控制策略服务 (Phase 0 stub)
"""

from typing import List, Dict, Any


class ControlStrategyService:
    """控制策略业务逻辑服务 (Phase 0: empty methods)"""

    async def list_templates(self) -> List[Dict[str, Any]]:
        """获取模板列表 (Phase 0: empty list)"""
        return []

    async def list_strategies(self) -> Dict[str, Any]:
        """获取策略列表 (Phase 0: empty list)"""
        return {"total": 0, "items": []}

    async def list_plans(self) -> List[Dict[str, Any]]:
        """获取方案列表 (Phase 0: empty list)"""
        return []

    async def list_batch_simulations(self) -> List[Dict[str, Any]]:
        """获取批量仿真任务列表 (Phase 0: empty list)"""
        return []
```

### Verification

```python
# Test service import
python -c "from api.services.control import ControlStrategyService; svc = ControlStrategyService(); print('✅ Service created')"
```

---

## Step 6: Create Frontend Skeleton (30 minutes)

### File: `frontend/control/index.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>交通管控仿真优化系统</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>交通管控仿真优化系统</h1>
        <p>Traffic Control Simulation & Optimization</p>
    </header>

    <nav class="main-nav">
        <button class="nav-btn active" data-view="strategies">策略管理</button>
        <button class="nav-btn" data-view="plans">方案管理</button>
        <button class="nav-btn" data-view="batch">批量仿真</button>
        <button class="nav-btn" data-view="optimization">优化分析</button>
    </nav>

    <main id="content-area">
        <!-- Dynamic content area -->
        <section id="view-strategies" class="view-content active">
            <h2>策略管理 (Strategy Management)</h2>
            <p class="placeholder">Phase 0: 策略管理功能开发中...</p>
            <p>未来功能：创建、编辑、删除控制策略（基于模板）</p>
        </section>

        <section id="view-plans" class="view-content">
            <h2>方案管理 (Plan Management)</h2>
            <p class="placeholder">Phase 0: 方案管理功能开发中...</p>
            <p>未来功能：组建方案、生成Additional文件</p>
        </section>

        <section id="view-batch" class="view-content">
            <h2>批量仿真 (Batch Simulation)</h2>
            <p class="placeholder">Phase 0: 批量仿真功能开发中...</p>
            <p>未来功能：并行运行多个方案、进度监控</p>
        </section>

        <section id="view-optimization" class="view-content">
            <h2>优化分析 (Optimization Analysis)</h2>
            <p class="placeholder">Phase 0: 优化分析功能开发中...</p>
            <p>未来功能：指标计算、方案排序、可视化对比</p>
        </section>
    </main>

    <footer>
        <p>OD数据处理与仿真系统 - 交通管控优化模块 | Phase 0 基础设施</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
```

### File: `frontend/control/styles.css`

```css
/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Microsoft YaHei', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

/* Header */
header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

header p {
    font-size: 1rem;
    opacity: 0.9;
}

/* Navigation */
.main-nav {
    background: white;
    padding: 1rem 2rem;
    display: flex;
    gap: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-btn {
    padding: 0.8rem 1.5rem;
    border: 2px solid #667eea;
    background: white;
    color: #667eea;
    font-size: 1rem;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.3s ease;
}

.nav-btn:hover {
    background: #f0f3ff;
}

.nav-btn.active {
    background: #667eea;
    color: white;
}

/* Main Content */
main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
}

.view-content {
    display: none;
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    min-height: 400px;
}

.view-content.active {
    display: block;
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.view-content h2 {
    color: #667eea;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #667eea;
    padding-bottom: 0.5rem;
}

.placeholder {
    font-size: 1.2rem;
    color: #999;
    padding: 2rem;
    text-align: center;
    background: #f9f9f9;
    border-radius: 4px;
    margin-bottom: 1rem;
}

/* Footer */
footer {
    text-align: center;
    padding: 2rem;
    color: #666;
    margin-top: 4rem;
}

/* Responsive */
@media (max-width: 768px) {
    .main-nav {
        flex-direction: column;
    }

    .nav-btn {
        width: 100%;
    }
}
```

### File: `frontend/control/app.js`

```javascript
// 导航切换逻辑
document.addEventListener('DOMContentLoaded', () => {
    const navButtons = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-content');

    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const viewName = button.getAttribute('data-view');

            // 更新按钮激活状态
            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // 更新视图显示
            viewSections.forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(`view-${viewName}`).classList.add('active');

            // 保存当前视图到 sessionStorage (页面刷新保持状态)
            sessionStorage.setItem('activeView', viewName);
        });
    });

    // 页面加载时恢复上次激活的视图
    const savedView = sessionStorage.getItem('activeView');
    if (savedView) {
        const savedButton = document.querySelector(`[data-view="${savedView}"]`);
        if (savedButton) {
            savedButton.click();
        }
    }
});
```

### Verification

```bash
# Start API server (if not already running)
python api/main.py

# Open browser
# Visit: http://localhost:8000/control/index.html

# Expected:
# ✅ Page loads with header, navigation, and placeholder content
# ✅ Clicking navigation buttons switches views
# ✅ Page refresh preserves active view
# ✅ No JavaScript errors in console
```

---

## Step 7: Database Connection Test (15 minutes)

### File: `shared/data_access/test_dim_schema.py`

```python
"""
数据库连接测试脚本 - 验证dim schema访问
"""

import logging
from .connection import open_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_dim_schema_access():
    """测试dim schema访问权限和表查询"""

    print("=" * 60)
    print("数据库连接测试 - dim schema")
    print("=" * 60)

    try:
        # 建立数据库连接
        print("\n[1/4] 尝试连接数据库...")
        conn = open_db_connection()
        print("✅ 数据库连接成功")

        cursor = conn.cursor()

        # 测试1: 查询 dim.sim_network_edges
        print("\n[2/4] 查询 dim.sim_network_edges...")
        cursor.execute("SELECT COUNT(*) FROM dim.sim_network_edges")
        edge_count = cursor.fetchone()[0]
        print(f"✅ dim.sim_network_edges 表记录数: {edge_count}")

        # 测试2: 查询 dim.multiscale_node_units
        print("\n[3/4] 查询 dim.multiscale_node_units...")
        cursor.execute("SELECT COUNT(*) FROM dim.multiscale_node_units")
        node_count = cursor.fetchone()[0]
        print(f"✅ dim.multiscale_node_units 表记录数: {node_count}")

        # 测试3: 查询 dim.point_gantry
        print("\n[4/4] 查询 dim.point_gantry...")
        cursor.execute("SELECT COUNT(*) FROM dim.point_gantry")
        gantry_count = cursor.fetchone()[0]
        print(f"✅ dim.point_gantry 表记录数: {gantry_count}")

        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！dim schema访问正常")
        print("=" * 60)
        print(f"路段总数: {edge_count}")
        print(f"节点单元总数: {node_count}")
        print(f"门架点总数: {gantry_count}")
        print("=" * 60)

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        print("\n诊断建议:")
        print("1. 检查 .env 文件是否配置正确 (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)")
        print("2. 检查数据库服务器是否可访问 (ping DB_HOST)")
        print("3. 检查数据库凭据是否正确")
        print("4. 检查 dim schema 是否存在")
        print("=" * 60)

        return False


if __name__ == "__main__":
    test_dim_schema_access()
```

### Verification

```bash
# Run database test
python shared/data_access/test_dim_schema.py

# Expected output (success):
# ============================================================
# 数据库连接测试 - dim schema
# ============================================================
#
# [1/4] 尝试连接数据库...
# ✅ 数据库连接成功
#
# [2/4] 查询 dim.sim_network_edges...
# ✅ dim.sim_network_edges 表记录数: 15234
#
# [3/4] 查询 dim.multiscale_node_units...
# ✅ dim.multiscale_node_units 表记录数: 856
#
# [4/4] 查询 dim.point_gantry...
# ✅ dim.point_gantry 表记录数: 428
#
# ============================================================
# ✅ 所有测试通过！dim schema访问正常
# ============================================================

# If connection fails, check:
# 1. .env file exists and has correct credentials
# 2. Database server is reachable
# 3. dim schema tables exist
```

---

## Step 8: Verification Checklist

Run through this checklist to ensure Phase 0 is complete:

### Directory Structure
- [ ] `templates/control_strategies/` exists
- [ ] `control_data/strategies/` exists
- [ ] `control_data/plans/` exists
- [ ] `control_data/optimizations/` exists
- [ ] `api/models/control/entities/` exists
- [ ] `api/services/control/` exists
- [ ] `shared/control_tools/` exists
- [ ] `frontend/control/` exists

### Data Models
- [ ] `api/models/enums.py` contains `StrategyType` and `BatchSimulationStatus`
- [ ] `api/models/control/entities/template.py` defines `ControlTemplate`
- [ ] `api/models/control/entities/strategy.py` defines `Strategy`
- [ ] `api/models/control/entities/plan.py` defines `Plan`
- [ ] `api/models/control/entities/batch_simulation.py` defines `BatchSimulation`
- [ ] All models can be imported: `from api.models.control import ControlTemplate, Strategy, Plan, BatchSimulation`
- [ ] Type checking passes: `mypy api/models/control/` (0 errors)

### API Routes
- [ ] `api/routes/control_strategy_routes.py` exists with all endpoints
- [ ] Routes registered in `api/routes/__init__.py`
- [ ] API docs show "交通管控" tag at http://localhost:8000/docs
- [ ] `GET /api/v1/control/strategies/` returns `{"total": 0, "items": []}`
- [ ] `GET /api/v1/control/templates/` returns `[]`
- [ ] `GET /api/v1/control/plans/` returns `[]`
- [ ] `GET /api/v1/control/batch_simulations/` returns `[]`

### Frontend
- [ ] `frontend/control/index.html` loads at http://localhost:8000/control/index.html
- [ ] Navigation buttons switch views correctly
- [ ] Page refresh preserves active view (sessionStorage)
- [ ] No JavaScript errors in browser console
- [ ] All 4 views show placeholder text

### Database
- [ ] `shared/data_access/test_dim_schema.py` runs successfully
- [ ] Test script reports >0 records for all 3 tables
- [ ] No connection errors

---

## Next Steps

Phase 0 is complete! You've built the foundation. Next phases:

- **Phase 1A** (1 week): Strategy template system (actual templates, parser)
- **Phase 1B** (2 weeks): Database-driven edge selector (query dim schema, frontend filters)
- **Phase 1C** (2 weeks): Strategy CRUD (create/update/delete strategies)
- **Phase 2** (2 weeks): Plan management (Additional file generation)
- **Phase 3** (3 weeks): Batch simulation (parallel execution, progress monitoring)
- **Phase 4** (2 weeks): Optimization analysis (metric calculation, ranking)

**Recommended Command**:
```bash
# Generate task breakdown for implementation
/speckit.tasks

# Start implementation
/speckit.implement
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'api'"

**Solution**: Ensure you're running from project root (`D:\projects\OD_SIM`), not from subdirectory.

### Issue: "Database connection failed"

**Solution**:
1. Check `.env` file exists in project root
2. Verify credentials: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
3. Test connection manually: `psql -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -d <DB_NAME>`

### Issue: "Frontend page not loading"

**Solution**:
1. Verify API server is running: `python api/main.py`
2. Check main.py has `app.mount("/", StaticFiles(directory="frontend"))` (should already exist)
3. Clear browser cache (Ctrl+F5)

### Issue: "Type checking errors with mypy"

**Solution**:
1. Install mypy: `pip install mypy`
2. Check `datetime.now` vs `datetime.now()` in Field defaults
3. Ensure all imports are correct

---

**Completion Time**: Approximately 2-3 hours for a single developer following this guide.

**Questions?** Refer to:
- [spec.md](spec.md) - Feature requirements
- [data-model.md](data-model.md) - Detailed model specifications
- [contracts/openapi-control-routes.yaml](contracts/openapi-control-routes.yaml) - API contract
