# scenario_index.json 自动集成总结

**日期**: 2025-11-16
**状态**: ✅ **实现完成**
**功能**: 在案例各步骤完成后自动填充scenario_index.json，并提供反向重置接口

---

## 📋 实现总览

### 目标
1. **自动化填充**: 在案例创建、OD生成、仿真完成时自动更新scenario_index.json
2. **反向重置**: 提供API接口来删除/清空created_cases关联信息

### 实现状态
- ✅ 批量创建案例时自动注册到scenario_index.json
- ✅ OD生成完成时自动更新案例状态
- ✅ 仿真完成/失败时自动更新案例状态
- ✅ 创建3个新的重置API接口

---

## 🔧 技术集成详情

### 1️⃣ 批量创建案例时自动注册（step: OD生成中）

**文件**: `api/services/case_service.py`
**方法**: `create_event_case_batch()` (第1823-1840行)
**触发点**: 批量创建完成后（保存metadata.json之后）

```python
# 为每个场景注册该case（批量创建时case处于od_generating状态）
for scenario in request.scenarios:
    mapper.register_case_creation(
        scenario_id=scenario.scenario_id,
        case_id=case_id,
        case_name=case_name,
        case_status="od_generating"  # 初始状态：OD生成中
    )
```

**流程**:
```
批量创建API调用
    ↓
创建案例和仿真目录
    ↓
生成metadata.json
    ↓
✅ 自动注册到scenario_index.json (status: od_generating)
    ↓
启动后台OD生成线程
    ↓
返回响应（显示"OD生成中"）
```

---

### 2️⃣ OD生成完成时自动更新状态（step: 已创建，可仿真）

**文件**: `api/services/case_service.py`
**方法**: `_run_od_generation_in_background()` (第1333-1343行)
**触发点**: OD数据生成成功后，metadata.json状态更新为"created"

```python
# 更新scenario_index.json中该case的状态（从od_generating到created）
for scenario_id in metadata.get('scenarios', []):
    mapper.update_case_status(scenario_id, case_id, 'created')
```

**流程**:
```
后台OD生成线程运行
    ↓
OD数据处理成功
    ↓
更新metadata.json: status = "created"
    ↓
✅ 自动更新scenario_index.json (status: created)
    ↓
重新生成所有simulation的sumocfg
    ↓
前端显示"已准备就绪，可启动仿真"
```

---

### 3️⃣ 仿真完成时自动更新状态（step: 已完成）

**文件**: `api/services/simulation_service.py`
**方法**: `_update_case_completion_status()` (第489-503行)
**触发点**: 仿真成功或失败，更新案例元数据

```python
# 更新scenario_index.json中该case的状态（仿真完成或失败）
new_status = 'completed' if status == 'completed' else 'failed'
for scenario_id in metadata.get('scenarios', []):
    mapper.update_case_status(scenario_id, case_id, new_status)
```

**流程**:
```
SUMO仿真运行
    ↓
仿真完成或失败
    ↓
更新simulation_metadata.json
    ↓
更新case metadata.json: status = "completed" 或 "failed"
    ↓
✅ 自动更新scenario_index.json (status: completed/failed)
    ↓
前端显示最终状态
```

---

## 🔄 完整案例生命周期

```
时间轴                 | scenario_index.json中的status
═══════════════════════════════════════════════════════
1. 批量创建完成        | ✅ 自动设为 "od_generating"
2. OD生成开始          | (后台处理，1-5分钟)
3. OD生成成功          | ✅ 自动更新为 "created"
4. 启动仿真            | (SUMO运行，5-30分钟)
5. 仿真成功完成        | ✅ 自动更新为 "completed"
   或仿真失败          | ✅ 自动更新为 "failed"
```

---

## 🗑️ 反向重置操作（API接口）

### 接口1: 删除某个case的所有关联

```http
DELETE /api/v1/batch/reset-scenario-mapping/{case_id}
```

