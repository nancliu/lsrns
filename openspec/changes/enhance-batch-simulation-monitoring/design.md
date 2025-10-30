# 设计文档：增强批量仿真监控与管理

**变更ID**: enhance-batch-simulation-monitoring
**创建日期**: 2025-10-29
**版本**: 1.0

---

## 1. 架构概览

### 1.1 系统上下文

本变更增强现有的批量仿真系统，添加实时监控和批次管理能力。系统架构保持现有的两层模式（API层 + Shared层），在此基础上扩展功能。

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (Frontend)                         │
│                                                              │
│  simulations.html (批量仿真页面)                             │
│  ├── Tab 1: 配置视图                                         │
│  ├── Tab 2: 进度视图 ⭐ (增强: 实时监控)                      │
│  ├── Tab 3: 结果视图 ⭐ (新增: 基础对比)                      │
│  └── Tab 4: 批次历史 ⭐ (新增: 历史管理)                      │
│                                                              │
│  optimization.html (方案优化页面) ⭐ (增强: 深度分析)         │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────┴───────────────────────────────────────┐
│                    API层 (api/)                              │
│                                                              │
│  batch_optimization_routes.py                               │
│  ├── GET /batches ⭐ (新增: 批次列表)                        │
│  ├── GET /batches/{id}/detail ⭐ (新增: 批次详情)            │
│  ├── GET /batch/{id}/progress ⭐ (增强: 实时监控)            │
│  ├── DELETE /batches/{id} ⭐ (新增: 删除/归档)               │
│  └── POST /batches/{id}/reanalyze ⭐ (新增: 重新分析)        │
│                                                              │
│  batch_optimization_service.py                              │
│  ├── _extract_summary_last_step() ⭐ (新增)                 │
│  ├── _get_simulation_live_status() ⭐ (新增)                │
│  ├── _estimate_task_remaining_time() ⭐ (新增)              │
│  ├── _estimate_batch_remaining_time() ⭐ (新增)             │
│  ├── list_batches() ⭐ (新增)                               │
│  ├── delete_batch() ⭐ (新增)                               │
│  └── reanalyze_batch() ⭐ (新增)                            │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────────────┐
│                  文件系统 (File System)                      │
│                                                              │
│  cases/{case_id}/simulations/plan_opti/                     │
│  ├── batches_index.json ⭐ (新增: 批次索引)                  │
│  └── {batch_id}/                                            │
│      ├── batch_metadata.json                                │
│      ├── batch_progress.json                                │
│      ├── batch_summary.json                                 │
│      └── {plan_id}/                                         │
│          └── sim_{seed}/                                    │
│              ├── summary.xml ⭐ (实时读取)                   │
│              ├── tripinfo.xml                               │
│              └── simulation_metadata.json                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

#### 1.2.1 实时监控模块 (Live Monitoring)

**职责**:
- 从运行中仿真的summary.xml提取最新状态
- 估算单个任务和批次的剩余时间
- 为前端提供实时监控数据

**关键技术**:
- **增量解析**: 仅解析summary.xml的最后一个`<step>`元素，避免全文解析
- **缓存机制**: 使用TTL缓存（5秒）减少文件I/O
- **异常处理**: 优雅处理文件不存在、解析失败等情况

#### 1.2.2 批次管理模块 (Batch Management)

**职责**:
- 维护批次索引文件（batches_index.json）
- 提供批次列表查询、详情查询、删除、归档、重新分析功能
- 管理历史批次的生命周期

**关键技术**:
- **索引同步**: 在批次创建、状态变更、删除时自动更新索引
- **分页查询**: 支持大量历史批次的高效查询
- **归档机制**: 保留元数据，删除大文件（summary.xml等）以节省空间

#### 1.2.3 结果页面分离 (Result Page Separation)

**职责**:
- 明确批量仿真页面和方案优化页面的职责边界
- 提供流畅的页面跳转和上下文传递
- 支持快速查看（基础对比）和深度分析（决策支持）

**设计原则**:
- **职责单一**: 批量仿真页面关注执行和监控，方案优化页面关注分析和决策
- **渐进展示**: 用户先看基础对比，需要时再进入深度分析
- **无缝衔接**: 通过URL参数传递batch_id，确保上下文连贯

