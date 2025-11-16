# Phase 2 前后端 API 端点和接口确认指南

**版本**: 1.0
**日期**: 2025-11-16
**状态**: ✅ 已验证

---

## 目录

1. [概述](#概述)
2. [前端使用的 API 端点](#前端使用的-api-端点)
3. [后端服务实现](#后端服务实现)
4. [API 调用流程](#api-调用流程)
5. [数据模型](#数据模型)
6. [错误处理](#错误处理)

---

## 概述

Phase 2 实现需要前后端正确使用以下 API 端点：

| 功能模块 | 端点数量 | 状态 |
|---------|---------|------|
| 进度监控面板 | 2 个 | ✅ 已实现 |
| 批次对比分析 | 2 个 | ✅ 已实现 |
| 支持端点 | 多个 | ✅ 已实现 |
| **合计** | **4+ 个** | **✅** |

---

## 前端使用的 API 端点

### 1. 进度监控相关端点

#### 1.1 获取仿真进度 (单案例批次)

**端点**: `GET /api/v1/simulation/simulation_progress/{case_id}`

**用途**: 获取某个案例下的所有仿真进度信息

**前端调用场景**:
- 监控面板展开状态（5-10秒刷新一次）
- 监控面板折叠状态（30秒刷新一次）
- 表格数据更新

**请求参数**:
```
Path Parameters:
  - case_id (string, required): 案例ID，格式 "case_20251112_001"
```

**响应格式**:
```json
{
  "code": 200,
  "message": "获取进度成功",
  "data": {
    "case_id": "case_20251112_001",
    "event_scenario": "事件名称",
    "total_simulations": 10,
    "completed": 3,
    "running": 2,
    "failed": 0,
    "created": 5,
    "progress_percentage": 30,
    "simulations": [
      {
        "simulation_id": "sim_001",
        "case_id": "case_20251112_001",
        "status": "completed",  // 或 running, failed, created
        "progress": 100,        // 百分比 0-100
        "started_at": "2025-11-16T10:00:00",
        "completed_at": "2025-11-16T10:05:00",
        "duration": "5m 30s"
      },
      ...
    ]
  }
}
```

**前端代码示例**:
```javascript
// 展开状态：高频刷新
async function fetchProgressData(caseId) {
  const response = await fetch(`/api/v1/simulation/simulation_progress/${caseId}`);
  const data = await response.json();

  // 更新统计卡片
  updateStatisticCards(data.data);

  // 更新进度条
  updateProgressBar(data.data.progress_percentage);

  // 更新表格
  updateSimulationTable(data.data.simulations);

  // 如果展开，5-10秒后继续刷新
  if (isMonitoringExpanded) {
    setTimeout(() => fetchProgressData(caseId), 10000);
  } else {
    // 如果折叠，30秒后继续刷新
    setTimeout(() => fetchProgressData(caseId), 30000);
  }
}
```

**验证检查清单**:
- [ ] 前端能正确解析 simulations 数组
- [ ] progress_percentage 在 0-100 范围内
- [ ] 状态值为 "completed", "running", "failed", "created" 之一
- [ ] 时间戳格式为 ISO 8601

---

#### 1.2 获取案例下的所有仿真

**端点**: `GET /api/v1/simulation/simulations/{case_id}`

**用途**: 获取某个案例下的全部仿真列表（包括历史仿真）

**前端调用场景**:
- 页面初始化加载案例列表时
- 刷新查看全部仿真

**请求参数**:
```
Path Parameters:
  - case_id (string, required): 案例ID
```

**响应格式**:
```json
{
  "code": 200,
  "message": "获取仿真列表成功",
  "data": {
    "simulations": [
      {
        "simulation_id": "sim_001",
        "case_id": "case_20251112_001",
        "status": "completed",
        "scenario_name": "场景名称",
        "control_strategy": "VSS_001",
        "created_at": "2025-11-16T10:00:00",
        "updated_at": "2025-11-16T10:05:00"
      },
      ...
    ]
  }
}
```

---

### 2. 批次对比分析相关端点

#### 2.1 获取分析结果（批次级别）

**端点**: `GET /api/v1/analysis/results/{batch_id}`

**用途**: 获取多个仿真的聚合分析结果（用于对比分析）

**前端调用场景**:
- 对比分析标签页加载时
- 用户选择多个案例进行对比

**请求参数**:
```
Path Parameters:
  - batch_id (string, required): 批次ID，格式 "batch_20251112_100000"

Query Parameters:
  - case_id (string, required): 案例ID
```

**响应格式**:
```json
{
  "code": 200,
  "message": "获取分析结果成功",
  "data": {
    "summary": {
      "batch_id": "batch_20251112_100000",
      "case_id": "case_20251112_001",
      "total_simulations": 3,
      "analyzed_simulations": 3,
      "analysis_type": "comparison"
    },
    "metrics": [
      {
        "metric_name": "总车辆数",
        "unit": "个",
        "values": [1000, 1050, 980],
        "average": 1010,
        "min": 980,
        "max": 1050
      },
      {
        "metric_name": "平均行程时间",
        "unit": "分钟",
        "values": [25.3, 23.1, 26.5],
        "average": 24.97,
        "min": 23.1,
        "max": 26.5
      },
      ...
    ],
    "edgedata_metrics": [...],
    "aggregated_statistics": {...}
  }
}
```

---

#### 2.2 获取对比报告

**端点**: `GET /api/v1/analysis/comparison/{batch_id}`

**用途**: 生成多案例对比报告，计算差异和改善趋势

**前端调用场景**:
- 对比分析表格渲染时
- 计算并展示差异百分比

**请求参数**:
```
Path Parameters:
  - batch_id (string, required): 批次ID

Query Parameters:
  - case_id (string, required): 案例ID
```

**响应格式**:
```json
{
  "code": 200,
  "message": "生成对比报告成功",
  "data": {
    "comparison_table": [
      {
        "metric_name": "总车辆数",
        "case_a": {
          "case_id": "case_001",
          "value": 1000
        },
        "case_b": {
          "case_id": "case_002",
          "value": 1050
        },
        "difference": 50,
        "difference_percentage": 5.0,
        "improvement": "negative"  // 或 "positive", "neutral"
      },
      ...
    ],
    "ranking": [
      {
        "rank": 1,
        "case_id": "case_001",
        "case_name": "方案A",
        "score": 95.5
      },
      ...
    ]
  }
}
```

**前端代码示例**:
```javascript
async function loadComparisonAnalysis(caseIds) {
  // 步骤1：调用 batch-start 或创建 batch_id
  const batchId = "batch_20251112_100000";

  // 步骤2：获取对比报告
  const response = await fetch(
    `/api/v1/analysis/comparison/${batchId}?case_id=${caseIds[0]}`
  );
  const data = await response.json();

  // 步骤3：渲染对比表格
  renderComparisonTable(data.data.comparison_table);

  // 步骤4：颜色标记改善/恶化
  data.data.comparison_table.forEach(row => {
    if (row.improvement === "positive") {
      markAsImproved(row.metric_name);  // 绿色
    } else if (row.improvement === "negative") {
      markAsWorsened(row.metric_name);  // 红色
    }
  });
}
```

---

### 3. 支持性端点

#### 3.1 获取单个仿真详情

**端点**: `GET /api/v1/simulation/simulation/{simulation_id}`

**用途**: 获取单个仿真的详细信息（用于"查看分析"跳转）

**前端调用场景**:
- 点击表格中的"查看分析"按钮前
- 获取 simulation_id 确认仿真已完成

**请求参数**:
```
Path Parameters:
  - simulation_id (string, required): 仿真ID
```

**响应格式**:
```json
{
  "code": 200,
  "message": "获取仿真详情成功",
  "data": {
    "simulation_id": "sim_001",
    "case_id": "case_20251112_001",
    "status": "completed",
    "scenario_name": "场景名称",
    "control_strategy": "VSS_001",
    "progress": 100,
    "created_at": "2025-11-16T10:00:00",
    "started_at": "2025-11-16T10:01:00",
    "completed_at": "2025-11-16T10:05:00",
    "output_format": "tripinfo,vehroute,edgedata"
  }
}
```

---

#### 3.2 批量启动仿真

**端点**: `POST /api/v1/simulation/batch-start`

**用途**: 批量启动多个仿真（Phase 1 已实现，Phase 2 复用）

**前端调用场景**:
- 用户在案例列表中批量选择案例并点击"批量启动"时

**请求格式**:
```json
POST /api/v1/simulation/batch-start
{
  "simulation_ids": ["sim_001", "sim_002", "sim_003"],
  "case_id": "case_20251112_001",
  "parallel_workers": 4,
  "auto_run_analysis": true,
  "analysis_types": ["accuracy", "edgedata"]
}
```

**响应格式**:
```json
{
  "code": 200,
  "message": "批量仿真已启动",
  "data": {
    "batch_id": "batch_20251112_100000",
    "total_simulations": 3,
    "status": "queued",
    "started_at": "2025-11-16T10:00:00"
  }
}
```

---

## 后端服务实现

### 后端服务架构

```
api/routes/
├── simulation_routes.py
│   ├── GET /simulation_progress/{case_id}
│   ├── GET /simulations/{case_id}
│   ├── GET /simulation/{simulation_id}
│   └── POST /batch-start
│
└── analysis_routes.py
    ├── GET /analysis_results/{case_id}
    ├── GET /results/{batch_id}           ← 批次聚合分析
    ├── GET /comparison/{batch_id}        ← 批次对比报告
    └── [各分析类型的具体分析端点]

api/services/
├── simulation_orchestrator.py            ← 批量仿真管理
├── accuracy_service.py                   ← 精度分析
├── mechanism_service.py                  ← 机理分析
├── performance_service.py                ← 性能分析
├── edgedata_service.py                   ← EdgeData分析
└── analysis_results_service.py           ← 分析结果聚合
```

### 关键服务方法

#### 获取仿真进度服务

```python
# File: api/services/simulation_service.py
async def get_simulation_progress_service(case_id: str) -> dict:
    """
    获取案例下的所有仿真进度

    Returns:
        {
            "case_id": str,
            "total_simulations": int,
            "completed": int,
            "running": int,
            "failed": int,
            "created": int,
            "progress_percentage": float (0-100),
            "simulations": [
                {
                    "simulation_id": str,
                    "status": str,  # completed, running, failed, created
                    "progress": int,
                    "started_at": str,
                    "completed_at": str,
                    "duration": str
                },
                ...
            ]
        }
    """
    # 1. 从数据库或文件系统读取仿真元数据
    # 2. 计算进度百分比
    # 3. 按状态分类统计
    # 4. 返回格式化数据
```

#### 分析结果聚合服务

```python
# File: api/services/analysis_results_service.py
async def get_analysis_results(batch_id: str, case_id: str) -> AnalysisResultsResponse:
    """
    获取批次的聚合分析结果

    用于对比分析标签页加载数据

    Returns:
        AnalysisResultsResponse:
            - summary: 批次摘要
            - metrics: 聚合指标（跨多个仿真）
            - edgedata_metrics: EdgeData指标
            - aggregated_statistics: 统计汇总
    """
    # 1. 根据 batch_id 查找所有仿真
    # 2. 对每个仿真的分析结果进行聚合
    # 3. 计算平均值、最小值、最大值
    # 4. 返回聚合后的结果

async def get_comparison_report(batch_id: str, case_id: str) -> ComparisonReportResponse:
    """
    生成批次对比报告

    计算多个案例/仿真之间的差异和改善趋势

    Returns:
        ComparisonReportResponse:
            - comparison_table: 对比表格（含差异百分比）
            - ranking: 案例/仿真排名
    """
    # 1. 获取多个仿真的分析结果
    # 2. 计算差异百分比: (value_b - value_a) / value_a * 100
    # 3. 判断改善趋势（基于指标定义）
    # 4. 生成排名
```

---

## API 调用流程

### 流程1：进度监控更新流程

```
用户打开 case-simulation-center.html
    ↓
页面加载时调用:
  GET /api/v1/simulation/simulations/{case_id}  ← 获取仿真列表
    ↓
用户展开监控面板
    ↓
启动 5-10 秒循环刷新:
  GET /api/v1/simulation/simulation_progress/{case_id}
    ↓
收到响应，更新:
  1. 统计卡片 (总/完成/运行/失败)
  2. 进度条 (progress_percentage)
  3. 详细表格 (simulations 数组)
    ↓
用户折叠监控面板
    ↓
改为 30 秒循环刷新
    ↓
所有仿真完成或失败时
    ↓
停止刷新，显示完成提示
```

### 流程2：对比分析流程

```
用户在分析页面选择"对比分析"标签页
    ↓
显示"选择案例"按钮
    ↓
用户点击，弹出案例选择器
    ↓
用户多选 2 个或以上案例，点击"确认对比"
    ↓
前端准备 batch_id（可从 URL 或后端批量启动响应）
    ↓
并行调用两个 API:
  1. GET /api/v1/analysis/results/{batch_id}?case_id=...
  2. GET /api/v1/analysis/comparison/{batch_id}?case_id=...
    ↓
收到响应，渲染:
  1. 多案例指标卡片（顶部）
  2. 对比表格（详细指标 + 差异 + 改善标签）
  3. 排名表格
    ↓
用户可复制当前 URL 分享: ?case_ids=case1,case2,case3
```

### 流程3：跳转到分析流程

```
用户在监控面板详细表格中
    ↓
点击某行的"查看分析"按钮
    ↓
前端调用:
  GET /api/v1/simulation/simulation/{simulation_id}  ← 确认已完成
    ↓
跳转到:
  analysis_viewer.html?case_id={case_id}&simulation_id={sim_id}
    ↓
分析页面加载时调用分析 API
    ↓
显示单个案例的分析结果
```

---

## 数据模型

### 请求模型

#### BatchSimulationStartRequest
```python
from pydantic import BaseModel
from typing import List, Optional

class BatchSimulationStartRequest(BaseModel):
    simulation_ids: List[str]  # 仿真ID列表，如 ["sim_001", "sim_002"]
    case_id: str               # 案例ID，如 "case_20251112_001"
    parallel_workers: int = 4  # 并发数，默认4
    auto_run_analysis: bool = True  # 自动分析
    analysis_types: Optional[List[str]] = None  # 分析类型列表
```

### 响应模型

#### SimulationProgressResponse
```python
from typing import List
from pydantic import BaseModel

class SimulationItem(BaseModel):
    simulation_id: str
    case_id: str
    status: str  # completed, running, failed, created
    progress: int  # 0-100
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: Optional[str] = None

class SimulationProgressResponse(BaseModel):
    case_id: str
    total_simulations: int
    completed: int
    running: int
    failed: int
    created: int
    progress_percentage: float
    simulations: List[SimulationItem]
```

#### ComparisonReportResponse
```python
from typing import List

class ComparisonMetric(BaseModel):
    metric_name: str
    case_a_value: float
    case_b_value: float
    difference: float
    difference_percentage: float
    improvement: str  # positive, negative, neutral

class ComparisonReportResponse(BaseModel):
    comparison_table: List[ComparisonMetric]
    ranking: List[dict]  # 排名信息
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 含义 | 前端处理 |
|--------|------|---------|
| 200 | 成功 | 解析响应数据 |
| 400 | 请求参数错误 | 显示错误提示，检查参数 |
| 404 | 资源不存在 | 显示"未找到"提示 |
| 500 | 服务器错误 | 显示"服务器错误，请稍后重试" |

### 错误响应格式

```json
{
  "code": 400,
  "message": "参数错误：case_id 不能为空",
  "data": null
}
```

### 前端错误处理示例

```javascript
async function fetchProgressData(caseId) {
  try {
    const response = await fetch(
      `/api/v1/simulation/simulation_progress/${caseId}`
    );

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    const data = await response.json();

    if (data.code !== 200) {
      console.error(`后端错误: ${data.message}`);
      showErrorMessage(data.message);
      return;
    }

    // 处理成功响应
    updateMonitoringPanel(data.data);

  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    showErrorMessage("获取进度数据失败，请重试");
  }
}
```

---

## 实现检查清单

### 后端需要实现/验证

- [ ] `GET /api/v1/simulation/simulation_progress/{case_id}`
  - [ ] 返回正确的进度统计
  - [ ] simulations 数组包含所有必需字段
  - [ ] progress_percentage 计算正确

- [ ] `GET /api/v1/analysis/results/{batch_id}`
  - [ ] 支持 ?case_id 查询参数
  - [ ] 返回聚合的指标数据

- [ ] `GET /api/v1/analysis/comparison/{batch_id}`
  - [ ] 支持 ?case_id 查询参数
  - [ ] 正确计算差异百分比
  - [ ] improvement 字段正确判断

- [ ] 所有端点
  - [ ] 错误处理完善
  - [ ] 返回格式统一
  - [ ] 性能满足前端刷新需求（<2秒）

### 前端需要实现

- [ ] 进度监控面板
  - [ ] 展开/折叠状态切换
  - [ ] 动态刷新频率调整
  - [ ] 表格筛选和排序
  - [ ] "查看分析"按钮导航

- [ ] 对比分析页面
  - [ ] 案例选择器
  - [ ] 多选功能
  - [ ] 对比表格渲染
  - [ ] 差异颜色标记

- [ ] 响应式设计
  - [ ] 移动设备表格滚动
  - [ ] 各断点布局切换
  - [ ] 字体和间距调整

---

## 参考资源

- **API 文档**: `/api/docs` (自动生成的 Swagger UI)
- **后端代码**: `api/routes/`, `api/services/`
- **前端代码**: `frontend/scenarios/case-simulation-center.html`, `analysis_viewer.html`
- **数据模型**: `api/models/`

---

**最后更新**: 2025-11-16
**维护人员**: 系统架构团队
**下一个审查**: 实现完成后
