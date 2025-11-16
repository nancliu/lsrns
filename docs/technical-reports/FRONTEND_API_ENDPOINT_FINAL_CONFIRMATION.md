# 前端批量创建按钮 API 调用 - 最终确认报告

**报告日期**: 2025-11-15
**确认状态**: ✅ 已根据规范文档确认
**文件**: `openspec/changes/event-scenario-simulation-integration/CASE_AND_ANALYSIS_CLEANUP_GUIDE.md`
**结论**: 🔴 前端调用的接口**不符合规范**

---

## 核心发现

### ❌ 当前前端实现（错误）

**文件**: `frontend/scenarios/scenario_browser.js:713`

```javascript
const response = await fetch('/api/v1/scenario/create-case-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
});
```

**问题**:
- ❌ 调用 `/api/v1/scenario/create-case-batch` 接口
- ❌ 规范文档中**未提及**这个接口
- ❌ 属于非规范的快速批量实现
- ❌ 会导致后续维护困难

---

### ✅ 规范要求的接口

根据 `CASE_AND_ANALYSIS_CLEANUP_GUIDE.md` **第249行**：

```
POST /api/v1/case/create-from-event-scenario
```

**规范描述** (第249-267行):
```
# 2. 从场景创建（整合 Phase 2 和 Phase 5.3.3）
POST /api/v1/case/create-from-event-scenario
  Request:
    - scenario_id: 场景ID（例: scenario_10814_vss）
    - simulation_duration_hours: 仿真时长（小时）
    - output_config: 输出配置（可选）
  Response: {
    case_id: "case_event_{event_id}",
    case_type: "event_based",
    simulation_id: "event_simulation_scenario_{scenario_id}",
    metadata,
    status: "case_created_with_scenario"
  }
  用途: 事件场景工作流，从场景快速创建案例和仿真
```

---

## 规范架构（完整工作流）

根据规范文档 **第628-637行** 的"事件工作流架构"：

```
1. create_case_from_event_scenario (创建case+仿真)
   ↓ [逐个场景循环调用此接口]

2. event-simulation/batch-start (启动批次)
   ↓ [批量启动创建好的仿真]

3. event-simulation/batch-results (获取仿真结果)
   ↓ [查询仿真结果]

4. event-simulation-analysis/run-comparison (对比分析)
   ↓ [对比不同策略的效果]

5. event-simulation-analysis/results (分析报告)
   ↓ [获取最终分析报告]
```

**关键点**:
- **第1步**: `create_case_from_event_scenario` - 为**每个场景**创建case+simulation
- **第2步**: `event-simulation/batch-start` - 批量启动多个仿真
- 规范中**没有**"批量创建"接口

---

## 规范中的方法合并说明

根据规范文档 **第294-307行**：

### 保留的方法
```python
✓ create_case()                      # 基础创建
✓ list_cases()
✓ get_case()
✓ delete_case()
✓ clone_case()

✓ create_case_from_event_scenario()  # ← 统一接口，替代：
                                      #   - create_case_from_scenario()
                                      #   - quick_create_case_from_event()
```

### 删除/内部化的方法
```python
❌ - _get_or_create_event_case()          # 改为内部用
❌ - _get_or_create_event_case_with_lock()  # 改为内部用
❌ - create_case_from_scenario()          # 合并到 create_case_from_event_scenario()
❌ - quick_create_case_from_event()       # 合并到 create_case_from_event_scenario()
```

### 删除的端点
根据规范文档 **第269-281行**：

```python
❌ DELETE /api/v1/case/create_case/
   ← 改名为 /api/v1/case/create

❌ DELETE /api/v1/case/quick-create-from-event
   ← 改名为 /api/v1/case/create-from-event-scenario
   ← 合并 create-from-scenario 的功能

❌ DELETE /api/v1/case/create-case-with-simulation
   ← 功能由 create-from-event-scenario 的自动模拟创建实现
```

**重点**: 规范中**根本没有**"批量创建"的概念。统一的做法是：
1. 逐个调用 `create-from-event-scenario`
2. 然后通过 `batch-start` 统一启动仿真

---

## 当前不符合规范的接口

### `POST /api/v1/scenario/create-case-batch`

**位置**: `api/routes/scenario_routes.py:404`

```python
@router.post("/create-case-batch", response_model=EventCaseBatchCreationResponse)
async def create_event_case_batch(request: CreateEventCaseBatchRequest):
```

**问题**:
- ❌ 规范文档中**完全未提及**
- ❌ 不是规范推荐的接口
- ❌ 违反了规范的单一责任原则
- ❌ 位置错误（在scenario_routes而不是case_routes）
- ❌ 创建了"批量创建"的非规范路径

**为什么会有这个接口**:
- 可能是为了性能优化（1次API调用而非N次）
- 可能是开发过程中的快速实现
- 但**未被纳入规范**

---

## 前端应该如何修改

### 规范的做法 ✅

前端"批量创建"按钮应该：

1. **逐个调用** `POST /api/v1/case/create-from-event-scenario`
2. **然后调用** `POST /api/v1/event-simulation/batch-start` 启动批次

