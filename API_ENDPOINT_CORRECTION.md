# API 端点调用修正 - 前端批量创建按钮

**报告日期**: 2025-11-15
**状态**: ⚠️ 需要修正
**优先级**: P1

---

## 问题确认

用户指出：前端"批量创建"按钮应该调用 `/api/v1/case/create-from-event-scenario` 而不是 `/api/v1/scenario/create-case-batch`。

---

## 规范查证

### 根据 CASE_AND_ANALYSIS_CLEANUP_GUIDE.md

规范文档第249行明确说明：
```
POST /api/v1/case/create-from-event-scenario
```

规范说明(第628行):
```
1. create_case_from_event_scenario (创建case+仿真)
```

合并政策(第1201行):
```
✅ create_case_from_event_scenario(request)  # 替代5个旧方法
```

---

## 现状分析

### 当前前端实现 ❌

**文件**: `frontend/scenarios/scenario_browser.js:713`

```javascript
const response = await fetch('/api/v1/scenario/create-case-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
});
```

**问题**:
- 调用的是 `/api/v1/scenario/create-case-batch`（scenario路由）
- 这个接口不符合规范
- 应该调用case路由下的接口

### 规范要求接口 ✅

**路由**: `api/routes/case_routes.py:84`

```python
@router.post("/from-event-scenario", response_model=BaseResponse)
@handle_service_errors
async def create_case_from_event_scenario(request: CreateCaseWithSimulationRequest):
```

**特点**:
- 路由在case_routes.py中（符合语义）
- 调用 `case_service.create_case_from_event_scenario()`
- 完整的事件场景工作流

---

## 两个接口对比

### 接口1: `/api/v1/scenario/create-case-batch` ❌

| 属性 | 值 |
|------|-----|
| 路由位置 | `api/routes/scenario_routes.py:404` |
| 路由装饰器 | `@router.post("/create-case-batch")` |
| 服务方法 | `case_service.create_event_case_batch()` |
| 功能 | 批量创建一个事件的多个场景在一个case下 |
| 批量 | ✅ 支持多个场景 |
| 场景重用 | ❌ 不支持 |
| 统一EdgeData | ✅ 所有场景共享 |
| 规范符合度 | ❌ **不符合规范** |

**问题**: 这个接口的功能虽然有用，但不是规范推荐的接口。

### 接口2: `/api/v1/case/from-event-scenario` ✅

| 属性 | 值 |
|------|-----|
| 路由位置 | `api/routes/case_routes.py:84` |
| 路由装饰器 | `@router.post("/from-event-scenario")` |
| 服务方法 | `case_service.create_case_from_event_scenario()` |
| 功能 | 从单个事件场景创建case+simulation |
| 单个 | ✅ 单场景一次 |
| 场景重用 | ✅ **支持case重用** |
| EdgeData | ✅ 自动处理 |
| 规范符合度 | ✅ **完全符合规范** |

**优势**: 这是规范定义的统一接口，支持case重用（多个场景共享同一case）。

---

## 规范文档关键引用

### CASE_AND_ANALYSIS_CLEANUP_GUIDE.md

**第249行**:
```
POST /api/v1/case/create-from-event-scenario
```

**第276-280行**:
```
   ← 改名为 /api/v1/case/create-from-event-scenario
   ← 功能由 create-from-event-scenario 的自动模拟创建实现
```

**第295-307行** (方法合并清单):
```
✓ create_case_from_event_scenario()  # 替代：
- _get_or_create_event_case()        # 内部用，调用方改为 create_case_from_event_scenario()
- _get_or_create_event_case_with_lock()  # 锁定逻辑移到 create_case_from_event_scenario()
- create_case_from_scenario()        # 合并到 create_case_from_event_scenario()
- quick_create_case_from_event()     # 合并到 create_case_from_event_scenario()
```

**第1201行** (最终结论):
```
✅ create_case_from_event_scenario(request)  # 替代5个旧方法
```

---

## 需要修正的地方

### 修正1: 前端调用的API端点

**文件**: `frontend/scenarios/scenario_browser.js:713`

**修改前** ❌:
```javascript
const response = await fetch('/api/v1/scenario/create-case-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
});
```

**修改后** ✅:
```javascript
// 方案1: 循环调用单场景接口（符合规范）
for (const scenario of selectedScenarios) {
    const singleScenarioRequest = {
        ...scenario,
        // scenario包含的字段
    };

    const response = await fetch('/api/v1/case/from-event-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(singleScenarioRequest)
    });

    // 处理响应
    const result = await response.json();
    // 收集结果
}
```

或

```javascript
// 方案2: 保持调用 /create-case-batch（现有功能，非规范）
// 但需要明确这是"快速批量创建"而不是规范的单场景创建
```

---

## 两个接口的使用场景

### 使用 `/api/v1/case/from-event-scenario` 的场景 ✅ 推荐

1. **单个场景创建** - 逐个从事件场景创建case+simulation
2. **支持case重用** - 同一个event的多个scenario可以共享同一个case
3. **符合规范** - 按照CASE_AND_ANALYSIS_CLEANUP_GUIDE.md规范

