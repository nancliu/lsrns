# Case ID 命名规范修复 - 执行总结

**修复时间**: 2025-11-15  
**修复状态**: ✅ 完成  
**影响范围**: 事件场景案例创建流程

---

## 问题回顾

### 原始问题
- **症状**: 批量创建事件案例时，生成的case_id为 `case_event_20251115_213819` (包含时间戳)
- **预期**: `case_event_10754` (使用event_id)
- **根本原因**: create_event_case_batch方法中使用了generate_unique_id()而非直接格式化event_id

### 影响
- ❌ 从case_id无法直接识别事件
- ❌ 难以进行case检索和管理
- ❌ 不符合event-based架构规范

---

## 修复内容

### 1. Case ID 命名规范修复 ✅

**文件**: `api/services/case_service.py`

**修改位置 1**: create_event_case_batch方法 (第1695行)

```python
# 修改前
case_id = self.generate_unique_id("case_event")

# 修改后
case_id = f"case_event_{request.event_id}"
```

**说明**: 直接使用event_id格式化case_id，符合event-based架构规范

---

### 2. Tripinfo输出配置修复 ✅

**文件**: `api/services/case_service.py`

**修改位置 1**: create_event_case_batch方法 (第1883-1893行)

```python
# 修改前
simulation_params = {
    "duration_hours": scenario.time.get('sim_duration_hours', 2.5),
    "random_seed": None,
    "simulation_type": request.simulation_type,
    "output_config": scenario.output_config  # 直接使用前端提供的config
}

# 修改后
event_output_config = scenario.output_config.copy() if scenario.output_config else {}
event_output_config["generate_tripinfo"] = False  # 强制禁用tripinfo

simulation_params = {
    "duration_hours": scenario.time.get('sim_duration_hours', 2.5),
    "random_seed": None,
    "simulation_type": request.simulation_type,
    "output_config": event_output_config  # 禁用tripinfo后的config
}
```

**修改位置 2**: create_case_from_event_scenario方法 (第1490-1509行)

```python
# 修改前
output_config = request.output_config or {}
simulation_params = {
    ...
    "output_config": request.output_config,
    "output_edgedata": output_config.get("generate_edgedata", False),
    ...
    "output_vehroute": output_config.get("generate_vehroute", False),
    ...
}

# 修改后
output_config = request.output_config or {}
event_output_config = output_config.copy()
event_output_config["generate_tripinfo"] = False  # 禁用tripinfo

simulation_params = {
    ...
    "output_config": event_output_config,
    "output_edgedata": event_output_config.get("generate_edgedata", False),
    ...
    "output_vehroute": event_output_config.get("generate_vehroute", False),
    ...
}
```

**说明**: 强制禁用tripinfo输出，因为Phase 2分析仅需summary.xml + edgedata.xml

---

## 修复效果对比

### 修复前 ❌
| 维度 | 值 |
|------|-----|
| Case ID 格式 | `case_event_20251115_213819` (时间戳) |
| Case ID 与event的关系 | 无法从ID判断event |
| Tripinfo生成 | 启用（浪费存储) |
| 数据驱动性 | 低 |

### 修复后 ✅
| 维度 | 值 |
|------|-----|
| Case ID 格式 | `case_event_10754` (event_id) |
| Case ID 与event的关系 | 直接对应 |
| Tripinfo生成 | 禁用（节省资源) |
| 数据驱动性 | 高 |

---

## 验证清单

- [x] 修改case_id生成逻辑，使用event_id
- [x] 禁用event仿真的tripinfo生成
- [x] 修改create_event_case_batch方法
- [x] 修改create_case_from_event_scenario方法
- [x] 检查Python语法（无错误）
- [ ] 创建新的event案例进行测试（待执行）

---

## 代码变更统计

| 项目 | 数量 |
|------|------|
| 修改的文件 | 1 (case_service.py) |
| 修改的方法 | 2 (create_event_case_batch, create_case_from_event_scenario) |
| 修改行数 | ~15 lines |
| 新增注释行 | 4 |

---

## 向后兼容性

✅ **完全兼容** - 修改仅影响新创建的案例，现有案例不受影响

- 现有的time-based案例（非事件场景）不受影响
- 只有event-based案例（通过create_event_case_batch创建）会使用新的命名格式
- 旧的案例ID仍可以继续使用

---

## 后续建议

### 立即执行
1. ✅ 已完成 - Case ID命名修复
2. ✅ 已完成 - Tripinfo配置修复
3. 🟡 待执行 - 测试新案例创建

### 后续改进
1. EdgeData完整性改进（P2）
2. Phase 1.5实现（批量仿真启动/进度/结果查询）
3. Phase 2实现（事件仿真批量结果分析）

---

## 测试建议

建议创建新的event案例（如event 10755）进行测试：

```bash
# 前端调用
POST /api/v1/scenario/create-case-batch
{
  "event_id": "10755",
  "event_type": "01_accident",
  "scenarios": [...],
  "network_file": "...",
  "od_file": "...",
  "taz_file": "..."
}

# 验证结果
- Case ID应为: case_event_10755 ✅
- Simulation output_config中generate_tripinfo应为: false ✅
```

---

## 相关文档

- 原始需求: `openspec/changes/event-scenario-simulation-integration/CASE_AND_ANALYSIS_CLEANUP_GUIDE.md`
- 验证报告: `cases/case_event_20251115_213819/VERIFICATION_REPORT.md`
- 规范文档: `CLAUDE.md` (PRINCIPLE-ARCH-001, PRINCIPLE-ARCH-002等)