---

## 2. 关键技术决策

### 2.1 summary.xml增量解析

**问题**: summary.xml文件可能很大（>10MB），包含上万个`<step>`元素。每次查询进度时全文解析会导致性能问题。

**方案对比**:

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **A. 全文解析** | 实现简单 | 性能差（50ms+/文件） | ❌ |
| **B. 增量解析（从末尾读取）** | 性能好（<10ms） | 需要seekable文件处理 | ✅ **推荐** |
| **C. 实时监听SUMO输出** | 最实时 | 复杂度高，需要进程管理 | ❌ |
| **D. 使用SUMO的CSV输出** | 易解析 | 需要修改仿真配置 | ❌ |

**最终选择**: **方案B - 增量解析**

**实现细节**:
```python
def _extract_summary_last_step(summary_file: Path) -> Dict:
    """
    增量解析summary.xml，仅提取最后一个<step>元素

    策略:
    1. 从文件末尾向前搜索最后一个</step>标签
    2. 向前扩展读取完整的<step>元素（约200-500字节）
    3. 使用xml.etree.ElementTree解析单个元素
    4. 返回字典：{time, running, loaded, ended, meanSpeed}

    性能: <10ms (vs 全文解析的50ms)
    """
    if not summary_file.exists():
        return None

    # 从末尾读取最后4KB（通常足够包含最后一个<step>）
    with open(summary_file, 'rb') as f:
        f.seek(0, 2)  # 移到文件末尾
        file_size = f.tell()
        read_size = min(4096, file_size)
        f.seek(-read_size, 2)
        tail_content = f.read().decode('utf-8', errors='ignore')

    # 正则提取最后一个<step>元素
    import re
    match = re.search(r'<step\s+([^>]+)/>', tail_content[::-1])
    if not match:
        return None

    # 反转并解析属性
    step_tag = match.group(0)[::-1]
    # ... 解析属性 ...

    return parsed_data
```

### 2.2 轮询频率优化

**问题**: 原设计前端每2秒轮询，对服务器压力较大且实时性提升有限。

**方案调整**:
- **前端轮询间隔**: 从2秒调整为**10秒**
- **Backend缓存TTL**: 保持5秒不变
- **理由**:
  - summary.xml每秒写入新数据，但10秒粒度足够显示仿真进展
  - 降低服务器负载（请求量减少80%）
  - 缓存TTL=5秒，确保每2次轮询至少刷新一次数据

### 2.3 进度查询缓存策略

**问题**: 每次查询需读取60+个summary.xml文件，频繁I/O影响性能。

**方案对比**:

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **A. 无缓存** | 数据最新 | 性能差（200ms+响应） | ❌ |
| **B. 内存缓存（TTL=5秒）** | 性能好（10ms响应） | 5秒内数据可能稍旧 | ✅ **推荐** |
| **C. Redis缓存** | 性能好，支持分布式 | 引入外部依赖 | ❌ |
| **D. 后台定时刷新** | 主动更新 | 复杂度高 | ❌ |

**最终选择**: **方案B - 内存缓存（TTL=5秒）**

**理由**:
- 5秒延迟对实时监控影响可接受（前端10秒轮询，每2次轮询刷新一次缓存）
- 无需外部依赖，实现简单
- 缓存失效后自动刷新，无需额外管理

**实现**:
```python
from cachetools import TTLCache

# 缓存：batch_id -> progress_data
progress_cache = TTLCache(maxsize=100, ttl=5)

def get_batch_progress_cached(batch_id: str) -> Dict:
    if batch_id in progress_cache:
        logger.debug(f"Cache hit for batch {batch_id}")
        return progress_cache[batch_id]

    logger.debug(f"Cache miss for batch {batch_id}, loading from disk")
    progress = _load_batch_progress_from_disk(batch_id)
    progress_cache[batch_id] = progress
    return progress
```

### 2.4 动态在网车辆曲线设计

**问题**: 如何在进度视图实时显示在网车辆数曲线？

**方案对比**:

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **A. 每个任务单独曲线** | 详细 | 复杂，多曲线难以阅读 | ❌ |
| **B. 汇总所有任务的总在网车辆数** | 简单直观 | 无法看单个任务细节 | ✅ **推荐** |
| **C. 按方案分组显示曲线** | 平衡详细和简洁 | 实现复杂 | ❌ (未来增强) |

