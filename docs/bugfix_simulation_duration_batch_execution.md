# BUG修复: 批量仿真中simulation_duration未生效

**报告时间:** 2025-11-04
**问题:** 用户通过批量仿真API设置自定义仿真时长（如15分钟），但实际仿真时长仍使用case元数据的默认值（10分钟）
**严重性:** 高 - 影响用户自定义仿真时长的功能
**状态:** ✅ 已修复

---

## 问题描述

### 症状
- 前端成功收集了simulation_duration参数（15分钟）
- API创建批次成功，simulation_config.json正确保存了参数
- 但实际批量仿真执行时：
  - sumocfg.xml的`<time><end>`值仍为600秒（10分钟），而不是900秒（15分钟）
  - 仿真完成后，时长未改变
  - 控制台日志显示使用了case元数据的时间范围，而非自定义时长

### 影响范围
- **只影响批量仿真** (通过 POST /api/v1/control/batch-optimization/batch)
- **不影响单仿真** (直接使用 simulation_service 的prepare_simulation)
- **参数已正确保存** 在simulation_config.json中，问题在执行阶段

---

## 根本原因分析

### 问题链路

```
API创建批次
  ✅ simulation_duration被正确保存到simulation_config.json

BatchSimulationScheduler读取批次配置
  ❌ 只读取output_*参数，忽略simulation_duration
  ❌ 只读取output_*参数，忽略edgedata_use_template_edges
  ❌ 构造的simulation_params缺少这两个参数

SimulationService.prepare_simulation()
  ❌ 接收到的simulation_params不包含simulation_duration
  ❌ 调用generate_sumocfg_for_simulation时无法应用自定义时长

generate_sumocfg_for_simulation()
  ❌ simulation_params.get('simulation_duration')返回None
  ❌ 降级为使用case元数据计算时长
```

### 代码位置

**问题文件:** `shared/control_tools/batch_simulation_scheduler.py`

**问题代码段** (L608-620，修复前):
```python
simulation_params = {
    "random_seed": task.seed,
}

# 添加来自batch的output参数
if batch_simulation_config:
    for key in ['output_tripinfo', 'output_vehroute', 'output_netstate', 'output_fcd', 'output_emission', 'output_edgedata']:
        if key in batch_simulation_config:
            simulation_params[key] = batch_simulation_config[key]
    # ❌ 没有添加simulation_duration！
    # ❌ 没有添加edgedata_use_template_edges！

# 如果方案有additional_file，添加到仿真参数中
if additional_file_path:
    simulation_params["additional_file"] = additional_file_path
```

---

## 修复方案

### 修改内容

**文件:** `shared/control_tools/batch_simulation_scheduler.py`

**修复范围:** L608-631

**修复代码** (修复后):
```python
simulation_params = {
    "random_seed": task.seed,
}

# 添加来自batch的output参数
if batch_simulation_config:
    # 添加output_*参数
    for key in ['output_tripinfo', 'output_vehroute', 'output_netstate', 'output_fcd', 'output_emission', 'output_edgedata']:
        if key in batch_simulation_config:
            simulation_params[key] = batch_simulation_config[key]

    # ✅ 添加simulation_duration参数 (P1-4: 批量仿真支持)
    if 'simulation_duration' in batch_simulation_config:
        simulation_params['simulation_duration'] = batch_simulation_config['simulation_duration']
        logger.info(f"Applied custom simulation_duration: {batch_simulation_config['simulation_duration']}")

    # ✅ 添加edgedata_use_template_edges参数 (P2-4: 批量仿真支持)
    if 'edgedata_use_template_edges' in batch_simulation_config:
        simulation_params['edgedata_use_template_edges'] = batch_simulation_config['edgedata_use_template_edges']
        logger.info(f"Applied edgedata_use_template_edges: {batch_simulation_config['edgedata_use_template_edges']}")

# 如果方案有additional_file，添加到仿真参数中
if additional_file_path:
    simulation_params["additional_file"] = additional_file_path
```

### 修复涉及的参数

1. **simulation_duration** (P1-4)
   - 来源: simulation_config.json 的 simulation_params
   - 用途: 覆盖case元数据计算的仿真时长
   - 应用位置: shared/utilities/sumo_utils.py L154-157

2. **edgedata_use_template_edges** (P2-4)
   - 来源: simulation_config.json 的 simulation_params
   - 用途: 控制EdgeData生成时是否保留edges属性
   - 应用位置: shared/utilities/sumo_utils.py L212-213

---

## 验证方法

