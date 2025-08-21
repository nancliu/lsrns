# 新架构API指南

## 📋 概述

本文档介绍重构完成后的OD数据处理与仿真系统API架构。新架构采用完全模块化设计，按业务领域组织API端点，提供更好的开发体验和更清晰的API结构。

## 🎯 新架构特点

### 1. 业务分组
- **数据处理组** - OD数据处理相关API
- **仿真管理组** - 仿真运行和管理API
- **案例管理组** - 案例CRUD操作API
- **分析结果组** - 结果分析和查看API
- **模板管理组** - 模板资源管理API
- **文件管理组** - 文件操作相关API

### 2. 模块化架构
系统采用完全模块化的架构设计：

#### 推荐访问方式
```
POST /api/v1/data/process_od_data/
GET /api/v1/case/list_cases/
POST /api/v1/simulation/run_simulation/
```

#### 架构层次
- **API层** (`api/`) - 专注于请求/响应处理和业务协调
- **共享层** (`shared/`) - 包含核心业务逻辑、算法和数据访问

## 🌐 API端点详细说明

### 数据处理组 (`/api/v1/data/`)

#### 处理OD数据
```
POST /api/v1/data/process_od_data/
```

**请求体示例:**
```json
{
  "start_time": "2025/07/21 08:00:00",
  "end_time": "2025/07/21 09:00:00",
  "schemas_name": "dwd",
  "interval_minutes": 5,
  "taz_file": "templates/taz_files/TAZ_5_validated.add.xml",
  "net_file": "templates/network_files/sichuan202503v6.net.xml",
  "case_name": "测试案例",
  "description": "案例描述",
  "output_summary": true,
  "output_tripinfo": true
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "OD数据处理成功",
  "data": {
    "case_id": "case_20250119_143000",
    "status": "completed",
    "od_file": "cases/case_20250119_143000/config/od_data.xml",
    "route_file": "cases/case_20250119_143000/config/routes.xml",
    "total_records": 1250,
    "od_pairs": 45
  }
}
```

### 仿真管理组 (`/api/v1/simulation/`)

#### 运行仿真
```
POST /api/v1/simulation/run_simulation/
```

**请求体示例:**
```json
{
  "case_id": "case_20250119_143000",
  "gui": false,
  "simulation_type": "microscopic",
  "simulation_name": "基线仿真",
  "simulation_description": "基线场景仿真",
  "simulation_params": {
    "output_vehroute": false,
    "output_fcd": false
  },
  "expected_duration": 3600
}
```

#### 获取仿真进度
```
GET /api/v1/simulation/simulation_progress/{case_id}
```

**响应示例:**
```json
{
  "success": true,
  "message": "获取仿真进度成功",
  "data": {
    "case_id": "case_20250119_143000",
    "simulation_id": "sim_20250119_143000",
    "status": "running",
    "progress": 65,
    "elapsed_time": 2340,
    "estimated_remaining": 1260
  }
}
```

#### 停止仿真
```
POST /api/v1/simulation/stop_simulation/
```

**请求体示例:**
```json
{
  "case_id": "case_20250119_143000",
  "simulation_id": "sim_20250119_143000"
}
```

### 案例管理组 (`/api/v1/case/`)

#### 列出所有案例
```
GET /api/v1/case/list_cases/
```

**查询参数:**
- `status` (可选): 案例状态筛选
- `created_after` (可选): 创建时间筛选
- `limit` (可选): 返回数量限制

**响应示例:**
```json
{
  "success": true,
  "message": "获取案例列表成功",
  "data": [
    {
      "case_id": "case_20250119_143000",
      "case_name": "测试案例",
      "status": "completed",
      "created_at": "2025-01-19T14:30:00"
    }
  ]
}
```

#### 获取案例详情
```
GET /api/v1/case/case_detail/{case_id}
```

#### 删除案例
```
DELETE /api/v1/case/delete_case/{case_id}
```

### 分析结果组 (`/api/v1/analysis/`)

#### 执行精度分析
```
POST /api/v1/analysis/analyze_accuracy/
```

