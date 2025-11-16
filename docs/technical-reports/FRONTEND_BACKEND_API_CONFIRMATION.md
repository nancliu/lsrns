# 前端批量创建按钮 - 后端调用链路确认

**确认日期**: 2025-11-15
**检查人**: Claude Code AI
**状态**: ✅ 调用链路正确

---

## 📍 快速概览

| 维度 | 详情 |
|------|------|
| **前端按钮位置** | `frontend/scenarios/scenario_browser.html` |
| **前端处理函数** | `batchCreateEventCase()` - `frontend/scenarios/scenario_browser.js:646` |
| **调用的API端点** | `POST /api/v1/scenario/create-case-batch` |
| **后端路由处理** | `create_event_case_batch()` - `api/routes/scenario_routes.py:405` |
| **后端服务方法** | `case_service.create_event_case_batch()` - `api/services/case_service.py:1670` |
| **调用状态** | ✅ 正确映射，符合规范 |

---

## 前端部分详解

### 1. HTML 按钮定义

**文件**: `frontend/scenarios/scenario_browser.html`
**位置**: 事件卡片中的按钮

```html
<button
    class="btn btn-primary"
    onclick="batchCreateEventCase('${event.event_id}')"
    title="批量创建选中的场景案例">
    批量创建
</button>
```

**位置**: `frontend/scenarios/scenario_browser.js:550-552`

---

### 2. JavaScript 处理函数

**文件**: `frontend/scenarios/scenario_browser.js`
**函数名**: `batchCreateEventCase(eventId)`
**行号**: 第646-761行

#### 函数流程

```
用户点击"批量创建"按钮
    ↓ 触发 batchCreateEventCase(eventId)
    ↓
步骤1: 获取用户勾选的场景 (第647行)
    - 查询: .scenario-checkbox[data-event-id="${eventId}"]:checked
    - 验证: 至少选择一个场景

    ↓
步骤2: 提取场景参数 (第671-675行)
    - 调用: extractScenarioParameters(scenario)
    - 获取: 每个场景的仿真参数、策略、时间等

    ↓
步骤3: 显示确认对话框 (第681-691行)
    - 显示: 事件ID、事件类型、场景数量、策略列表
    - 等待: 用户点击"确定"继续

    ↓
步骤4: 构建请求数据 (第696-710行)
    ├─ event_id: 事件ID
    ├─ event_type: 事件类型（如"01_accident"）
    ├─ scenarios: 所有场景的参数数组
    ├─ network_file: "templates/network_files/sichuan202508v7.net.xml"
    ├─ od_file: "dwd.dwd_od_weekly"
    ├─ taz_file: "templates/taz_files/TAZ_6.add.xml"
    ├─ time_range:
    │   ├─ start_time: 仿真开始时间（OD时间范围）
    │   └─ end_time: 仿真结束时间（OD时间范围）
    ├─ simulation_type: "microscopic"
    └─ random_seed: null

    ↓
步骤5: 发送 API 请求 (第713-719行)
    POST /api/v1/scenario/create-case-batch
    Headers: Content-Type: application/json
    Body: JSON.stringify(requestData)

    ↓
步骤6: 处理响应 (第721-755行)
    ├─ 成功响应 (200):
    │   ├─ 显示成功消息
    │   ├─ 显示 case_id, 场景成功/失败数
    │   ├─ 显示 EdgeData 信息
    │   └─ 刷新案例列表
    │
    └─ 失败响应:
        └─ 显示错误消息并记录
```

---

### 3. 关键参数提取

从 **extractScenarioParameters()** 提取的场景参数：