**最终选择**: **方案B - 汇总总在网车辆数**

**实现细节**:

**Backend**:
```python
def get_batch_progress_with_live_monitoring(...) -> Dict:
    """
    返回进度数据时，额外计算live_time_series用于动态曲线
    """
    progress_data = self._load_batch_progress(batch_id)

    # 对每个running任务提取live_status
    for task in progress_data['tasks']:
        if task['status'] == 'running':
            task['live_status'] = self._get_simulation_live_status(...)

    # 新增：汇总时序数据（用于动态曲线）
    live_time_series = self._aggregate_live_time_series(
        progress_data['tasks']
    )
    # {
    #   'time_points': [0, 10, 20, ..., 1500],  # 当前已运行的时间点
    #   'total_running': [0, 50, 120, ..., 320],  # 汇总所有任务的在网车辆数
    #   'last_update': '2025-10-29T10:25:00'
    # }

    progress_data['live_time_series'] = live_time_series
    return progress_data
```

**Frontend**:
```javascript
// batch_simulation.js

let liveCurveChartInstance = null;

function renderLiveCurve(liveTimeSeries) {
    if (!liveTimeSeries || liveTimeSeries.time_points.length === 0) {
        // 无数据时隐藏图表区域
        document.getElementById('liveCurveSection').style.display = 'none';
        return;
    }

    document.getElementById('liveCurveSection').style.display = 'block';

    // 转换时间点为HH:MM格式
    const timeLabels = liveTimeSeries.time_points.map(t => {
        const hours = Math.floor(t / 3600);
        const minutes = Math.floor((t % 3600) / 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    });

    // 销毁旧图表实例
    if (liveCurveChartInstance) {
        liveCurveChartInstance.destroy();
    }

    // 创建简单折线图（无复杂交互）
    const ctx = document.getElementById('liveCurveChart').getContext('2d');
    liveCurveChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: '总在网车辆数',
                data: liveTimeSeries.total_running,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: '动态在网车辆数曲线（实时）',
                    font: { size: 14 }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => context.parsed.y.toFixed(0) + ' 辆'
                    }
                },
                // 禁用放大、平移等复杂功能
                zoom: { zoom: { wheel: { enabled: false } } }
            },
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: '仿真时间' }
                },
                y: {
                    display: true,
                    title: { display: true, text: '在网车辆数 (辆)' },
                    beginAtZero: true
                }
            },
            // 禁用交互（无hover、点击等）
            interaction: { mode: 'nearest', intersect: false }
        }
    });
}

// 在进度轮询中调用
async function pollProgress() {
    const response = await fetch(`${API_BASE}/control/batch-optimization/batch/${currentBatchId}/progress`);
    const data = await response.json();

    // 更新任务列表
    updateTaskList(data.tasks);

    // 更新动态曲线
    renderLiveCurve(data.live_time_series);
}

// 轮询间隔：10秒
setInterval(pollProgress, 10000);
```

**特性**:
- ✅ 简单折线图，单一曲线
- ✅ 无放大、缩放、导出等功能
- ✅ 自动隐藏（无运行批次时）
- ✅ 每10秒自动更新
- ✅ 汇总所有running任务的在网车辆数

### 2.5 批次索引文件设计

**问题**: 如何高效查询历史批次列表（可能有100+个批次）？扫描所有批次目录太慢。

**方案对比**:

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **A. 扫描批次目录** | 无额外文件 | 慢（300ms+ for 100批次） | ❌ |
| **B. 索引文件（batches_index.json）** | 快（<50ms） | 需要同步维护 | ✅ **推荐** |
| **C. 数据库（SQLite/PostgreSQL）** | 高性能，支持复杂查询 | 引入数据库依赖 | ❌ |

**最终选择**: **方案B - 索引文件**

**索引文件结构**:
```json
{
  "batches": [
    {
      "batch_id": "batch_20251029_103000",
      "case_id": "case_001",
      "plan_count": 3,
      "total_tasks": 9,
      "status": "completed",
      "created_at": "2025-10-29T10:30:00",
      "completed_at": "2025-10-29T11:15:00",
      "duration_seconds": 2640,
      "success_rate": 1.0
    },
    ...
  ],
  "last_updated": "2025-10-29T14:30:00"
}
```