**请求体示例:**
```json
{
  "case_id": "case_20250119_143000",
  "simulation_id": "sim_20250119_143000",
  "analysis_type": "comprehensive",
  "output_format": "all"
}
```

#### 获取分析结果
```
GET /api/v1/analysis/analysis_results/{case_id}/{simulation_id}
```

#### 获取分析报告
```
GET /api/v1/analysis/analysis_report/{case_id}/{simulation_id}
```

### 模板管理组 (`/api/v1/template/`)

#### 列出可用模板
```
GET /api/v1/template/list_templates/
```

#### 获取模板详情
```
GET /api/v1/template/template_detail/{template_id}
```

#### 创建新模板
```
POST /api/v1/template/create_template/
```

### 文件管理组 (`/api/v1/file/`)

#### 获取文件信息
```
GET /api/v1/file/file_info/{file_path}
```

## 🔧 开发指南

### 导入方式

#### 服务层导入
```python
from api.services.data_service import DataService
from api.services.simulation_service import SimulationService
from api.services.case_service import CaseService
from api.services.analysis_service import AnalysisService
```

#### 模型层导入
```python
from api.models.requests.data_requests import TimeRangeRequest
from api.models.requests.simulation_requests import SimulationRequest
from api.models.entities.case import Case
from api.models.entities.simulation import Simulation
```

#### 工具层导入
```python
from shared.utilities.time_utils import calculate_duration, parse_datetime
from shared.utilities.file_utils import ensure_directory, copy_template_file
from shared.data_access.connection import open_db_connection
from shared.data_access.gantry_loader import GantryDataLoader
```

### 错误处理

所有API都使用统一的错误处理机制：

```python
# 成功响应
{
  "success": true,
  "message": "操作成功",
  "data": {...}
}

# 错误响应
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {...}
}
```

### 状态码

- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

## 📊 性能指标

### 响应时间
- 简单查询: < 100ms
- 复杂计算: < 2s
- 文件上传: 根据文件大小

### 并发支持
- 支持多用户并发访问
- 数据库连接池管理
- 异步处理支持

## 🚀 扩展指南

### 添加新的API端点

1. **在相应的路由文件中添加端点**:
```python
# routes/data_routes.py
@router.post("/new_endpoint/")
async def new_endpoint(request: NewRequest):
    return await new_service(request)
```

2. **在服务层实现业务逻辑**:
```python
# services/data_service.py
async def new_service(request: NewRequest):
    # 实现业务逻辑
    pass
```

3. **定义请求/响应模型**:
```python
# models/requests/data_requests.py
class NewRequest(BaseModel):
    field1: str
    field2: int
```

### 添加新的业务服务

1. **创建服务文件**:
```python
# services/new_service.py
class NewService(BaseService):
    def __init__(self):
        super().__init__()
    
    async def process_request(self, request):
        # 实现业务逻辑
        pass
```

2. **在 `__init__.py` 中导出**:
```python
# services/__init__.py
from .new_service import NewService

__all__ = ["NewService"]
```

## 📚 相关文档

- [架构重构完成报告](../development/架构重构完成报告.md)
- [新架构开发指南](../development/新架构开发指南.md)
- [门架数据管理说明](../development/门架数据管理说明.md)
- [部署指南](../../DEPLOYMENT_GUIDE.md)

## 🗃 元数据规范（仿真三层）

以下定义适用于“仿真分支”的三层元数据。结果分析分支仅维护 `analysis` 下的元数据（批次与索引），不会创建或更新案例级与仿真分支的任何元数据。

### 第一层：案例级元数据（case_dir/metadata.json）

字段定义：

| 字段 | 类型 | 说明 |
|---|---|---|
| case_id | string | 案例目录名（唯一标识） |
| created_at | string(ISO8601) | 案例创建时间 |
| updated_at | string(ISO8601) | 最近一次变更时间（统一使用该字段） |
| status | string | 案例状态：active/simulating/completed/failed |
| description | string | 案例描述，可为空 |

创建/更新/删除规则：

- 创建：由案例创建流程或仿真启动前的前置流程写入；结果分析不会创建该文件。
- 更新：仿真启动、完成或失败时更新 `status` 与 `updated_at`；删除仿真时仅刷新 `updated_at`。
- 删除：删除案例目录时随目录一并删除。