```javascript
{
    scenario_id: "scenario_10754_vss",
    event_id: "10754",
    event_type: "01_accident",
    strategy: "VSS",           // 或 "NO_CONTROL", "TEC", "DHS"
    event_location: {
        edge_id: "3026",
        edge_name: "高速公路A段"
    },
    control_strategy: {        // 如果有策略
        strategy_type: "VSS",
        parameters: {...}
    },
    output_config: {
        generate_summary: true,
        generate_edgedata: true,
        generate_tripinfo: false,  // ← 已禁用（P1修复）
        generate_vehroute: false
    },
    time: {
        sim_start_time: "06:00:00",     // OD开始时间（事件前30分钟）
        sim_end_time: "09:00:00",       // OD结束时间（事件后30分钟）
        sim_duration_hours: 2.5         // 场景仿真时长（小时）
    },
    road: "成都市绕城高速",
    event_type_display: "交通事故"
}
```

---

## 后端部分详解

### 1. API 路由定义

**文件**: `api/routes/scenario_routes.py`
**路由**: `POST /api/v1/scenario/create-case-batch`
**处理函数**: `create_event_case_batch()`
**行号**: 第404-465行

```python
@router.post("/create-case-batch", response_model=EventCaseBatchCreationResponse)
async def create_event_case_batch(request: CreateEventCaseBatchRequest):
    """
    批量创建事件案例
    - 在一个case下创建多个simulations（每个场景一个）
    - 聚合事件和策略的影响边缘，生成统一的edgeData.add.xml
    """
    try:
        from ..services.case_service import case_service

        result = await case_service.create_event_case_batch(request)

        logger.info(f"✓ 批量创建成功: event={request.event_id}, "
                    f"scenarios={result['successful_scenarios']}/{result['total_scenarios']}")

        return EventCaseBatchCreationResponse(**result)

    except Exception as e:
        logger.error(f"✗ 批量创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建失败: {str(e)}")
```

---

### 2. 服务层处理

**文件**: `api/services/case_service.py`
**方法**: `create_event_case_batch()`
**行号**: 第1670-2000+ 行

#### 处理流程

```
case_service.create_event_case_batch(request)
    ↓
步骤1: 验证请求和初始化 (第1670-1740行)
    ├─ 验证event_id, scenarios非空
    ├─ 创建case目录
    ├─ 准备配置目录

    ↓
步骤2: 生成EdgeData配置 (第1740-1772行)
    ├─ 调用: generate_edgedata_xml_for_case()
    ├─ 提取: event_location (事件边缘)
    ├─ 提取: strategies (策略边缘)
    ├─ 获取: 智能决策信息 (should_enable)

    ↓
步骤3: 初始化案例元数据 (第1815-1846行)
    ├─ case_id: case_event_{event_id}  ← P1修复（使用event_id）
    ├─ source_type: event_scenario_batch
    ├─ event_scenario: event_id, event_type
    ├─ case_config: network_file, od_file, taz_file, time_range

    ↓
步骤4: 为每个场景创建仿真 (第1853-1975行)
    对每个scenario:
        ├─ 生成simulation_id: sim_{scenario_id}
        ├─ 创建仿真目录
        ├─ 复制策略文件
        ├─ 复制EdgeData文件
        ├─ 复制TAZ文件
        ├─ 设置output_config
        │  ├─ generate_tripinfo: false  ← P1修复（禁用tripinfo）
        │  ├─ generate_edgedata: 根据智能决策  ← P2改进（智能决策）
        │  └─ ...
        ├─ 构建simulation_params
        │  ├─ duration_hours: 从scenario提取  ← P1修复（时长解析）
        │  └─ ...
        ├─ 调用: generate_sumocfg_for_simulation()
        │  ├─ 检查: simulation_params['duration_hours']
        │  ├─ 备用: case_metadata['case_config']['time_range']
        │  ├─ 计算: 正确的仿真时长
        │  └─ 生成: simulation.sumocfg
        ├─ 写入: simulation_metadata.json
        └─ 记录: 成功/失败状态

    ↓
步骤5: 收集结果并返回 (第1976-2000+行)
    ├─ successful_scenarios: 成功数
    ├─ failed_scenarios: 失败数
    ├─ total_scenarios: 总数
    ├─ case_id: 案例ID
    ├─ event_id: 事件ID
    ├─ edgedata_info: EdgeData信息
    │  ├─ edge_count
    │  ├─ validation_rate
    │  ├─ should_enable  ← 智能决策结果
    │  └─ ...
    ├─ scenario_results: 各场景的创建结果
    └─ duration_seconds: 执行耗时
```