**同步时机**:
- 批次创建时：添加新记录
- 批次状态变更时（started/completed/cancelled）：更新记录
- 批次删除时：移除记录

### 2.6 结果页面职责划分

**问题**: 批量仿真页面和方案优化页面都可以显示结果，如何划分职责？

**设计原则**:

| 页面 | 定位 | 内容 | 用户场景 |
|------|------|------|----------|
| **批量仿真 - 结果视图** | 快速查看 | 基础对比（表格、曲线、卡片） | "仿真完成了，快速看看哪个方案更好" |
| **方案优化页面** | 深度分析 | 详细对比、雷达图、报告导出 | "需要深入分析，写报告/做决策" |

**导航流程**:
```
用户启动批次 → 监控进度 → 批次完成
    ↓
自动切换到"结果视图"（基于summary.xml的基础对比）
    ↓
查看基础对比（快速扫一眼）
    - 方案对比表（行程时间、速度、车辆数）
    - 峰值曲线
    - 峰值指标卡片
    ↓
决定: 够了 or 需要进一步分析
    ↓ (需要进一步分析)
点击"查看详细优化分析"按钮
    ↓
跳转到 optimization.html?batch_id=xxx（深度分析页面）
    ↓
查看详细分析、多指标雷达图、导出报告
```

**职责边界**:

| 维度 | 批量仿真页面 | 方案优化页面 |
|------|-------------|-------------|
| **关注点** | 执行和监控 | 分析和决策 |
| **数据来源** | summary.xml（基础指标） | summary.xml + tripinfo.xml等（详细指标） |
| **数据粒度** | 基础指标（行程时间、速度、车辆数） | 详细指标（10+个） |
| **可视化** | 峰值曲线（简单） | 峰值曲线（交互）+雷达图 |
| **交互** | 简单查看 | 交互分析（缩放、导出） |
| **导出** | 无 | PDF/Excel/PNG |
| **URL** | simulations.html | optimization.html?batch_id=xxx |

---

## 3. 数据模型

### 3.0 进度字段同步问题修复 (2025-10-29)

**问题**：批量仿真任务进度在前端显示为 `undefined%`

**根因**：
- `shared/control_tools/batch_simulation_scheduler.py` 中的 `BatchTask` dataclass 定义了 `progress: int = 0` 字段
- `api/models/control/entities/batch_simulation.py` 中的 `BatchSimulationTask` Pydantic模型**缺少** `progress` 字段定义
- Pydantic序列化API响应时，会过滤掉未定义的字段，导致前端无法获取进度数据

**修复内容**：

1. **在 BatchSimulationTask 模型中添加 progress 字段**：
```python
# api/models/control/entities/batch_simulation.py

progress: int = Field(
    default=0,
    description="仿真进度百分比（0-100）",
    ge=0,
    le=100,
    examples=[85]
)
```

2. **修复仿真执行器中缺少 progress_path 参数**：
```python
# shared/control_tools/batch_simulation_scheduler.py:589

request_params = {
    "run_folder": str(simulation_folder),
    "gui": False,
    "mesoscopic": sim_metadata.get("simulation_type") == "mesoscopic",
    "config_file": config_file,
    "expected_duration": sim_metadata.get("simulation_params", {}).get("expected_duration"),
    "progress_path": str(simulation_folder / "progress.json"),  # ✅ 添加此行
}
```

3. **更新所有相关示例数据**，确保包含 `progress` 字段

**影响范围**：
- `api/models/control/entities/batch_simulation.py` - 添加 progress 字段定义
- `api/models/control/responses/batch_response.py` - 更新示例数据
- `shared/control_tools/batch_simulation_scheduler.py` - 添加 progress_path 参数

**验收**：
- ✅ API响应中包含 `progress` 字段（值范围 0-100）
- ✅ 前端正确显示各个任务的进度百分比（例如：95%）
- ✅ 进度文件 `progress.json` 正常写入和更新
- ✅ 批次进度监控正常工作（批次级和任务级）

