# MVP并行仿真功能清单

**版本**: v1.2
**更新日期**: 2025-10-02
**状态**: ✅ Epic 1 完成并验证通过

---

## 功能概览

MVP并行仿真系统包含两大核心功能：
1. **批量配置生成** - 为并行仿真生成配置文件和元数据
2. **并行仿真执行** - 启动多个SUMO实例并行运行

---

## 1. 批量配置生成

### 功能描述
基于现有的案例和仿真配置，生成批量并行仿真所需的配置文件和元数据。

### 核心特性
- ✅ **共享配置模式**: 所有并行实例共享同一个sumocfg配置文件
- ✅ **端口自动分配**: 自动分配8813-8913端口范围，避免冲突
- ✅ **元数据管理**: 生成batch_metadata.json记录批次信息
- ✅ **实例清单**: 生成instances.json记录每个实例的端口分配

### 技术实现

**后端组件**:
- 文件: [shared/utilities/control_optimization/batch_config_generator.py](../../../shared/utilities/control_optimization/batch_config_generator.py)
- 核心类: `BatchConfigGenerator`
- 便捷函数: `generate_batch_configs_for_case()`

**API端点**:
```
POST /api/v1/control_optimization/mvp/generate_batch_configs
参数:
  - case_id: 案例ID
  - simulation_id: 模板仿真ID
  - num_configs: 配置数量（默认40）
```

**响应示例**:
```json
{
  "status": "success",
  "message": "成功生成批量配置，40个实例共享配置文件",
  "batch_id": "batch_config_1001_120000",
  "case_id": "case_20250923_143156",
  "template_simulation_id": "sim_0926_152911_micro",
  "num_configs": 40,
  "config_type": "shared",
  "output_directory": "cases/case_20250923_143156/control_optimization/batch_config_1001_120000",
  "shared_config_file": "cases/.../simulation.sumocfg",
  "metadata_file": "cases/.../batch_metadata.json",
  "instances_file": "cases/.../instances.json",
  "created_at": "2025-10-01T12:00:00"
}
```

### 生成文件结构

```
cases/{case_id}/control_optimization/batch_config_{timestamp}/
├── simulation.sumocfg          # 共享SUMO配置文件（复制自模板）
├── batch_metadata.json         # 批次元数据
│   ├── batch_id               # 批次ID
│   ├── case_id                # 案例ID
│   ├── template_simulation_id # 模板仿真ID
│   ├── num_parallel           # 并行数量
│   ├── config_type: "shared"  # 配置类型
│   ├── status: "pending"      # 批次状态
│   └── created_at             # 创建时间
└── instances.json              # 实例列表
    └── [
          {
            "instance_id": 0,
            "instance_name": "parallel_instance_0",
            "port": 8813,
            "config_file": "path/to/simulation.sumocfg",
            "status": "pending"
          },
          ...
        ]
```

### 使用场景
1. **配置检查**: 生成配置后，先检查配置文件是否正确，再启动仿真
2. **批量准备**: 一次性准备多个批次的配置，按需启动
3. **配置复用**: 保存生成的配置，用于后续重复实验

---

## 2. 并行仿真执行

### 功能描述
基于配置文件启动多个SUMO实例并行运行，实时监控资源使用和车辆统计。

### 核心特性
- ✅ **多进程并行**: 使用multiprocessing启动多个独立SUMO进程
- ✅ **共享配置**: 所有实例共享同一sumocfg，通过端口隔离
- ✅ **实时监控**: 独立线程监控CPU/内存使用
- ✅ **车辆统计**: 收集每个时间步的总车辆数和峰值
- ✅ **数据导出**: Excel格式保存所有监控数据

### 技术实现

**后端组件**:
- 文件: [shared/utilities/control_optimization/parallel_simulator.py](../../../shared/utilities/control_optimization/parallel_simulator.py)
- 核心类:
  - `ParallelSimulator` - 主执行器
  - `SimulationTimer` - 执行时长统计
  - `ResourceMonitor` - 资源监控器