---

## 完整的调用链路图

```
┌─────────────────────────────────────┐
│   前端 (scenario_browser.html)      │
│  点击"批量创建"按钮                  │
└─────────────────┬───────────────────┘
                  │
                  │ onclick="batchCreateEventCase(eventId)"
                  ↓
┌─────────────────────────────────────┐
│  JavaScript: batchCreateEventCase()  │ (line 646-761)
│  - 获取选中场景                      │
│  - 提取参数                          │
│  - 显示确认对话框                    │
│  - 构建请求数据                      │
└─────────────────┬───────────────────┘
                  │
                  │ POST /api/v1/scenario/create-case-batch
                  │ Content-Type: application/json
                  │ Body: {
                  │   event_id, event_type, scenarios[],
                  │   network_file, od_file, taz_file,
                  │   time_range, simulation_type
                  │ }
                  ↓
┌──────────────────────────────────────┐
│  后端路由: scenario_routes.py:404    │
│  @router.post("/create-case-batch")  │
│  def create_event_case_batch()       │ (line 405-465)
│  - 验证请求                          │
│  - 调用case_service                  │
└────────────────┬─────────────────────┘
                 │
                 │ await case_service.create_event_case_batch(request)
                 ↓
┌──────────────────────────────────────┐
│  后端服务: case_service.py:1670      │
│  async def create_event_case_batch() │
│                                      │
│  核心逻辑:                           │
│  1. EdgeData生成 + 智能决策 (P2)    │
│  2. case_id 格式化 (P1)             │
│  3. tripinfo 禁用 (P1)              │
│  4. 时长解析修复 (P1)                │
│  5. 元数据初始化                     │
│  6. 逐个创建仿真                     │
│  7. 返回批量结果                     │
└────────────────┬─────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────┐
│  返回响应: EventCaseBatchCreationResponse
│  {                                   │
│    case_id: "case_event_10754",     │
│    event_id: "10754",                │
│    successful_scenarios: 3,          │
│    total_scenarios: 3,               │
│    failed_scenarios: 0,              │
│    edgedata_info: {...},             │
│    scenario_results: [...],          │
│    duration_seconds: 12.34           │
│  }                                   │
└──────────────────────────────────────┘
                 │
                 ↓ HTTP 200 OK
┌──────────────────────────────────────┐
│  前端: 处理响应 (line 721-750)       │
│  - 显示成功消息                      │
│  - 刷新案例列表                      │
│  - 显示创建结果详情                  │
└──────────────────────────────────────┘
```

---

## 关键修复在调用链路中的位置

### P1 修复1: Case ID 命名规范

**位置**: `api/services/case_service.py:1699`

```python
# 修复前: 时间戳格式
case_id = self.generate_unique_id("case_event")  ❌

# 修复后: event_id格式
case_id = f"case_event_{request.event_id}"  ✅
```

**影响**: 前端创建时指定 event_id，后端直接使用 → case_event_10754 格式

---

### P1 修复2: Tripinfo 输出禁用

**位置**: `api/services/case_service.py:1900-1901`

```python
# 强制禁用tripinfo输出（事件仿真不需要）
event_output_config = scenario.output_config.copy() if scenario.output_config else {}
event_output_config["generate_tripinfo"] = False  ✅
```

**影响**: 即使前端的 output_config 中有 generate_tripinfo: true，也会被覆盖为 false

---

### P2 改进1: EdgeData 智能决策

**位置**: `api/services/case_service.py:1750-1772`

