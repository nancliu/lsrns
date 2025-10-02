# MVP并行仿真测试指南

## 概述

本文档提供管控方案优化子系统MVP阶段的完整测试流程,验证核心功能:
- 并行仿真集成（基于subprocess，无TraCI依赖）
- 实例完全独立（独立目录+配置+输出）
- 基础监控
- 峰值车辆数统计

**MVP版本**: v1.0 (Epic 1完成)
**测试范围**: Phase 1核心功能
**预计测试时间**: 30-60分钟
**架构变更**: Epic 1移除TraCI依赖，采用subprocess直接运行SUMO

---

## 前置条件

### 1. 环境检查

```powershell
# 确认conda环境
mamba activate od-sim  # 或你的环境名

# 确认Python版本
python --version  # 需要3.10+

# 确认SUMO环境变量
$env:SUMO_HOME  # 应输出SUMO安装路径
```

### 2. 依赖包检查

```powershell
# 检查必需包（Epic1已移除traci依赖）
python -c "import psutil, pandas; print('依赖包完整')"
```

如果缺少包,安装:
```powershell
mamba install -c conda-forge psutil pandas prettytable
```

**注意**: Epic1已移除TraCI依赖，现在使用subprocess直接运行SUMO。

### 3. 数据准备

确保至少有一个已完成OD数据处理的案例:
- 访问: http://localhost:8000/index.html
- 导航到"案例管理"页面
- 确认至少有1个案例,且状态为"completed"或"simulating"
- 确认该案例下至少有1个仿真配置(status可以是pending/completed)

---

## 测试方法

### 方法1: Web前端测试 (推荐)

#### 步骤1: 启动API服务

```powershell
.\start_api.ps1
```

等待服务启动完成,看到:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 步骤2: 访问MVP并行仿真页面

浏览器打开: **http://localhost:8000/control_optimization/mvp_parallel_simulation.html**

#### 步骤3: 选择案例和仿真

1. 在"选择案例"下拉框中选择一个案例
2. 在"选择仿真配置"下拉框中选择一个仿真
3. 设置"并行数量" (建议从5-10开始测试)

#### 步骤4: 生成配置（可选）

**推荐**: 先生成配置文件,检查配置是否正确

1. 点击"仅生成配置文件"按钮
2. 观察"执行结果"区域,应显示:
   ```json
   {
     "status": "success",
     "message": "成功生成批量配置，5个实例共享配置文件",
     "batch_id": "batch_config_1001_120000",
     "case_id": "case_20250923_143156",
     "template_simulation_id": "sim_0926_152911_micro",
     "num_configs": 5,
     "config_type": "shared",
     "output_directory": "cases/.../control_optimization/batch_config_MMDD_HHMMSS",
     "shared_config_file": "cases/.../batch_config_MMDD_HHMMSS/simulation.sumocfg",
     "metadata_file": "cases/.../batch_config_MMDD_HHMMSS/batch_metadata.json",
     "instances_file": "cases/.../batch_config_MMDD_HHMMSS/instances.json",
     "created_at": "2025-10-01T12:00:00"
   }
   ```

3. 检查生成的配置文件:
   ```powershell
   cd cases/case_XXXXXX/control_optimization/batch_config_MMDD_HHMMSS
   ls
   # 应看到:
   # - simulation.sumocfg (模板配置文件)
   # - TAZ_6.add.xml (共享TAZ文件)
   # - batch_metadata.json (批量元数据)
   # - instances.json (实例列表)
   #
   # Epic1注意: 实际运行时每个实例会创建独立目录:
   # - instance_0/, instance_1/, ..., instance_N/
   # - 每个instance_X/包含独立的simulation.sumocfg、TAZ、e1/、edgedata/
   ```

#### 步骤5: 启动并行仿真

1. 点击"生成配置并启动仿真"按钮
2. 观察"执行结果"区域,应显示:
   ```json
   {
     "status": "started",
     "message": "并行仿真已在后台启动",
     "case_id": "case_20250923_143156",
     "simulation_id": "sim_0926_152911_micro",
     "num_parallel": 10,
     "config_path": "cases/.../simulation.sumocfg",
     "output_dir": "cases/.../control_optimization/parallel_sim_MMDD_HHMMSS",
     "timestamp": "2025-10-01T12:00:00"
   }
   ```

#### 步骤6: 查看执行结果

