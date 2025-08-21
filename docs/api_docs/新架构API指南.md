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
      "created_at": "2025-01-19T14:30:00",
      "simulation_count": 2,
      "analysis_count": 1
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

## 🔄 更新日志

### v2.0.0 (2025-01-19)
- ✅ 完成架构重构
- ✅ 实现完全模块化设计
- ✅ 移除向后兼容性
- ✅ 优化API组织结构
- ✅ 提升开发体验
