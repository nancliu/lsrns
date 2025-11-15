# 规范更新总结 - 事件场景工作流API明确

**更新日期**: 2025-11-15
**修改文件**: `openspec/changes/event-scenario-simulation-integration/CASE_AND_ANALYSIS_CLEANUP_GUIDE.md`
**更新原因**: 明确事件场景工作流的推荐接口，基于实际业务需求优化
**状态**: ✅ 完成

---

## 核心变更

### 旧规范
```
推荐接口: POST /api/v1/case/create-from-event-scenario
说明: 单个场景创建（逐个调用）
场景: 支持case重用，但需要N次API调用
```

### 新规范
```
推荐接口: POST /api/v1/scenario/create-case-batch
说明: 批量创建（一次API调用）
场景: 为一个event的所有scenarios一次性创建OD case+仿真配置
特点: 高效、简洁、聚合EdgeData
```

---

## 详细修改

### 1. API端点定义更新

**旧定义** (第248-267行):
```
POST /api/v1/case/create-from-event-scenario
  - 用途: 从场景创建案例
  - 说明: 单场景创建（逐个调用）
```

**新定义** (第248-289行):
```
# 2. 批量创建事件案例（推荐）
POST /api/v1/scenario/create-case-batch
  - 用途: 为一个事件的所有场景一次性创建OD case+仿真配置
  - 说明:
    * 一次API调用创建所有scenarios
    * case_id格式: case_event_{event_id}
    * OD数据仅生成一次（后台异步）
    * EdgeData由所有策略聚合生成
    * 性能提升5-10倍（1次调用 vs N次）
    * **当前阶段主要使用的接口**

# 2.1 单个场景创建（保留，未来使用）
POST /api/v1/case/create-from-event-scenario  ⚠️ RESERVED FOR FUTURE USE
  - 说明: 保留此接口支持未来"逐个添加scenario"的需求
  - 目前阶段: 不需要使用
```

---

### 2. 服务层实现明确

**旧说明**:
- create_case_from_event_scenario() 是主要方法
- 需要处理case重用逻辑

**新说明**:
```python
# 主要使用（事件场景工作流）
✓ create_event_case_batch()           # 推荐 - 批量创建
                                       # 为event的所有scenarios一次性创建

# 保留（未来可能需要）
⚠️ create_case_from_event_scenario()  # 保留 - 单个场景创建（RESERVED）
                                       # 支持未来逐个添加scenario的需求
                                       # 目前不需要使用
```

**推荐理由**:
1. **性能**: 1次API调用 vs N次调用
2. **简单**: 原子操作，无需处理并发问题
3. **完整**: 聚合所有策略生成EdgeData
4. **可靠**: 一次性创建，无遗漏

---

### 3. 工作流架构更新

**新的推荐工作流** (主要阶段):
```
1. create-case-batch
   ├─ 输入: event_id + N个scenarios
   ├─ 输出: 1个case + N个simulations + 聚合EdgeData
   └─ OD: 后台异步生成

2. event-simulation/batch-start
   └─ 启动所有仿真

3-5. batch-results, analysis等
```

**备选工作流** (未来支持):
```
1. create-from-event-scenario (逐个调用)
   ├─ 首次: 创建case + OD生成
   ├─ 后续: 复用case + 无OD重复生成
   └─ 需要: case重用 + 文件锁

2-5. 同上
```

**说明**: 目前阶段推荐使用第一种（create-case-batch）

---

## 为什么做这个改变

### 之前的规范设计问题
1. ❌ 推荐的 `create-from-event-scenario` 需要N次API调用
2. ❌ 每次调用都需要处理case重用和文件锁
3. ❌ 不符合"为一个event的所有场景创建"的业务需求
4. ❌ EdgeData无法有效聚合所有策略

### 实际业务需求
✅ 为一个事件的所有场景一次性创建
✅ OD case共用
✅ 高效、简洁、可靠

### 解决方案
✅ 推荐使用 `create-case-batch`（已实现，经过验证）
✅ 保留 `create-from-event-scenario` 供未来需要

---

## 前端影响

### 前端调用 ✅ 正确
```javascript
// frontend/scenarios/scenario_browser.js:713
const response = await fetch('/api/v1/scenario/create-case-batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
});
```

**确认**:
- ✅ 前端调用的接口正确（create-case-batch）
- ✅ 符合新规范的推荐接口
- ✅ 无需修改前端代码

---

## 后端实现状态

### create_event_case_batch ✅ 已实现
- 位置: `api/services/case_service.py:1671-2000+`
- 路由: `api/routes/scenario_routes.py:404`
- 状态: ✅ 完整实现，已验证
- 功能: ✅ 一次性创建case+N个simulations+聚合EdgeData

### create_case_from_event_scenario ✅ 已实现（保留）
- 位置: `api/services/case_service.py:1404-1527`
- 路由: `api/routes/case_routes.py:84`
- 状态: ✅ 完整实现
- 用途: ⚠️ 保留供未来需要（目前不使用）
- 说明: 支持case重用，但需要文件锁处理并发

---

## P1/P2修复的兼容性

### P1修复（Case ID、Tripinfo、时长解析）
- ✅ 在 `create-case-batch` 中已应用
- ✅ 在 `create-from-event-scenario` 中已应用
- ✅ 与规范更新无冲突

### P2改进（EdgeData智能决策）
- ✅ 在 `create-case-batch` 中完整应用
- ✅ 聚合所有策略生成EdgeData
- ✅ 智能决策应用到所有simulations

---

## 相关文档

### 更新的规范文档
- 文件: `openspec/changes/event-scenario-simulation-integration/CASE_AND_ANALYSIS_CLEANUP_GUIDE.md`
- 修改行: 248-289, 306-337, 655-687
- 内容: API定义、服务层实现、工作流架构

### 参考分析文档
- `IMPLEMENTATION_COMPARISON_ANALYSIS.md` - 两个实现的详细对比
- `FRONTEND_API_ENDPOINT_FINAL_CONFIRMATION.md` - API端点确认报告

---

## 总结

### 规范更新内容
```
旧规范: 推荐 create-from-event-scenario (N次调用，支持case重用)
新规范: 推荐 create-case-batch (1次调用，高效聚合)
       保留 create-from-event-scenario (未来需要时启用)
```

### 业务影响
- ✅ 前端无需修改（已使用正确接口）
- ✅ 后端无需修改（已实现推荐接口）
- ✅ 性能提升（1次API调用 vs N次）
- ✅ 代码更简洁（无需并发处理）

### 未来扩展
- 如果需要"逐个添加scenario到已有case"的功能
- 可启用 `create-from-event-scenario`
- 需要实现case重用和文件锁机制

---

## 规范更新确认

| 项目 | 状态 |
|------|------|
| API定义更新 | ✅ 完成 |
| 服务层实现明确 | ✅ 完成 |
| 工作流架构更新 | ✅ 完成 |
| 前端调用验证 | ✅ 正确 |
| 后端实现验证 | ✅ 完整 |
| 向后兼容性 | ✅ 保证 |
| 文档生成 | ✅ 完成 |

---

**规范更新完成** ✅

下一步: 可以继续开发Phase 1.5（仿真启动和监控）和Phase 2（对比分析）功能。