**技术细节**：
- Pydantic响应模型的字段定义必须与后端数据源（BatchTask dataclass）保持一致
- 仿真执行时必须传递 `progress_path` 参数，否则 `SimulationProcessor.write_progress()` 会提前返回
- 进度监控协程 `_monitor_simulation_progress()` 依赖 `progress.json` 文件来更新任务进度

### 3.1 批次索引（batches_index.json）

**位置**: `cases/{case_id}/simulations/plan_opti/batches_index.json`

**结构**:
```typescript
interface BatchesIndex {
  batches: BatchSummary[];
  last_updated: string;  // ISO 8601
}

interface BatchSummary {
  batch_id: string;
  case_id: string;
  case_name?: string;
  plan_ids: string[];
  plan_count: number;
  total_tasks: number;
  num_seeds: number;
  base_seed: number;
  max_concurrent: number;
  status: "pending" | "running" | "completed" | "cancelled" | "failed" | "archived";
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  success_rate?: number;  // 0.0 - 1.0
  completed_tasks?: number;
  failed_tasks?: number;
}
```

### 3.2 实时状态（live_status）

**在进度API响应中包含**:

```typescript
interface TaskProgress {
  task_id: string;
  plan_id: string;
  plan_name: string;
  seed: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  simulation_id?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error?: string;

  // 新增: 实时监控数据
  live_status?: {
    current_step: number;
    total_steps: number;
    progress_percent: number;  // 0-100
    running_vehicles: number;
    ended_vehicles: number;
    loaded_vehicles: number;
    mean_speed_ms: number;
    mean_speed_kmh: number;
    estimated_remaining_seconds?: number;
    estimated_remaining_display?: string;  // "21分30秒"
    message?: string;  // "仿真正在初始化..." / "无法读取状态"
  };
}

interface BatchProgress {
  batch_id: string;
  case_id: string;
  status: string;
  progress: number;  // 0.0 - 1.0
  max_concurrent: number;
  tasks: TaskProgress[];

  // 新增: 批次级估算
  estimated_completion_seconds?: number;
  estimated_completion_display?: string;  // "约1小时28分"
  estimated_completion_time?: string;  // ISO 8601
}
```

### 3.3 批次详情（detail）

**API响应结构**:

```typescript
interface BatchDetail {
  // 基础信息
  batch_id: string;
  case_id: string;
  case_name?: string;
  plan_ids: string[];
  num_seeds: number;
  base_seed: number;
  max_concurrent: number;

  // 状态
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;

  // 任务列表（完整）
  tasks: TaskProgress[];

  // 摘要统计
  summary: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    cancelled_tasks: number;
    success_rate: number;
    avg_task_duration_seconds?: number;
  };
}
```

---

## 4. API设计

### 4.1 新增API

#### 4.1.1 批次列表

```
GET /api/v1/control/batch-optimization/batches

Query参数:
  - status: string (可选) - 筛选状态（running/completed/cancelled/failed/archived）
  - case_id: string (可选) - 筛选case
  - start_date: string (可选) - 起始日期（YYYY-MM-DD）
  - end_date: string (可选) - 结束日期（YYYY-MM-DD）
  - page: int (默认1) - 页码
  - limit: int (默认20) - 每页数量

响应: 200 OK
{
  "batches": [BatchSummary],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

#### 4.1.2 批次详情

```
GET /api/v1/control/batch-optimization/batches/{batch_id}/detail

响应: 200 OK
BatchDetail
```

#### 4.1.3 删除/归档批次

```
DELETE /api/v1/control/batch-optimization/batches/{batch_id}?archive=false

Query参数:
  - archive: bool (默认false) - true=归档（保留元数据），false=完全删除

响应: 204 No Content (完全删除)
响应: 200 OK {"message": "批次已归档"} (归档)
错误: 409 Conflict (批次正在运行)
```

#### 4.1.4 重新分析批次

```
POST /api/v1/control/batch-optimization/batches/{batch_id}/reanalyze

响应: 200 OK
{
  "message": "分析完成",
  "batch_id": "batch_001",
  "reanalyzed_at": "2025-10-29T14:30:00"
}
```

### 4.2 增强现有API

#### 4.2.1 进度查询（增加live_status）

```
GET /api/v1/control/batch-optimization/batch/{batch_id}/progress