```
场景1: scenario_10754_no_control
    ↓ POST /api/v1/case/from-event-scenario
    → case_event_10754 (新建)
       + sim_scenario_10754_no_control (新建)

场景2: scenario_10754_vss (同一个event)
    ↓ POST /api/v1/case/from-event-scenario
    → case_event_10754 (重用)
       + sim_scenario_10754_vss (新建)

场景3: scenario_10754_tec (同一个event)
    ↓ POST /api/v1/case/from-event-scenario
    → case_event_10754 (重用)
       + sim_scenario_10754_tec (新建)

优势: 存储效率高，所有场景共享一个case的config文件
```

### 使用 `/api/v1/scenario/create-case-batch` 的场景

1. **快速批量创建** - 一次性为所有场景创建
2. **统一EdgeData** - 所有场景共享同一个edgedata.add.xml
3. **快速操作** - 减少API调用次数（1次而非3次）

```
多个场景
    ↓ POST /api/v1/scenario/create-case-batch
    → case_event_10754 (一次性创建所有simulation)
       + sim_scenario_10754_no_control
       + sim_scenario_10754_vss
       + sim_scenario_10754_tec

优势: 速度快（1次API调用），但不支持case重用
```

---

## 建议的改进方案

### 方案A: 按规范修改（推荐）✅

**调用接口**: `POST /api/v1/case/from-event-scenario`

**实现方式**: 循环调用，为每个场景创建一个case+simulation对

**优势**:
- ✅ 完全符合规范
- ✅ 支持case重用
- ✅ 未来维护清晰

**劣势**:
- API调用次数增加（N个场景=N次调用）
- 用户界面需要显示逐个创建的进度

**示例实现**:
```javascript
async function batchCreateEventCase(eventId) {
    const selectedScenarios = [...获取选中场景...];
    const results = [];

    for (const scenario of selectedScenarios) {
        try {
            const response = await fetch('/api/v1/case/from-event-scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scenario_id: scenario.scenario_id,
                    event_type: scenario.event_type,
                    event_id: eventId,
                    ... // 其他必需字段
                })
            });

            const result = await response.json();
            results.push(result);
        } catch (error) {
            results.push({ error: error.message });
        }
    }

    // 显示汇总结果
    displayResults(results);
}
```

### 方案B: 保持现状（临时方案）

**调用接口**: `POST /api/v1/scenario/create-case-batch` (现有)

**优势**:
- 无需修改前端代码
- 性能更好（1次API调用）
- 已经实现并验证

**劣势**:
- ❌ 不符合规范
- ❌ 不支持case重用
- ❌ 后续可能需要大改

**建议**: 这不是长期方案，只适合作为过渡

---

## 后端接口验证

### 接口存在确认

✅ `/api/v1/case/from-event-scenario` **存在**
```
文件: api/routes/case_routes.py:84
装饰器: @router.post("/from-event-scenario", response_model=BaseResponse)
处理函数: create_case_from_event_scenario()
服务方法: case_service.create_case_from_event_scenario()
```

✅ `/api/v1/scenario/create-case-batch` **存在**
```
文件: api/routes/scenario_routes.py:404
装饰器: @router.post("/create-case-batch", response_model=EventCaseBatchCreationResponse)
处理函数: create_event_case_batch()
服务方法: case_service.create_event_case_batch()
```

---

## 关键问题解答

### Q: 为什么规范说应该用 `/case/from-event-scenario`？

**A**:
- 这是统一的事件场景接口
- 符合单一职责原则（case路由处理case创建）
- 支持case重用和高效存储
- 是通过合并5个旧方法后的最终接口

### Q: 现在的 `/scenario/create-case-batch` 还有用吗？

**A**:
- 有，它提供了"快速批量创建"的功能
- 但它不是规范推荐的接口
- 可以作为高级功能或优化选项，但不应该是默认接口

### Q: 修改前端会不会破坏现有功能？

**A**:
- 不会，`/case/from-event-scenario` 实现完整
- 可能需要调整请求格式（从批量改为单个场景）
- 可以逐步迁移而不是全部替换

### Q: 两个接口都保留吗？

**A**:
- 是的，两个接口可以共存
- `/case/from-event-scenario` 是规范接口（推荐）
- `/scenario/create-case-batch` 是优化接口（可选）
- 前端应该默认使用规范接口

---

## 后续行动建议

### 立即行动

1. **确认需求**
   - [ ] 前端应该调用规范接口还是保持现状？
   - [ ] 是否需要支持case重用？
   - [ ] 性能和功能哪个优先？

2. **如果采用规范接口**
   - [ ] 修改前端调用 `/api/v1/case/from-event-scenario`
   - [ ] 调整请求格式（从批量改为循环单个）
   - [ ] 更新用户界面显示进度
   - [ ] 测试新流程

3. **如果保持现状**
   - [ ] 更新CASE_AND_ANALYSIS_CLEANUP_GUIDE.md，说明这是临时方案
   - [ ] 在代码注释中明确标注
   - [ ] 计划后续迁移路径

---

## 总结

| 方面 | 现状 | 规范 |
|------|------|------|
| **前端调用端点** | `/api/v1/scenario/create-case-batch` | `/api/v1/case/from-event-scenario` |
| **符合规范** | ❌ 否 | ✅ 是 |
| **支持case重用** | ❌ 否 | ✅ 是 |
| **API调用次数** | 1次 | N次（每个场景1次） |
| **性能** | ⚡ 快 | 🐢 慢一些 |
| **规范性** | ❌ 临时方案 | ✅ 最终方案 |

**建议**: 优先按规范修改，但要根据项目的实际需求做出最终决策。