仿真完成后,在输出目录中检查:
```powershell
# 进入批次配置目录(从API响应的batch_config_dir获取)
cd cases/case_XXXXXX/control_optimization/batch_config_MMDD_HHMMSS

# 查看实例目录结构（Epic1架构）
ls
# 应看到:
# - instance_0/
# - instance_1/
# - ...
# - instance_N/
# - simulation.sumocfg (模板配置)
# - TAZ_6.add.xml (模板TAZ)
# - batch_metadata.json
# - instances.json

# 检查单个实例的输出（以instance_0为例）
cd instance_0
ls
# 应看到:
# - simulation.sumocfg (独立配置，路径已自动调整)
# - TAZ_6.add.xml (复制的TAZ文件)
# - summary.xml (仿真汇总结果)
# - tripinfo.xml (车辆行程信息)
# - e1/ (E1检测器输出目录)
# - edgedata/ (EdgeData输出目录)
```

**注意**: Epic 1架构变更后，每个实例完全独立运行，输出文件分散在各自的instance_X/目录中。Phase 2将实现结果汇聚功能。

---

### 方法2: Python脚本测试

#### 测试A: 批量配置生成

```powershell
# 确保API服务运行
.\start_api.ps1

# 运行配置生成测试
python test_batch_config_generation.py
```

**预期输出**:
```
============================================================
MVP批量配置生成功能测试
============================================================

步骤1: 获取案例列表
✓ 选择测试案例: case_20250923_143156

步骤2: 获取仿真列表 (case_id=case_20250923_143156)
✓ 选择测试仿真: sim_0926_152911_micro

步骤3: 生成批量配置
✓ 配置生成成功!

步骤4: 验证生成的文件
✓ 输出目录存在
✓ 共享配置文件存在: simulation.sumocfg
✓ 元数据文件存在: batch_metadata.json
✓ 实例列表文件存在: instances.json
✓ 端口分配无重复 (范围: 8813-8817)
✓ 所有实例共享同一配置文件

============================================================
✓ 批量配置生成测试通过!
============================================================
```

#### 测试B: 完整并行仿真流程

```powershell
python test_mvp_api.py
```

#### 预期输出示例

```
============================================================
MVP并行仿真API测试
============================================================

=== 测试案例列表API ===
✓ API调用成功
案例总数: 15

可用案例:
  - case_20250923_143156 (状态: simulating)
  - case_20250901_174435 (状态: completed)
  ...

选择测试案例: case_20250923_143156

=== 测试仿真列表API (case_id=case_20250923_143156) ===
✓ API调用成功
仿真数量: 4

可用仿真:
  - sim_0926_152911_micro (状态: pending)
  - sim_0923_143335_micro (状态: completed)
  ...

选择测试仿真: sim_0926_152911_micro

=== 测试MVP并行仿真API ===
case_id: case_20250923_143156
config_file: cases/case_20250923_143156/simulations/sim_0926_152911_micro/simulation.sumocfg
num_parallel: 5

调用API: POST http://localhost:8000/api/v1/control_optimization/mvp/parallel_simulation

✓ API调用成功
响应:
{
  "status": "started",
  "message": "并行仿真已在后台启动",
  ...
}

============================================================
✓ MVP并行仿真测试完成!
============================================================
```

---

### 方法3: 命令行直接测试

```powershell
# 使用Invoke-WebRequest测试API

$caseId = "case_20250923_143156"
$configFile = "cases/case_20250923_143156/simulations/sim_0926_152911_micro/simulation.sumocfg"
$numParallel = 5

# URL编码配置文件路径
$encodedConfigFile = [System.Web.HttpUtility]::UrlEncode($configFile)
$url = "http://localhost:8000/api/v1/control_optimization/mvp/parallel_simulation?case_id=$caseId&config_file=$encodedConfigFile&num_parallel=$numParallel"

Invoke-WebRequest -Uri $url -Method POST | Select-Object -ExpandProperty Content
```

---

## 验收标准

### Phase 1 MVP核心功能验收

#### 1. API可用性 ✅
- [ ] `/api/v1/case/list_cases/` 返回案例列表
- [ ] `/api/v1/simulation/simulations/{case_id}` 返回仿真列表
- [ ] `/api/v1/control_optimization/mvp/parallel_simulation` 启动成功

#### 2. 并行仿真执行 ✅
- [ ] 能够启动5-10个并行SUMO实例
- [ ] 每个实例拥有独立目录（instance_0/, instance_1/, ...）
- [ ] 每个实例有独立的sumocfg、TAZ、e1/、edgedata/子目录
- [ ] 无进程启动失败（Epic1已移除TraCI，使用subprocess）