**API端点**:
```
POST /api/v1/control_optimization/mvp/parallel_simulation
参数:
  - case_id: 案例ID
  - simulation_id: 仿真ID（使用其sumocfg）
  - num_parallel: 并行数量（默认40）
```

**响应示例**:
```json
{
  "status": "started",
  "message": "并行仿真已在后台启动",
  "case_id": "case_20250923_143156",
  "simulation_id": "sim_0926_152911_micro",
  "num_parallel": 40,
  "config_path": "cases/.../simulation.sumocfg",
  "output_dir": "cases/.../parallel_sim_1001_120000",
  "timestamp": "2025-10-01T12:00:00"
}
```

### 输出文件

```
cases/{case_id}/control_optimization/parallel_sim_{timestamp}/
└── parallel_simulation_{timestamp}.xlsx
    ├── 列: 时间戳
    ├── 列: 仿真时间(s)
    ├── 列: 总车辆数
    ├── 列: 主程序CPU%
    ├── 列: 主程序内存(MB)
    ├── 列: 子进程X CPU%
    ├── 列: 子进程X 内存(MB)
    ├── 列: SUMO进程X CPU%
    └── 列: SUMO进程X 内存(MB)
```

### 监控参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `data_collection_interval` | 10步 | 车辆数据收集间隔 |
| `resource_collection_interval` | 30步 | 资源数据收集间隔 |
| `resource_monitor_interval` | 5秒 | 资源监控更新间隔 |

---

## 3. 前端界面

### 访问地址
```
http://localhost:8000/control_optimization/mvp_parallel_simulation.html
```

### 界面功能

**区域1: 案例和仿真选择**
- 案例下拉框（复用 `/api/v1/case/list_cases/`）
- 仿真下拉框（复用 `/api/v1/simulation/simulations/{case_id}`）
- 动态联动：选择案例后自动加载仿真列表

**区域2: 并行仿真参数**
- 并行数量输入框（默认10，范围1-100）
- MVP建议：10-40个实例

**区域3: 操作按钮**
- **仅生成配置文件** - 调用配置生成API
- **生成配置并启动仿真** - 调用并行仿真API
- **刷新案例列表** - 重新加载案例数据

**区域4: 执行结果**
- JSON格式展示API响应
- 状态标识（已启动/已完成/错误）

---

## 4. 测试工具

### 测试脚本

| 脚本名称 | 功能 | 运行命令 |
|---------|------|---------|
| [test_batch_config_generation.py](../../../test_batch_config_generation.py) | 测试批量配置生成 | `python test_batch_config_generation.py` |
| [test_mvp_api.py](../../../test_mvp_api.py) | 测试完整并行仿真流程 | `python test_mvp_api.py` |
| [test_mvp_parallel_simulation.py](../../../test_mvp_parallel_simulation.py) | 直接调用ParallelSimulator | `python test_mvp_parallel_simulation.py` |

### 测试文档
- [MVP测试指南.md](./MVP测试指南.md) - 完整测试流程和验收标准

---

## 5. MVP验收标准

### Phase 1核心功能 ✅

#### 批量配置生成
- [x] API端点可用
- [x] 生成共享配置文件
- [x] 生成批次元数据
- [x] 生成实例清单
- [x] 端口自动分配无冲突
- [x] 前端界面集成

#### 并行仿真执行
- [x] 启动多个SUMO实例（10实例验证通过）
- [x] 实例完全独立（独立目录+配置+TAZ+e1/+edgedata/）
- [x] 移除TraCI依赖（改用subprocess直接运行）
- [x] 自动路径计算（os.path.relpath）
- [x] 执行时长统计（SimulationTimer）
- [x] 前端界面集成

#### 系统集成
- [x] 独立页面访问
- [x] 复用主系统API
- [x] 不影响主系统功能
- [x] 完整的测试覆盖

---