响应: 200 OK
BatchProgress (包含live_status字段)
```

---

## 5. 前端设计

### 5.1 批量仿真页面（simulations.html）

**Tab结构**:
```
┌─────────────────────────────────────────────────────┐
│  [配置] [进度⭐] [结果⭐] [批次历史⭐]               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  (当前Tab的内容)                                     │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Tab 2: 进度视图（增强）**

```
┌─────────────────────────────────────────────────────┐
│  批次信息                                            │
│  batch_001 | 运行中 | 25% (15/60)                   │
│  预计完成: 11:30 | 剩余: 约1小时28分 ⏱               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  任务列表                                            │
│  ┌──────┬───────┬────┬────────┬──────┬────────────┐ │
│  │任务ID│方案   │种子│状态    │进度  │实时状态⭐   │ │
│  ├──────┼───────┼────┼────────┼──────┼────────────┤ │
│  │t_001 │方案A  │66  │运行中  │10%   │320辆       │ │
│  │      │       │    │        │█     │剩余:21分30秒│ │
│  ├──────┼───────┼────┼────────┼──────┼────────────┤ │
│  │t_002 │方案A  │67  │等待中  │-     │-           │ │
│  └──────┴───────┴────┴────────┴──────┴────────────┘ │
│  注：进度视图简化，不显示平均速度                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  动态在网车辆曲线⭐（新增）                          │
│  [Chart.js简单折线图: 汇总所有运行中任务]            │
│  - 每10秒自动更新                                    │
│  - 简单折线图，无放大/导出功能                       │
│  - 无运行批次时自动隐藏                              │
└─────────────────────────────────────────────────────┘
```

**Tab 3: 结果视图（新增）**

```
┌─────────────────────────────────────────────────────┐
│  方案对比表                                          │
│  ┌────────┬──────────┬────────┬──────────┬────────┐ │
│  │方案    │平均行程  │相比基准│平均速度  │总车辆数│ │
│  ├────────┼──────────┼────────┼──────────┼────────┤ │
│  │基准方案│1448.5s   │-       │22.3 km/h │500     │ │
│  │方案A   │1250.3s   │↓-13.7% │26.1 km/h │520     │ │
│  │方案B   │1180.8s   │↓-18.5%✓│28.5 km/h │540     │ │
│  └────────┴──────────┴────────┴──────────┴────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  在网车辆峰值曲线                                     │
│  [Chart.js折线图: 3条曲线，蓝/绿/橙]                 │
└─────────────────────────────────────────────────────┘

┌────────────┐ ┌────────────┐ ┌────────────────┐
│基准方案    │ │方案A       │ │方案B (最优) ✓  │
│峰值:450辆  │ │峰值:380辆  │ │峰值:350辆      │
│时刻:08:15  │ │时刻:08:20  │ │时刻:08:25      │
└────────────┘ └────────────┘ └────────────────┘

┌─────────────────────────────────────────────────────┐
│         🔍 查看详细优化分析                          │
│        (包含多指标雷达图、深度对比等)                 │
└─────────────────────────────────────────────────────┘
```

**Tab 4: 批次历史（新增）**

```
┌─────────────────────────────────────────────────────┐
│  筛选: [全部状态▼] [最近30天▼] [搜索...]            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  批次列表 (卡片视图)                                 │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ batch_...3000 | case_001 | 完成✓             │    │
│  │ 3个方案 | 9/9任务成功 | 2小时前完成           │    │
│  │ [查看结果] [删除]                             │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ batch_...2500 | case_002 | 运行中⏳           │    │
│  │ 5个方案 | 35% (7/20) | 预计30分钟后完成      │    │
│  │ [监控进度]                                   │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 5.2 方案优化页面（optimization.html）

**增强功能**:

```
┌─────────────────────────────────────────────────────┐
│  批次信息卡片                                        │
│  batch_001 | case_001 (成都绕城早高峰案例)          │
│  3方案 × 3种子 = 9任务 | 完成时间: 11:15 | 44分钟   │
│  [返回批量仿真] [导出详细报告▼]                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  详细对比表 (10+列)                                  │
│  [表格: 包含更多指标，综合得分]                      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  在网车辆峰值曲线（增强版）                          │
│  [Chart.js折线图: 支持缩放、导出]                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  多指标雷达图（5维）                                 │
│  [Radar Chart: 3个方案叠加显示]                      │
└─────────────────────────────────────────────────────┘
```

---

## 6. 性能优化

### 6.1 关键性能指标

| 操作 | 目标 | 策略 |
|------|------|------|
| 进度查询（缓存命中） | <50ms | 内存缓存 |
| 进度查询（缓存未命中） | <200ms | 增量解析 + 并发读取 |
| summary.xml解析 | <10ms/文件 | 增量解析 |
| 批次列表查询 | <300ms | 索引文件 |
| 批次删除 | <5s | 异步删除 |

### 6.2 优化策略

#### 6.2.1 缓存层次

```
Level 1: 内存缓存（TTL=5秒）
  - 批次进度数据
  - 批次列表数据

