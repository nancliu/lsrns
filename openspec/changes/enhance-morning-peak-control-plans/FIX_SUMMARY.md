# 管控方案仿真问题修复总结

## 问题分析

### 问题1: status端点500错误
**现象**: `GET /api/v1/simulation/status?case_id=case_20251110_130339&simulation_id=sim_1110_130957098_micro` 返回500错误

**分析**:
- 代码库中**不存在** `/api/v1/simulation/status` 端点
- 该端点可能是误调用或不存在
- 应该复用批次仿真的进度查询逻辑

**解决方案**:
- 管控方案仿真应使用批次仿真的进度查询端点：`GET /api/v1/control/batch-optimization/batch/{batch_id}/progress`
- 该端点不需要传递case_id，会通过batch_id自动查找case_id
- 前端应通过 `control/simulations.html` 调用，而不是 `scenario_browser.html`

### 问题2: 管控方案仿真目录结构
**确认**: 管控方案仿真已正确使用 `plan_opti` 目录结构
- 路径: `cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/`
- sumocfg路径: `cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/simulation.sumocfg`

**验证**:
- `shared/control_tools/batch_simulation_scheduler.py` 第669-672行已正确实现
- `shared/utilities/file_utils.py` 第110-118行已正确实现
- `api/services/simulation_service.py` 第186-200行已正确实现

### 问题3: sumocfg文件路径
**确认**: sumocfg文件路径生成逻辑正确
- `simulation.sumocfg` 位于 `simulation_folder` 目录下
- 对于批次仿真，`simulation_folder` = `cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/`
- SUMO运行时，工作目录设置为 `simulation_folder`，使用相对路径 `simulation.sumocfg`

**验证**:
- `api/services/simulation_service.py` 第208行: `cfg_file = simulation_folder / "simulation.sumocfg"`
- `shared/data_processors/simulation_processor.py` 第82-87行: 正确设置工作目录和配置文件路径

## 修复建议

### 1. 前端调用修复
- **不要**通过 `scenario_browser.html` 调用仿真
- **应该**通过 `control/simulations.html` 调用批次仿真API
- 使用批次仿真的进度查询端点：`GET /api/v1/control/batch-optimization/batch/{batch_id}/progress`

### 2. 进度查询修复
- **不要**使用 `/api/v1/simulation/status` 端点（不存在）
- **应该**使用 `/api/v1/control/batch-optimization/batch/{batch_id}/progress` 端点
- 该端点通过batch_id自动查找case_id，不需要传递case_id参数

### 3. 目录结构确认
- 管控方案仿真已正确使用 `plan_opti` 目录结构
- sumocfg文件路径正确
- 无需修改

## 验证步骤

1. **验证sumocfg路径**:
   ```bash
   # 检查批次仿真目录结构
   ls cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/
   # 应该看到 simulation.sumocfg 文件
   ```

2. **验证进度查询**:
   ```bash
   # 使用批次进度查询端点
   curl "http://localhost:8000/api/v1/control/batch-optimization/batch/{batch_id}/progress"
   ```

3. **验证前端调用**:
   - 打开 `frontend/control/simulations.html`
   - 创建批次仿真
   - 查看进度监控是否正常工作

## 总结

- ✅ 批次仿真目录结构正确（plan_opti）
- ✅ sumocfg文件路径正确
- ❌ status端点不存在，应使用批次进度查询端点
- ❌ 前端应通过control/simulations.html调用，而不是scenario_browser.html