## 6. 性能指标

### 小规模测试（10并行）✅ 已验证
- **实际测试日期**: 2025-10-02
- **执行时长**: 603秒（约10分钟）
- **实例数量**: 10个完全独立的实例
- **配置**: case_20250829_175003, batch_config_1002_150604
- **输出**: 每个实例独立的 summary.xml + tripinfo.xml + e1/
- **状态**: ✅ 全部成功完成

### 中规模测试（40并行）
- **峰值车辆数**: 40-100万辆
- **执行时长**: 10-30分钟
- **CPU使用**: 80-95%
- **内存使用**: 4-8GB

---

## 7. 技术架构

### 模块依赖关系（2025-10-02更新）

```
前端 (mvp_parallel_simulation.html)
  ↓
API Routes (control_optimization_routes.py)
  ├─→ BatchConfigGenerator (批量配置生成)
  │    └─→ 文件系统 (cases/{case_id}/control_optimization/)
  │
  └─→ ParallelSimulator (并行仿真执行)
       ├─→ SimulationTimer (时长统计)
       ├─→ multiprocessing (多进程)
       ├─→ subprocess (直接运行SUMO，移除TraCI依赖)
       └─→ 实例独立目录 (instance_0/, instance_1/, ...)
            ├─→ simulation.sumocfg (动态生成，路径自动计算)
            ├─→ TAZ_6.add.xml (复制自模板)
            ├─→ e1/ (E1检测器输出)
            ├─→ edgedata/ (EdgeData输出)
            ├─→ summary.xml
            └─→ tripinfo.xml
```

### 关键设计模式（2025-10-02更新）

1. **实例完全独立模式**: 每个实例拥有独立目录、配置文件、TAZ文件、输出目录
2. **直接运行模式**: 使用subprocess直接运行SUMO，不依赖TraCI（更简单、更稳定）
3. **动态路径计算**: 使用os.path.relpath()自动计算相对路径，适应不同目录层级
4. **后台任务模式**: FastAPI BackgroundTasks异步执行仿真
5. **元数据分层模式**: batch → instance 两级元数据

---

## 8. 后续扩展计划

### Phase 2功能（待开发）

1. **峰值曲线可视化**
   - 实时曲线图展示
   - 历史数据对比
   - 导出图表功能

2. **Top3方案推荐**
   - 多维度评分算法
   - 自动排序和推荐
   - 评分权重配置

3. **批量任务管理**
   - CSV批量导入
   - 任务队列管理
   - 批次结果对比

4. **高级监控**
   - 实时日志流
   - 错误自动诊断
   - 性能瓶颈分析

---

## 9. 常见问题

### Q1: 为什么所有实例共享同一个sumocfg?
**A**: MVP阶段简化配置管理，通过端口隔离实现多实例并行。Phase 2可支持差异化配置。

### Q2: 并行数量上限是多少?
**A**: 理论上限取决于端口范围（8813-8913，共100个端口）和系统资源。建议MVP阶段10-40个。

### Q3: 配置生成和仿真启动可以分离吗?
**A**: 可以。先"仅生成配置文件"检查配置，确认后再启动仿真。

### Q4: 如何查看仿真进度?
**A**: MVP阶段仿真在后台运行，完成后查看输出Excel文件。Phase 2将添加实时进度API。

### Q5: 能否手动修改生成的配置文件?
**A**: 可以。生成配置后，可手动编辑batch_config目录下的simulation.sumocfg文件。

---

## 10. 相关文档

- **测试指南**: [MVP测试指南.md](./MVP测试指南.md)
- **架构设计**: [架构设计方案.md](./架构设计方案.md)
- **PRD文档**: [管控方案优化子系统PRD文档.md](./管控方案优化子系统PRD文档.md)
- **需求分析**: [管控方案优化子模块需求分析文档.md](./管控方案优化子模块需求分析文档.md)
- **主项目文档**: [CLAUDE.md](../../../CLAUDE.md)