**示例**:
```bash
curl -X DELETE http://localhost:8000/api/v1/batch/reset-scenario-mapping/case_event_10754
```

**响应**:
```json
{
  "success": true,
  "case_id": "case_event_10754",
  "scenarios_affected": 3,
  "message": "✓ 已从 3 个scenario中删除该case"
}
```

**用途**: 删除某个案例的所有scenario关联（撤销某次批量创建）

---

### 接口2: 清空某个scenario的所有created_cases

```http
DELETE /api/v1/batch/clear-scenario-cases/{scenario_id}
```

**示例**:
```bash
curl -X DELETE http://localhost:8000/api/v1/batch/clear-scenario-cases/scenario_10754_no_control
```

**响应**:
```json
{
  "success": true,
  "scenario_id": "scenario_10754_no_control",
  "cases_removed": 5,
  "message": "✓ 已清空该scenario的 5 个created_cases"
}
```

**用途**: 重置某个场景（删除所有为该场景创建的案例）

---

### 接口3: 重置整个系统（管理员操作）

```http
POST /api/v1/batch/reset-all-scenario-mappings
```

**示例**:
```bash
curl -X POST http://localhost:8000/api/v1/batch/reset-all-scenario-mappings
```

**响应**:
```json
{
  "success": true,
  "total_cases_removed": 45,
  "total_scenarios_affected": 15,
  "message": "✓ 已清空所有 45 个case，影响 15 个scenarios"
}
```

**⚠️ 警告**: 这是一个破坏性操作，仅在确实需要重置整个系统时使用

---

## 🔌 新增的服务层方法

### ScenarioCaseMapper 新增方法

**文件**: `shared/utilities/scenario_case_mapping.py`

#### 1. unregister_case_from_all_scenarios(case_id)
从所有scenario中删除某个case

```python
mapper = ScenarioCaseMapper()
removed_count = mapper.unregister_case_from_all_scenarios("case_event_10754")
# 返回值: 删除的scenario数量
```

#### 2. clear_scenario_cases(scenario_id)
清空某个scenario的所有created_cases

```python
mapper = ScenarioCaseMapper()
removed_count = mapper.clear_scenario_cases("scenario_10754_no_control")
# 返回值: 被清空的case数量
```

#### 3. reset_all_cases()
重置整个scenario_index.json

```python
mapper = ScenarioCaseMapper()
result = mapper.reset_all_cases()
# 返回值: {'total_cases_removed': int, 'total_scenarios_affected': int}
```

---

## 📊 scenario_index.json数据结构

### 创建后的数据示例

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",
  "location": {...},
  "time": {...},
  "files": {
    "scenario_dir": "scenario_10754_no_control",
    ...
  },
  "created_cases": [
    {
      "case_id": "case_event_10754",
      "case_name": "case_10754_batch",
      "status": "od_generating",        // 初始状态
      "source_scenario": "scenario_10754_no_control",
      "created_at": "2025-11-16T00:09:24.283768",
      "updated_at": "2025-11-16T00:15:30.123456"  // 状态更新时间
    }
  ]
}
```

### 状态转换

```
创建时:      "od_generating"
    ↓ (OD生成完成)
OD完成后:    "created"
    ↓ (启动仿真)
仿真运行中:  "created" (保持)
    ↓ (仿真完成/失败)
最终状态:    "completed" 或 "failed"
```

---

## 🔍 验证集成

### 1. 检查API文档
访问 http://localhost:8000/docs 查看新增的API接口

### 2. 测试批量创建流程
```bash
# 创建案例
curl -X POST http://localhost:8000/api/v1/case/create-case-batch \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "10754",
    "scenarios": [...]
  }'

# 检查scenario_index.json中的created_cases
grep -A 10 "scenario_10754_no_control" output/scenarios/scenario_index.json
```

### 3. 测试状态更新
- 观察服务日志输出，确认OD生成和仿真完成时的日志消息
- 检查scenario_index.json中的status字段是否自动更新

### 4. 测试重置接口
```bash
# 删除某个case
curl -X DELETE http://localhost:8000/api/v1/batch/reset-scenario-mapping/case_event_10754