#### 3. 资源监控 ✅
- [ ] 能够监控CPU使用率
- [ ] 能够监控内存使用量
- [ ] 监控数据保存到Excel文件

#### 4. 车辆统计 ✅
- [ ] 能够统计每个时间点的总车辆数
- [ ] 能够记录峰值车辆数
- [ ] 数据保存到Excel文件,包含时间戳、仿真时间、车辆数

#### 5. 前端界面 ✅
- [ ] MVP专用页面可以正常访问
- [ ] 案例下拉框正常加载
- [ ] 仿真下拉框根据案例动态更新
- [ ] 启动按钮点击后显示执行结果

---

## 常见问题排查

### 问题1: "配置文件不存在"错误

**原因**: 选择的仿真配置尚未生成sumocfg文件

**解决**:
1. 在主OD系统中,导航到"仿真运行"页面
2. 选择该案例
3. 点击"仅准备配置"按钮
4. 等待配置生成完成
5. 重新测试MVP并行仿真

### 问题2: 实例目录创建失败

**原因**: 输出目录权限不足或磁盘空间不足

**解决**:
1. 检查 `cases/{case_id}/control_optimization/` 目录权限
2. 确保有足够的磁盘空间（每个实例约100-200MB）
3. 检查文件系统路径长度限制（Windows MAX_PATH问题）

### 问题3: SUMO进程启动失败

**原因**: SUMO_HOME环境变量未设置或SUMO未安装

**解决**:
```powershell
# 检查SUMO_HOME
echo $env:SUMO_HOME

# 如果为空,设置SUMO_HOME
$env:SUMO_HOME = "C:\Program Files (x86)\Eclipse\Sumo"  # 替换为实际路径
```

### 问题4: 仿真卡住不前进

**原因**: SUMO配置文件中的路径错误或车辆定义有问题

**解决**:
1. 检查实例配置: `cases/{case_id}/control_optimization/batch_config_xxx/instance_X/simulation.sumocfg`
2. 验证路径计算正确（Epic1使用os.path.relpath自动计算）
3. 检查TAZ文件存在: `instance_X/TAZ_6.add.xml`
4. 验证routes文件存在: `cases/{case_id}/config/*.rou.xml`
5. 查看SUMO错误输出（在后台日志中）

---

## 性能基准

### 小规模测试 (10并行实例) ✅ Epic 1已验证

**实际测试结果** (2025-10-02):
- **实例数量**: 10个完全独立实例
- **执行时长**: 603秒 (~10分钟)
- **峰值车辆数**: 取决于OD数据规模
- **架构**: subprocess直接运行，无TraCI通信开销
- **实时比**: ~6.0 (实际时间/仿真时间)
- **测试案例**: case_20250829_175003
- **状态**: ✅ 全部实例成功完成

### 中规模测试 (40并行实例) ⏳ 待验证

**预期指标**:
- **峰值车辆数**: 40-100万辆
- **预期执行时长**: 10-30分钟
- **CPU使用**: 80-95%
- **内存使用**: 4-8GB
- **实时比**: ≥1.0 (目标)

**注意**: 如果峰值车辆数低于预期,检查:
1. SUMO配置的时间范围 (`<time>` 标签)
2. Routes文件的车辆数量
3. OD数据的时间段和流量规模

---

## 下一步计划

Epic 1完成后，进入Phase 2开发:

### Phase 2核心任务 (优先级排序)

**P0任务** (本周):
1. **EdgeData采集与指标计算** (Epic 3)
   - 实现edges.add.xml生成
   - 解析EdgeData输出并计算指标

2. **评分与排名系统** (Epic 4)
   - 实现固定权重评分模型
   - 开发Top3推荐算法

**P1任务** (本周):
3. **结果页面开发** (Epic 5)
   - 展示峰值曲线
   - 显示Top3推荐结果

**P2任务** (下周):
4. **大规模测试**: 验证40-60并行实例
5. **性能优化**: 进一步提升实时比

**详细任务清单**: 参考 [TODO.md](./TODO.md)

### 相关文档
- Epic 1完成报告: [Epic1_完成报告.md](./Epic1_完成报告.md)
- 功能清单: [MVP功能清单.md](./MVP功能清单.md)
- PRD文档: [管控方案优化子系统PRD文档.md](./管控方案优化子系统PRD文档.md)
- 架构设计: [管控方案优化子系统架构设计方案.md](./管控方案优化子系统架构设计方案.md)