边界约束：结果分析流程不创建/不更新该文件。

### 第二层：仿真索引（case_dir/simulations/simulations_index.json）

顶层字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| case_id | string | 所属案例ID（目录名） |
| simulation_count | number | `simulations` 子项数量（由系统维护） |
| updated_at | string(ISO8601) | 索引最近一次更新的时间 |
| simulations | array | 仿真记录列表 |

`simulations` 子项字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| simulation_id | string | 仿真ID（目录名） |
| simulation_name | string | 仿真名称 |
| simulation_type | string | microscopic/mesoscopic |
| status | string | running/completed/failed |
| created_at | string(ISO8601) | 仿真元数据创建时间 |
| started_at | string(ISO8601) | 仿真开始时间 |
| completed_at | string(ISO8601) | 仿真结束时间（完成/失败时写入） |
| duration | number | 耗时（秒），完成后写入 |
| error_message | string | 失败原因，可为空 |
| description | string | 仿真描述，可为空 |

创建/更新/删除规则：

- 创建：首次调用索引更新（仿真创建时）自动创建文件并写入首条记录。
- 更新：仿真状态变化（开始/完成/失败）时更新对应子项，并刷新顶层 `updated_at` 与 `simulation_count`。
- 删除：删除仿真时从 `simulations` 移除对应记录，并刷新顶层统计与 `updated_at`。

边界约束：结果分析流程不创建/不更新该文件。

### 第三层：单仿真元数据（case_dir/simulations/<sim_id>/simulation_metadata.json）

字段定义（创建时基础字段）：

| 字段 | 类型 | 说明 |
|---|---|---|
| simulation_id | string | 仿真ID（目录名） |
| case_id | string | 所属案例ID（目录名） |
| simulation_name | string | 仿真名称 |
| simulation_type | string | microscopic/mesoscopic（不会被结果分析覆盖） |
| simulation_params | object | 仿真参数（可选） |
| status | string | 初始为 running |
| created_at | string(ISO8601) | 元数据创建时间 |
| started_at | string(ISO8601) | 仿真开始时间 |
| description | string | 仿真描述（可选） |
| result_folder | string | 仿真结果目录（绝对/相对路径） |
| config_file | string | 配置文件路径 |
| input_files | object | 仿真输入文件清单（见下） |
| gui | boolean | 是否GUI模式 |

input_files 子字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| network_file | string|null | 路网文件路径（来自案例元数据 files.network_file） |
| routes_files | string[] | 路由文件列表（来自 files.routes_file，若存在则单元素列表） |
| taz_files | string[] | TAZ 文件列表（来自 files.taz_file，若存在则单元素列表） |

状态更新字段（运行结束写入）：

| 字段 | 类型 | 说明 |
|---|---|---|
| completed_at | string(ISO8601) | 完成或失败时间 |
| duration | number | 总耗时（秒），仅在完成时计算 |
| error_message | string | 失败原因（仅在失败时写入） |

创建/更新/删除规则：

- 创建：仿真启动时创建并写入初始元数据，同时从案例元数据 `files` 段收集并写入 `input_files`。
- 更新：仿真完成或失败后更新状态与时间字段；不修改 `input_files`；结果分析不会修改该文件，也不会覆盖 `simulation_type`。
- 删除：删除仿真目录时随目录一并删除。

边界约束：结果分析流程不创建/不更新该文件。

### 行为总览（调用关系）

- 仿真流程：
  - 创建并更新 单仿真元数据（第三级）
  - 更新 仿真索引（第二级）
  - 更新 案例级 `metadata.json` 的 `status/updated_at`（第一级）
- 结果分析流程：
  - 仅更新 `analysis/<batch>/metadata.json` 与 `analysis/analysis_index.json`
  - 不创建/不更新 案例级与仿真分支任何元数据

## 🔄 更新日志

### v2.0.0 (2025-01-19)
- ✅ 完成架构重构
- ✅ 实现完全模块化设计
- ✅ 移除向后兼容性
- ✅ 优化API组织结构
- ✅ 提升开发体验