# 验证：检查case已被删除
grep -c "case_event_10754" output/scenarios/scenario_index.json
# 应该返回 0
```

---

## ⚙️ 实现细节

### 文件修改汇总

| 文件 | 方法 | 行数 | 修改内容 |
|------|------|------|---------|
| api/services/case_service.py | create_event_case_batch() | 1823-1840 | 批量创建后注册到scenario_index.json |
| api/services/case_service.py | _run_od_generation_in_background() | 1333-1343 | OD生成完成后更新状态 |
| api/services/simulation_service.py | _update_case_completion_status() | 489-503 | 仿真完成/失败时更新状态 |
| shared/utilities/scenario_case_mapping.py | (新增3个方法) | 388-526 | 反向重置功能 |
| api/routes/batch_routes.py | (新增3个路由) | 225-342 | 重置API接口 |

### 关键设计决策

1. **非阻塞更新**: 所有scenario_index.json更新都用try-except包裹，避免影响主流程
2. **幂等性**: 重置操作可以安全地重复执行
3. **日志记录**: 所有操作都有详细的日志输出便于调试
4. **兼容性**: 不修改现有的metadata.json结构，只更新scenario_index.json

---

## 🚀 使用建议

### ✅ 推荐做法
- 批量创建后自动注册到scenario_index.json（已自动化）
- OD生成和仿真完成后自动更新状态（已自动化）
- 需要撤销某个案例时使用DELETE接口

### ❌ 避免做法
- 不要手动修改scenario_index.json的created_cases（自动流程会覆盖）
- 不要频繁使用reset-all接口（除非真的需要重置）

---

## 📝 日志示例

### 批量创建完成时
```
✓ 已注册到scenario_index.json: scenario_10754_no_control <- case_event_10754
✓ 已注册到scenario_index.json: scenario_10754_vss <- case_event_10754
✓ 已注册到scenario_index.json: scenario_10754_tec <- case_event_10754
✓ scenario_index.json 已更新（3个场景已注册）
```

### OD生成完成时
```
✓ Case case_event_10754 status updated to created after OD generation
✓ scenario_index.json已更新: scenario_10754_no_control - case_event_10754 状态 → created
✓ scenario_index.json已更新: scenario_10754_vss - case_event_10754 状态 → created
✓ scenario_index.json已更新: scenario_10754_tec - case_event_10754 状态 → created
```

### 仿真完成时
```
✓ scenario_index.json已更新: scenario_10754_no_control - case_event_10754 状态 → completed
✓ scenario_index.json已更新: scenario_10754_vss - case_event_10754 状态 → completed
✓ scenario_index.json已更新: scenario_10754_tec - case_event_10754 状态 → completed
```

---

## 🔗 相关文档

- `SCENARIO_INDEX_IMPLEMENTATION_COMPLETE.md` - 初始实现总结
- `SCENARIO_INDEX_QUICKSTART.md` - 快速开始指南
- `SCENARIO_INDEX_FIELDS_REFERENCE.md` - 字段参考文档
- `SCENARIO_INDEX_SYNC_GUIDE.md` - 同步详细指南

---

## ✨ 总结

### 实现成果
✅ **自动化集成**: scenario_index.json在案例生命周期的关键步骤自动更新
✅ **反向操作**: 提供3个灵活的API接口来重置/清空created_cases
✅ **非侵入式**: 不修改existing的元数据结构，只拓展functionality
✅ **错误处理**: 所有操作都有proper的异常处理，不影响主流程

### 用户体验
- 用户创建案例 → 自动注册到scenario_index.json
- OD生成完成 → 自动标记为"已创建"
- 仿真完成 → 自动标记为"已完成"
- 前端可以实时显示完整的scenario-case关联关系

---

**现在scenario_index.json完全集成到了案例生命周期中！** 🎉