### 手动验证

1. 通过UI创建批次，设置仿真时长为15分钟，case元数据为10分钟
2. 启动批量仿真
3. 检查生成的 `simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/simulation.sumocfg` 文件
4. 验证 `<time><end value="900"/>` (15分钟=900秒)

### 自动化测试

创建了新的集成测试: `tests/integration/test_batch_simulation_duration_execution.py`

**测试覆盖:**
- ✅ test_custom_duration_flow_in_batch_creation
- ✅ test_custom_duration_applied_in_sumocfg_generation
- ✅ test_batch_config_readable_by_simulation_scheduler
- ✅ test_case_default_vs_custom_duration

**测试命令:**
```bash
conda activate od_project
pytest tests/integration/test_batch_simulation_duration_execution.py -v
```

**结果:** ✅ 4/4 通过

---

## 完整参数流转验证

修复后，完整的参数流转链路：

```
1. Frontend
   └─ POST /api/v1/control/batch-optimization/batch
      ├─ simulation_duration: {hours: 0, minutes: 15, total_minutes: 15}
      └─ edgedata_use_template_edges: false

2. API Layer (batch_optimization_routes.py)
   └─ CreateBatchRequest 验证和解析
      └─ BatchOptimizationService.create_batch()

3. Batch Service (batch_optimization_service.py)
   ├─ simulation_duration保存到unified_simulation_config
   ├─ 保存到simulation_config.json顶级字段
   └─ 保存到simulation_params子字段

4. 批次配置文件 (simulation_config.json)
   {
     "simulation_params": {
       "output_tripinfo": true,
       "output_edgedata": false,
       "simulation_duration": {     ← ✅ 这里
         "hours": 0,
         "minutes": 15,
         "total_minutes": 15
       },
       "edgedata_use_template_edges": false  ← ✅ 这里
     }
   }

5. Batch Scheduler (batch_simulation_scheduler.py) - L620-627 ✅ FIXED
   ├─ 从simulation_config.json读取simulation_params
   ├─ 提取simulation_duration ✅
   ├─ 提取edgedata_use_template_edges ✅
   └─ 传递给SimulationService

6. Simulation Service (simulation_service.py)
   └─ 调用generate_sumocfg_for_simulation(
        simulation_params=simulation_params  ← 包含duration
      )

7. SUMO Utils (sumo_utils.py)
   ├─ L154: if simulation_params.get('simulation_duration'): ✅
   │   duration = 15 * 60 = 900 秒
   └─ L212: if not simulation_params.get('edgedata_use_template_edges', False): ✅
       移除edges属性

8. SUMO Configuration (sumocfg.xml)
   <time>
     <end value="900"/>  ← ✅ 正确应用了自定义时长！
   </time>
```

---

## 测试覆盖统计

### 修复前
- P1 integration tests: 6 tests ✅ (API层面的参数保存)
- P2 integration tests: 9 tests ✅ (边界条件验证)
- **批量仿真执行测试: 0** ❌ (没有验证整个流程)

### 修复后
- P1 integration tests: 6 tests ✅
- P2 integration tests: 9 tests ✅
- **批量仿真执行测试: 4 tests** ✅ (新增，验证完整流程)
- **总计: 19 tests** ✅ 100% 通过

---

## 性能影响

- **性能影响:** 无
  - 只是在现有条件判断中添加了两个额外的if语句
  - 额外开销: O(1)

- **向后兼容性:** ✅ 完全兼容
  - 当simulation_duration不存在时，降级为case元数据计算
  - 现有批次不受影响

---

## 部署检查清单

- [x] 修复代码已实现
- [x] 单元测试通过
- [x] 集成测试通过 (19/19)
- [x] 无性能回归
- [x] 向后兼容性验证
- [ ] 生产环境测试 (待执行)

---

## 用户影响

**修复前:**
```
用户设置: 仿真时长 15分钟
实际结果: 仿真时长 10分钟 (case元数据)
状态: ❌ 参数被忽略
```

**修复后:**
```
用户设置: 仿真时长 15分钟
实际结果: 仿真时长 15分钟 ✅
状态: ✅ 参数正确应用
```

---

## 相关任务

- **OpenSpec Change:** sumocfg-parameter-completion
- **P1-4 (新增):** 批量仿真中的simulation_duration支持
- **P2-4 (新增):** 批量仿真中的edgedata_use_template_edges支持

---

**修复完成时间:** 2025-11-04
**修复者:** Claude Code Assistant
**验证状态:** ✅ 所有测试通过