```python
# 生成EdgeData并获取智能决策
edgedata_result = generate_edgedata_xml_for_case(...)
edgedata_decision = edgedata_result.get('edgedata_decision', {})
should_enable_edgedata = edgedata_decision.get('should_enable', True)

# 根据决策自动配置输出
if edgedata_info and isinstance(edgedata_info, dict):
    should_enable = edgedata_info.get("should_enable", True)
    event_output_config["generate_edgedata"] = should_enable  ✅
```

**影响**: EdgeData 生成后，自动根据质量（边缘数、验证率）决定是否输出

---

### P1 修复3: 仿真时长解析

**位置**: `api/services/case_service.py:1913-1918`

```python
# 从scenario提取duration_hours
simulation_params = {
    "duration_hours": scenario.time.get('sim_duration_hours', 2.5),  ✅
    ...
}

# 后端调用generate_sumocfg_for_simulation时传递
sumocfg_content = generate_sumocfg_for_simulation(
    ...
    simulation_params=simulation_params  # 包含duration_hours
)
```

**时长计算** (`shared/utilities/sumo_utils.py:485-530`):
```python
# 优先级1: 使用传入的duration_hours
if simulation_params.get('duration_hours'):
    duration = int(simulation_params['duration_hours'] * 3600)  ✅

# 优先级2: 计算case_metadata.case_config.time_range
elif 'case_config' in case_metadata and 'time_range' in case_metadata['case_config']:
    duration = int((end_dt - start_dt).total_seconds())  ✅

# 优先级3: 默认值
else:
    duration = 3600
```

**影响**: 前端传递的 sim_duration_hours 直接用于sumocfg生成 → 仿真时长正确

---

## 请求数据结构确认

### 前端发送的请求

```javascript
{
    "event_id": "10754",
    "event_type": "01_accident",
    "scenarios": [
        {
            "scenario_id": "scenario_10754_no_control",
            "event_id": "10754",
            "event_type": "01_accident",
            "strategy": "NO_CONTROL",
            "event_location": {
                "edge_id": "3026",
                "edge_name": "..."
            },
            "output_config": {
                "generate_summary": true,
                "generate_edgedata": true,
                "generate_tripinfo": false,
                ...
            },
            "time": {
                "sim_start_time": "06:00:00",
                "sim_end_time": "09:00:00",
                "sim_duration_hours": 2.5
            },
            ...
        },
        // ... 更多场景
    ],
    "network_file": "templates/network_files/sichuan202508v7.net.xml",
    "od_file": "dwd.dwd_od_weekly",
    "taz_file": "templates/taz_files/TAZ_6.add.xml",
    "time_range": {
        "start_time": "06:00:00",
        "end_time": "09:00:00"
    },
    "simulation_type": "microscopic",
    "random_seed": null
}
```

### 后端返回的响应

```json
{
    "case_id": "case_event_10754",
    "event_id": "10754",
    "successful_scenarios": 3,
    "failed_scenarios": 0,
    "total_scenarios": 3,
    "edgedata_info": {
        "file_path": "cases/case_event_10754/config/edgeData.add.xml",
        "edge_count": 120,
        "event_edges": 2,
        "strategy_edges": 118,
        "validation_rate": 0.95,
        "should_enable": true
    },
    "scenario_results": [
        {
            "scenario_id": "scenario_10754_no_control",
            "simulation_id": "sim_scenario_10754_no_control",
            "success": true
        },
        ...
    ],
    "duration_seconds": 12.34
}
```

---

## 调用路径验证矩阵

