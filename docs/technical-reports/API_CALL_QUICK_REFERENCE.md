# 批量创建 API 调用 - 快速参考

**生成日期**: 2025-11-15

---

## 一句话总结

前端"批量创建"按钮 → 调用 `batchCreateEventCase()` → 发送 `POST /api/v1/scenario/create-case-batch` → 后端调用 `case_service.create_event_case_batch()`

---

## 前端调用信息

### 按钮位置
```
文件: frontend/scenarios/scenario_browser.html
HTML: <button onclick="batchCreateEventCase('${event.event_id}')">批量创建</button>
```

### 处理函数
```
文件: frontend/scenarios/scenario_browser.js
函数: batchCreateEventCase(eventId)
行号: 646-761行
```

### API 调用
```javascript
// 第713行
const response = await fetch('/api/v1/scenario/create-case-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
});
```

---

## 后端接口信息

### 路由定义
```
文件: api/routes/scenario_routes.py
行号: 404-465行
```

### 路由信息
```python
@router.post("/create-case-batch", response_model=EventCaseBatchCreationResponse)
async def create_event_case_batch(request: CreateEventCaseBatchRequest):
    # 调用: case_service.create_event_case_batch(request)
    pass
```

### 服务方法
```
文件: api/services/case_service.py
方法: async def create_event_case_batch(request: CreateEventCaseBatchRequest)
行号: 1670行起
```

---

## 请求参数

### 必需参数
```javascript
{
    "event_id": "10754",                    // 事件ID
    "event_type": "01_accident",            // 事件类型
    "scenarios": [                          // 场景数组
        {
            "scenario_id": "scenario_10754_vss",
            "time": {
                "sim_duration_hours": 2.5   // ← 仿真时长（小时）
            },
            // ... 其他场景参数
        }
    ],
    "network_file": "templates/...",        // 网络文件
    "od_file": "dwd.dwd_od_weekly",        // OD数据表
    "taz_file": "templates/...",           // TAZ文件
    "time_range": {                         // 时间范围
        "start_time": "06:00:00",
        "end_time": "09:00:00"
    },
    "simulation_type": "microscopic",       // 仿真类型
    "random_seed": null                     // 随机种子
}
```

---

## 响应参数

### 成功响应 (HTTP 200)
```javascript
{
    "case_id": "case_event_10754",           // ← P1修复：使用event_id
    "event_id": "10754",
    "successful_scenarios": 3,
    "failed_scenarios": 0,
    "total_scenarios": 3,
    "edgedata_info": {
        "edge_count": 120,
        "validation_rate": 0.95,
        "should_enable": true                // ← P2改进：智能决策
    },
    "scenario_results": [...],
    "duration_seconds": 12.34
}
```

### 失败响应 (HTTP 500)
```javascript
{
    "detail": "批量创建失败: 错误详情"
}
```

---

## 关键修复对应位置

### P1 修复1: Case ID 命名规范 ✅
```
后端位置: api/services/case_service.py:1699
修改: case_id = f"case_event_{request.event_id}"
结果: case_event_10754 （而非 case_event_20251115_213819）
```

### P1 修复2: Tripinfo 禁用 ✅
```
后端位置: api/services/case_service.py:1900-1901
修改: event_output_config["generate_tripinfo"] = False
结果: 事件仿真不输出tripinfo.xml
```

### P2 改进: EdgeData 智能决策 ✅
```
后端位置: api/services/case_service.py:1750-1772
逻辑: 根据edge_count和validation_rate自动决定是否输出edgedata
结果: 低质量EdgeData自动禁用，节省资源
```

### P1 修复3: 仿真时长解析 ✅
```
后端位置1: api/services/case_service.py:1913-1918
修改: simulation_params 包含 duration_hours

后端位置2: shared/utilities/sumo_utils.py:485-530
逻辑: 优先使用duration_hours，备用time_range，默认3600秒
结果: 仿真时长从scenario.sim_duration_hours正确推导
```

---

## API 端点总结表

| 方面 | 详情 |
|------|------|
| **HTTP方法** | POST |
| **端点路径** | `/api/v1/scenario/create-case-batch` |
| **完整URL** | `http://localhost:8000/api/v1/scenario/create-case-batch` |
| **前端调用** | `fetch('/api/v1/scenario/create-case-batch', {...})` |
| **后端路由文件** | `api/routes/scenario_routes.py:404` |
| **后端处理函数** | `create_event_case_batch()` (line 405) |
| **调用的服务** | `case_service.create_event_case_batch()` |
| **服务文件位置** | `api/services/case_service.py:1670+` |
| **请求模型** | `CreateEventCaseBatchRequest` |
| **响应模型** | `EventCaseBatchCreationResponse` |
| **成功状态码** | 200 |
| **错误状态码** | 500 |

---

## 流程图

```
┌─ 前端(scenario_browser.js)
│  ├─ 按钮onclick → batchCreateEventCase(eventId)
│  ├─ 获取选中场景
│  ├─ 提取参数 (包含 sim_duration_hours)
│  ├─ 构建请求体
│  └─ POST /api/v1/scenario/create-case-batch
│
└─ 后端(scenario_routes.py + case_service.py)
   ├─ 接收请求 @router.post("/create-case-batch")
   ├─ 调用 case_service.create_event_case_batch()
   ├─ 处理核心逻辑:
   │  ├─ EdgeData生成+智能决策 (P2)
   │  ├─ case_id格式化 (P1)
   │  ├─ tripinfo禁用 (P1)
   │  ├─ 时长解析 (P1)
   │  └─ 逐个创建仿真
   └─ 返回 EventCaseBatchCreationResponse (case_id, scenarios结果等)
```

---

## 修复验证清单

```
[✅] Case ID使用event_id而非时间戳
[✅] Tripinfo在event仿真中被禁用
[✅] EdgeData根据质量自动决定是否输出
[✅] 仿真时长从scenario.sim_duration_hours正确推导
[✅] 所有修复都集成在批量创建流程中
[✅] 前端和后端的调用链路一致
```

---

## 常见问题

### Q: 如果前端发送的time_range和scenario的sim_duration_hours不一致怎么办？
**A**: 优先使用scenario的sim_duration_hours（更准确）。time_range用作备用。

### Q: 为什么tripinfo被强制禁用？
**A**: Phase 2分析仅需summary.xml + edgedata.xml，tripinfo会浪费存储空间。

### Q: EdgeData决策的标准是什么？
**A**: 需要同时满足两个条件：
  - edge_count ≥ 10 条
  - validation_rate ≥ 50%

### Q: Case ID的格式是什么？
**A**: `case_event_{event_id}`，如 `case_event_10754`

---

## 部署验证

部署后，可以用以下命令验证：

```bash
# 1. 检查后端是否正常运行
curl -X GET http://localhost:8000/docs

# 2. 查看API文档中的/api/v1/scenario/create-case-batch端点

# 3. 创建一个测试事件案例
curl -X POST http://localhost:8000/api/v1/scenario/create-case-batch \
  -H "Content-Type: application/json" \
  -d @request.json

# 4. 验证返回结果中的case_id格式
```

---

**生成日期**: 2025-11-15
**版本**: Phase 1 Complete (P1 + P2)
**状态**: ✅ 就绪