```javascript
async function batchCreateEventCase(eventId) {
    const selectedScenarios = [...获取选中场景...];
    const createdCaseIds = [];

    try {
        // 步骤1: 为每个场景创建case+simulation
        for (const scenario of selectedScenarios) {
            console.log(`创建: ${scenario.scenario_id}...`);

            const response = await fetch('/api/v1/case/create-from-event-scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scenario_id: scenario.scenario_id,
                    simulation_duration_hours: scenario.time?.sim_duration_hours || 2.5,
                    output_config: scenario.output_config
                })
            });

            if (!response.ok) {
                throw new Error(`创建失败: ${scenario.scenario_id}`);
            }

            const result = await response.json();
            createdCaseIds.push(result.data.case_id);
            console.log(`✓ 创建成功: ${result.data.case_id}`);
        }

        // 步骤2: 批量启动这些案例的仿真（Phase 1.5）
        if (createdCaseIds.length > 0) {
            console.log(`批量启动 ${createdCaseIds.length} 个仿真...`);

            const batchStartResponse = await fetch('/api/v1/event-simulation/batch-start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    case_ids: createdCaseIds,
                    description: `Event ${eventId} batch`
                })
            });

            if (!batchStartResponse.ok) {
                throw new Error('批量启动失败');
            }

            const batchResult = await batchStartResponse.json();
            console.log(`✓ 批量启动成功: ${batchResult.data.batch_id}`);
        }

        // 显示成功消息
        alert(`✓ 批量创建成功！\n创建了 ${createdCaseIds.length} 个案例`);

        // 刷新列表
        loadCreatedCases();

    } catch (error) {
        console.error('批量创建失败:', error);
        alert(`✗ 批量创建失败: ${error.message}`);
    }
}
```

---

## 接口对比总结表

| 方面 | 现状（非规范）| 规范要求 |
|------|------|------|
| **API端点** | `/api/v1/scenario/create-case-batch` | `/api/v1/case/create-from-event-scenario` |
| **路由位置** | scenario_routes.py | **case_routes.py** |
| **规范文档提及** | ❌ 未提及 | ✅ **第249行明确定义** |
| **方法签名** | 批量（N个场景一次） | **单个（1个场景一次）** |
| **API调用数** | 1次 | N次（逐个循环） |
| **后续启动仿真** | 无专门接口 | ✅ **`batch-start` API** |
| **符合规范** | ❌ 否 | ✅ **是** |
| **向前兼容** | ⚠️ 可能有问题 | ✅ **完整兼容** |

---

## 规范核心原则

根据规范文档 **第364-367行**（Phase 1 的影响）：

```
- ✅ API 端点从 4 个减少到 2 个
- ✅ 功能完整（所有现有功能保留）
- ✅ 清晰的工作流（OD vs Event）
- ✅ 向后兼容（旧端点可在兼容层继续支持）
```

**这意味着**:
- `create-from-event-scenario` 是**唯一的**事件场景入口
- 不应该有"批量创建"的特殊接口
- 一切通过规范的接口实现

---

## 为什么不能用 `/scenario/create-case-batch`

### 1. 规范文档明确定义
- ✅ 定义了 `/case/create-from-event-scenario` (第249行)
- ❌ 完全未提及 `/scenario/create-case-batch`

### 2. 违反架构原则
- 违反了**单一职责** - case相关操作不应该在scenario路由中
- 违反了**统一入口** - 事件场景应该通过一个统一的接口

### 3. 影响后续维护
- 规范中Phase 1.5和Phase 2的所有设计都基于 `create-from-event-scenario`
- 使用非规范接口会导致与后续功能不兼容

### 4. 与规范不一致
- 规范明确说合并了5个旧方法到一个统一方法
- `/scenario/create-case-batch` 不在这个统一方法体系中

---

## 当前实现的技术债务

### 存在的问题
1. ❌ 前端调用了规范未定义的接口
2. ❌ 绕过了规范设计的单一入口
3. ❌ 后续如果规范接口有升级，这个快速实现可能需要大改
4. ❌ 与Phase 1.5和Phase 2的设计不兼容

### 建议的偿还方案

**优先级 P2** (高优先级，但不紧急)：
1. 修改前端逐个调用 `create-from-event-scenario`
2. 实现Phase 1.5的 `batch-start` API
3. 将 `/scenario/create-case-batch` 标记为**内部接口**或**临时接口**

---

## 行动建议

### 立即行动

1. **确认需求**
   - [ ] 确认前端是否应该按规范修改？
   - [ ] 什么时候修改？

2. **如果修改**
   - [ ] 修改 `frontend/scenarios/scenario_browser.js` 第713行
   - [ ] 改为循环调用 `/api/v1/case/create-from-event-scenario`
   - [ ] 实现Phase 1.5的 `batch-start` 支持
   - [ ] 更新用户界面显示进度

3. **如果保持现状**
   - [ ] 在代码中注释说明这是临时实现
   - [ ] 在规范文档中添加说明
   - [ ] 计划何时迁移到规范接口

---

## 规范文件参考

**文件**: `openspec/changes/event-scenario-simulation-integration/CASE_AND_ANALYSIS_CLEANUP_GUIDE.md`

**关键内容**:
- **第249行**: API端点定义 - `POST /api/v1/case/create-from-event-scenario`
- **第269-281行**: 删除的接口列表
- **第294-307行**: 方法合并说明
- **第364-367行**: Phase 1的影响
- **第628-637行**: 事件工作流架构
- **第639-720行**: 新增的批量管理接口

---

## 总结

### 当前状态
```
❌ 前端: /api/v1/scenario/create-case-batch
        ├─ 不符合规范
        ├─ 规范文档未提及
        └─ 属于非标准实现
```

### 规范要求
```
✅ 前端: /api/v1/case/create-from-event-scenario (循环调用)
        ↓
     /api/v1/event-simulation/batch-start (批量启动)
        └─ 完全符合规范
        ├─ 规范文档明确定义
        └─ 支持未来扩展
```

### 结论

🔴 **前端调用的 `/api/v1/scenario/create-case-batch` 接口不符合规范**

✅ **应该改为调用 `/api/v1/case/create-from-event-scenario`** (逐个场景)

---

**确认人**: Claude Code AI
**确认日期**: 2025-11-15
**规范来源**: `openspec/changes/event-scenario-simulation-integration/CASE_AND_ANALYSIS_CLEANUP_GUIDE.md`