| 步骤 | 前端 | 后端路由 | 后端服务 | 数据 | 修复 | 状态 |
|------|------|---------|--------|------|------|------|
| 1 | 点击批量创建按钮 | - | - | event_id | - | ✅ |
| 2 | 构建请求 | scenario_browser.js:696-710 | - | scenarios[], network_file, od_file, taz_file, time_range | - | ✅ |
| 3 | 发送API | POST /api/v1/scenario/create-case-batch | scenario_routes.py:404 | CreateEventCaseBatchRequest | - | ✅ |
| 4 | 路由处理 | - | create_event_case_batch() | request | - | ✅ |
| 5 | 调用服务 | - | case_service.create_event_case_batch() | request | - | ✅ |
| 6 | 生成EdgeData | - | 1750-1772 | scenarios | P2智能决策 | ✅ |
| 7 | 设置case_id | - | 1699 | event_id | P1命名规范 | ✅ |
| 8 | 禁用tripinfo | - | 1900-1901 | output_config | P1禁用tripinfo | ✅ |
| 9 | 提取时长 | 前端time.sim_duration_hours | 1913-1918 | duration_hours | P1时长解析 | ✅ |
| 10 | 生成sumocfg | - | sumo_utils:485-530 | simulation_params | P1时长优先级 | ✅ |
| 11 | 返回响应 | - | EventCaseBatchCreationResponse | case_id, scenarios结果, edgedata_info | - | ✅ |
| 12 | 显示结果 | scenario_browser.js:721-750 | - | 响应数据 | - | ✅ |

---

## 最终确认

### ✅ 前端调用链路

| 项目 | 值 |
|------|-----|
| 按钮位置 | `frontend/scenarios/scenario_browser.html` |
| 按钮HTML | `<button onclick="batchCreateEventCase('...')">批量创建</button>` |
| 处理函数 | `batchCreateEventCase()` - `scenario_browser.js:646-761` |
| API方法 | `fetch(..., { method: 'POST', ... })` |
| 请求URL | `/api/v1/scenario/create-case-batch` |
| 请求头 | `Content-Type: application/json` |
| 请求体 | CreateEventCaseBatchRequest |

### ✅ 后端调用链路

| 项目 | 值 |
|------|-----|
| 路由定义 | `api/routes/scenario_routes.py:404` |
| 路由处理 | `@router.post("/create-case-batch")` |
| 处理函数 | `create_event_case_batch()` - `scenario_routes.py:405-465` |
| 服务调用 | `case_service.create_event_case_batch(request)` |
| 服务位置 | `api/services/case_service.py:1670+` |
| 返回类型 | `EventCaseBatchCreationResponse` |

### ✅ 关键修复应用

| 修复 | 前端 | 后端 | 状态 |
|------|------|------|------|
| Case ID 规范化 | ✅ 前端传递 event_id | ✅ case_service:1699 使用 event_id | ✅ 已应用 |
| Tripinfo 禁用 | ✅ 前端配置 | ✅ case_service:1900-1901 强制禁用 | ✅ 已应用 |
| EdgeData 智能决策 | ✅ 前端显示 | ✅ case_service:1750-1772 自动决策 | ✅ 已应用 |
| 时长解析 | ✅ 前端传递 sim_duration_hours | ✅ sumo_utils:485-530 优先使用 | ✅ 已应用 |

---

## 总结

✅ **前端批量创建按钮调用链路确认完成**

### 调用路径
```
前端"批量创建"按钮
  → batchCreateEventCase(eventId)
  → POST /api/v1/scenario/create-case-batch
  → scenario_routes.py:create_event_case_batch()
  → case_service.create_event_case_batch()
  → 返回 EventCaseBatchCreationResponse
```

### 端点信息
- **HTTP方法**: POST
- **完整URL**: `/api/v1/scenario/create-case-batch`
- **请求类型**: CreateEventCaseBatchRequest
- **响应类型**: EventCaseBatchCreationResponse

### 服务方法
- **文件**: `api/services/case_service.py`
- **方法**: `create_event_case_batch()`
- **行号**: 第1670+行

### P1/P2修复的集成

| 修复项 | 应用位置 | 状态 |
|--------|---------|------|
| Case ID 命名 | case_service:1699 | ✅ 已应用 |
| Tripinfo 禁用 | case_service:1900-1901 | ✅ 已应用 |
| EdgeData 智能决策 | case_service:1750-1772 | ✅ 已应用 |
| 时长解析修复 | sumo_utils:485-530 | ✅ 已应用 |

**所有修复都已正确集成到批量创建流程中！** ✅