Level 2: 文件系统
  - batch_progress.json
  - batches_index.json

Level 3: 实时读取
  - summary.xml (仅在缓存过期时)
```

#### 6.2.2 并发控制

```python
# 并发读取多个summary.xml文件
import concurrent.futures

def get_batch_progress_parallel(batch_id: str) -> Dict:
    tasks = get_running_tasks(batch_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_get_simulation_live_status, task): task
            for task in tasks
        }

        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                task['live_status'] = future.result(timeout=1)
            except Exception as e:
                logger.warning(f"Failed to get live status for {task['task_id']}: {e}")
                task['live_status'] = {"error": "无法读取状态"}

    return tasks
```

---

## 7. 错误处理

### 7.1 常见错误场景

| 场景 | 处理策略 |
|------|----------|
| summary.xml不存在 | 返回`message: "仿真正在初始化..."`，不报错 |
| summary.xml解析失败 | 返回`error: "无法读取状态"`，记录警告日志 |
| 批次不存在 | 返回404错误 |
| 删除运行中批次 | 返回409错误，提示先取消 |
| 索引文件损坏 | 自动重建（扫描批次目录） |
| 缓存内存溢出 | 使用LRU淘汰，限制maxsize=100 |

### 7.2 降级策略

```
正常模式: 实时监控 + 缓存
  ↓ (summary.xml读取失败)
降级模式1: 仅显示任务状态（pending/running/completed）
  ↓ (批次元数据文件损坏)
降级模式2: 显示"数据加载失败，请刷新页面"
```

---

## 8. 安全考虑

### 8.1 文件访问控制

- 批次删除前验证batch_id格式（防止路径遍历攻击）
- 批次查询限制在当前case_id范围内
- 归档操作仅删除输出文件，保留配置文件

### 8.2 并发安全

- 索引文件更新使用文件锁（或原子写入）
- 缓存更新使用线程安全的数据结构（TTLCache）
- 批次删除操作加锁（避免同时删除）

---

## 9. 测试策略

### 9.1 单元测试重点

- summary.xml增量解析（正常、异常、边界）
- 剩余时间估算算法（不同进度阶段）
- 批次索引同步逻辑
- 缓存命中/未命中行为

### 9.2 集成测试重点

- 完整批量仿真流程（含实时监控）
- 批次管理流程（创建→查询→删除）
- 页面跳转流程（simulations.html ↔ optimization.html）

### 9.3 性能测试重点

- 60任务批次的进度查询响应时间
- 100个历史批次的列表查询性能
- 大文件summary.xml（>10MB）解析性能
- 频繁轮询（每10秒）的系统负载
- **不同仿真时长场景**：
  - 短时仿真（1-2小时）：简单管控策略
  - 中等仿真（2-6小时）：中等复杂度管控
  - 长时仿真（6-24小时）：复杂管控策略组合
  - **说明**：仿真时长取决于管控复杂度和策略配置

### 9.4 E2E测试重点

- 实时监控数据显示
- 批次历史视图交互
- 结果页面跳转和返回
- 图表渲染和导出

---

## 10. 未来扩展

### 10.1 短期（3个月内）

- [ ] WebSocket支持（替代轮询，实现真正的实时推送）
- [ ] 批次比较功能（对比不同批次的结果）
- [ ] 更多可视化（热力图、箱线图）

### 10.2 长期（6个月以上）

- [ ] 分布式批量仿真（跨多台服务器）
- [ ] 智能推荐（基于历史数据推荐最优方案）
- [ ] 移动端支持（响应式设计）

---

## 11. 参考资料

- 现有设计文档: `docs/design/traffic_control_optimization_overview.md`
- SUMO文档: summary.xml格式规范
- 现有实现: `api/services/batch_optimization_service.py`
- Chart.js文档: v4.4.0 API参考

---

## 12. 调试与故障排除 (2025-10-29)

### 12.1 车辆数和动态曲线不显示问题

**问题报告**：批量仿真进度页面UI已更新，但车辆数(`running_vehicles`)和动态曲线(`live_time_series`)未显示。

#### 12.1.1 诊断工具

**前端调试日志** (`frontend/control/js/batch_simulation.js`):
- `updateProgress()`: 添加API响应数据结构检查
- `renderLiveCurve()`: 追踪曲线渲染调用和数据点数量

**后端调试日志** (`api/services/batch_optimization_service.py`):
- `_get_simulation_live_status()`: 记录simulation_id分配状态、summary.xml文件存在性
- `_extract_summary_last_step()`: 追踪文件解析过程

**诊断脚本** (`debug_batch_progress.py`):
- 检查API响应数据结构
- 验证summary.xml文件存在性
- 输出完整JSON响应

#### 12.1.2 常见根因

1. **API服务器未重启** - 代码更新后需要重启API服务器才能生效
2. **simulation_id未分配** - 任务状态为running但仿真尚未启动
3. **summary.xml不存在** - SUMO刚启动，输出文件尚未生成（需等待10-30秒）
4. **文件路径错误** - plan_opti目录结构不正确
5. **解析失败** - summary.xml格式异常或文件损坏

#### 12.1.3 数据流追踪

**后端数据生成流程**：
```
get_batch_progress()
  ├─> 遍历running任务
  │   └─> _get_simulation_live_status()
  │       ├─> 检查simulation_id ❌ → 返回初始状态（无running_vehicles）
  │       ├─> 定位summary.xml
  │       │   └─> plan_opti/{batch_id}/{plan_id}/sim_{seed}/summary.xml
  │       ├─> _extract_summary_last_step() ❌ → 返回None
  │       │   ├─> 文件不存在 → 返回None
  │       │   └─> 解析失败 → 返回None
  │       └─> 返回live_status（包含running_vehicles） ✓
  │
  ├─> _aggregate_live_time_series()
  │   ├─> 过滤running任务 ❌ → 返回空数据
  │   ├─> 遍历任务，提取时序数据
  │   │   └─> _extract_summary_time_series()
  │   │       └─> 解析summary.xml全部<step>元素
  │   ├─> 汇总aggregated_data ❌ → 返回空数据
  │   └─> 返回{time_points, total_running} ✓
  │
  └─> 返回响应{tasks, live_time_series}
```

**前端渲染流程**：
```
updateProgress() [每10秒轮询]
  ├─> fetch API /batch/{id}/progress
  ├─> console.log API响应数据结构 [调试日志]
  ├─> renderTaskList(data.tasks)
  │   └─> 遍历running任务
  │       ├─> 检查task.live_status ❌ → 不显示车辆数
  │       └─> 显示: "在网: {running_vehicles}辆" ✓
  │
  └─> renderLiveCurve(data.live_time_series)
      ├─> console.log 数据结构 [调试日志]
      ├─> 检查time_points.length ❌ → 隐藏图表
      └─> 创建Chart.js曲线 ✓
```

#### 12.1.4 诊断流程

1. **重启API服务器** → `.\start_api.ps1`
2. **启动批量仿真** → 等待任务进入running状态
3. **检查浏览器控制台** (F12) → 查看调试日志输出
4. **运行诊断脚本** → `python debug_batch_progress.py <case_id> <batch_id>`
5. **检查API日志** → 查看DEBUG级别日志
6. **验证文件存在** → 检查summary.xml路径和大小

完整诊断指南: `BATCH_MONITORING_DEBUG_GUIDE.md`

#### 12.1.5 修复措施

- ✅ 前端添加调试日志（API响应、曲线渲染）
- ✅ 后端添加调试日志（文件定位、解析状态）
- ✅ 创建诊断脚本和指南
- ⏳ 等待用户运行诊断，提供具体输出结果
- 🔄 根据诊断结果进一步修复
