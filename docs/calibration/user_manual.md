# SUMO参数标定功能用户使用手册

## 📋 概述

本手册详细介绍如何使用SUMO参数标定功能来优化仿真参数，提高仿真精度和车辆容量。标定功能采用GA+XGBoost混合优化算法，能够自动找到最适合您交通场景的SUMO参数组合。

## 🎯 功能特点

- **智能优化**: 使用遗传算法+机器学习代理模型，自动寻找最优参数
- **场景适配**: 支持高流量、低流量、混合交通三种场景
- **并行计算**: 支持多进程并行仿真，大幅提升标定效率
- **实时监控**: 提供任务进度监控和实时状态查询
- **结果分析**: 自动生成标定报告和优化建议

## 🚀 快速开始

### 1. 准备工作

在开始标定之前，请确保：

- ✅ 已创建仿真案例
- ✅ 已配置网络文件和TAZ文件
- ✅ 已运行过基础仿真，了解当前参数效果
- ✅ 系统资源充足（建议至少4GB内存，4核CPU）

### 2. 选择交通场景

根据您的实际交通情况，选择合适的场景类型：

| 场景类型 | 适用情况 | 特点 |
|----------|----------|------|
| **高流量拥堵场景** | 早晚高峰、商业区、学校周边 | 车辆密度高，经常拥堵，需要优化插入成功率和路网容量 |
| **低流量畅通场景** | 夜间、郊区、工业园区 | 车辆密度低，交通流畅，重点优化行驶体验和仿真精度 |
| **混合交通场景** | 一般城市道路、混合时段 | 平衡各种指标，适合大多数情况 |

### 3. 启动标定任务

#### 方式一：通过Web界面

1. 登录系统，进入案例管理页面
2. 选择要标定的案例，点击"分析"按钮
3. 在分析类型中选择"参数标定"
4. 配置标定参数：
   - 选择交通场景
   - 设置初始采样数量（建议100-200）
   - 设置最大优化代数（建议100-200）
   - 配置并行工作进程数（建议4-8）
5. 点击"开始标定"按钮

#### 方式二：通过API接口

```bash
curl -X POST "http://localhost:8000/api/v1/calibration/create" \
     -H "Content-Type: application/json" \
     -d '{
         "case_id": "your_case_id",
         "scenario": "high_traffic",
         "network_file": "path/to/network.net.xml",
         "taz_file": "path/to/taz.add.xml",
         "simulation_duration": 7200,
         "initial_samples": 100,
         "max_generations": 100,
         "parallel_workers": 4
     }'
```

### 4. 监控标定进度

标定任务启动后，您可以通过以下方式监控进度：

#### 查看任务状态

```bash
curl "http://localhost:8000/api/v1/calibration/status/your_task_id"
```

#### 查看活跃任务列表

```bash
curl "http://localhost:8000/api/v1/calibration/active-tasks"
```

#### 任务状态说明

- **pending**: 等待执行
- **running**: 正在执行（会显示进度百分比）
- **completed**: 执行完成
- **failed**: 执行失败
- **cancelled**: 已取消

### 5. 获取标定结果

标定完成后，获取结果：

```bash
curl "http://localhost:8000/api/v1/calibration/results/your_case_id"
```

## ⚙️ 参数配置详解

### 1. 基础配置参数

| 参数名 | 说明 | 建议值 | 影响 |
|--------|------|--------|------|
| **initial_samples** | 初始采样数量 | 100-200 | 数量越多，初始模型越准确，但耗时越长 |
| **max_generations** | 最大优化代数 | 100-200 | 代数越多，优化效果越好，但可能过拟合 |
| **parallel_workers** | 并行工作进程数 | 4-8 | 根据CPU核心数设置，建议不超过CPU核心数 |
| **convergence_threshold** | 收敛阈值 | 0.01 | 值越小，收敛越精确，但耗时越长 |

### 2. 高级配置参数

#### 自定义参数范围

如果您对某些SUMO参数有特殊要求，可以自定义参数范围：

```json
{
    "custom_parameter_ranges": {
        "departSpeed": {
            "min": 2.0,
            "max": 4.0
        },
        "minGap": {
            "min": 1.5,
            "max": 2.5
        }
    }
}
```

#### 输出配置

控制仿真输出文件的生成：

```json
{
    "output_config": {
        "summary": true,      // 仿真汇总信息
        "tripinfo": true,     // 车辆行程信息
        "vehroute": false,    // 车辆路径信息（文件较大）
        "queue": false        // 排队信息
    }
}
```

## 📊 结果解读

### 1. 标定结果结构

标定完成后，系统会生成以下结果：

```
cases/your_case_id/results/calibration/
├── calibration_results.json      # 完整标定结果
├── analysis_report.json          # 分析报告
└── best_parameters.json         # 最优参数组合
```

### 2. 关键指标说明

#### 仿真精度指标

| 指标 | 说明 | 目标值 | 优化建议 |
|------|------|--------|----------|
| **flow_error** | 流量误差 | < 0.15 | 误差过大时，调整departSpeed和departLane |
| **delay_error** | 延误误差 | < 0.10 | 误差过大时，调整minGap和sigma |
| **insertion_rate** | 插入成功率 | > 0.95 | 成功率低时，调整maxDepartDelay和minGap |

#### 路网性能指标

| 指标 | 说明 | 目标值 | 优化建议 |
|------|------|--------|----------|
| **network_utilization** | 路网利用率 | > 0.80 | 利用率低时，调整sigma和laneChangeMode |
| **traffic_stability** | 交通稳定性 | > 0.85 | 稳定性差时，调整impatience和laneChangeMode |

### 3. 最优参数组合

系统会输出经过优化后的最佳参数组合，例如：

```json
{
    "departSpeed": 2.5,
    "departLane": "random",
    "minGap": 1.8,
    "sigma": 0.25,
    "impatience": 0.6,
    "laneChangeMode": 512,
    "maxDepartDelay": 450
}
```

### 4. 优化建议

系统会根据标定结果自动生成优化建议：

- **流量误差较大**: 建议调整departSpeed和departLane参数
- **插入成功率较低**: 建议优化minGap和maxDepartDelay参数
- **路网利用率不足**: 建议调整sigma和laneChangeMode参数

## 🔧 使用技巧

### 1. 参数选择策略

#### 高流量场景优化

```json
{
    "scenario": "high_traffic",
    "initial_samples": 150,
    "max_generations": 150,
    "parallel_workers": 6
}
```

**推荐参数组合**:
- `departSpeed`: 2.0-3.0（中等速度，平衡插入成功率和交通流）
- `departLane`: "random"（随机车道，提高分布均匀性）
- `minGap`: 1.5-2.0（较小间距，提高路网容量）
- `sigma`: 0.2-0.3（适度随机性）
- `impatience`: 0.5-0.6（保守驾驶）
- `laneChangeMode`: 512（限制性变道）
- `maxDepartDelay`: 450-600（较长等待时间）

#### 低流量场景优化

```json
{
    "scenario": "low_traffic",
    "initial_samples": 100,
    "max_generations": 100,
    "parallel_workers": 4
}
```

**推荐参数组合**:
- `departSpeed`: "max"（最大速度，提高行驶效率）
- `departLane`: "free"（自由车道选择）
- `minGap`: 2.0-2.5（标准间距）
- `sigma`: 0.3-0.4（适度随机性）
- `impatience`: 0.6-0.7（正常驾驶行为）
- `laneChangeMode`: 1621（标准变道模式）
- `maxDepartDelay`: 300-450（标准等待时间）

### 2. 标定流程优化

#### 分阶段标定

对于复杂场景，建议采用分阶段标定：

1. **第一阶段**: 使用较小样本数（50-100）快速获得大致方向
2. **第二阶段**: 基于第一阶段结果，使用较大样本数（150-200）精细优化
3. **第三阶段**: 在最优参数附近进行局部搜索

#### 参数敏感性分析

在标定过程中，注意观察不同参数对结果的影响：

- **高敏感性参数**: departSpeed, minGap, sigma
- **中等敏感性参数**: departLane, impatience
- **低敏感性参数**: laneChangeMode, maxDepartDelay

### 3. 资源管理

#### 内存优化

- 避免同时运行多个大型标定任务
- 监控系统内存使用情况
- 必要时调整parallel_workers数量

#### 时间管理

- 预估标定时间：初始采样 + 优化代数 × 平均仿真时间
- 建议在系统负载较低时运行标定任务
- 可以设置任务优先级

## 🚨 常见问题

### 1. 标定任务失败

**问题**: 标定任务执行失败，状态显示"failed"

**可能原因**:
- 网络文件或TAZ文件路径错误
- 仿真配置参数无效
- 系统资源不足
- SUMO执行错误

**解决方案**:
1. 检查文件路径是否正确
2. 验证仿真配置参数
3. 检查系统资源使用情况
4. 查看错误日志获取详细信息

### 2. 标定结果不理想

**问题**: 标定完成后，仿真精度仍然较低

**可能原因**:
- 初始采样数量不足
- 优化代数不够
- 参数范围设置不合理
- 交通场景选择不当

**解决方案**:
1. 增加initial_samples数量（建议200-300）
2. 增加max_generations数量（建议200-300）
3. 检查并调整参数范围设置
4. 重新评估交通场景类型

### 3. 标定时间过长

**问题**: 标定任务执行时间远超预期

**可能原因**:
- 仿真时长设置过长
- 并行进程数设置过少
- 系统资源不足
- 网络文件过大

**解决方案**:
1. 适当减少simulation_duration
2. 增加parallel_workers数量
3. 检查系统资源使用情况
4. 考虑简化网络文件

### 4. 内存不足

**问题**: 标定过程中出现内存不足错误

**可能原因**:
- 并行进程数过多
- 仿真输出文件过大
- 系统内存不足

**解决方案**:
1. 减少parallel_workers数量
2. 减少仿真输出文件
3. 关闭其他占用内存的程序
4. 考虑增加系统内存

## 📈 性能优化建议

### 1. 硬件配置建议

| 组件 | 最低配置 | 推荐配置 | 高性能配置 |
|------|----------|----------|------------|
| **CPU** | 4核 | 8核 | 16核+ |
| **内存** | 8GB | 16GB | 32GB+ |
| **存储** | SSD 256GB | SSD 512GB | NVMe 1TB+ |
| **网络** | 千兆 | 千兆 | 万兆 |

### 2. 软件配置优化

#### 操作系统优化

- 使用64位操作系统
- 关闭不必要的系统服务
- 调整虚拟内存设置
- 使用SSD存储

#### Python环境优化

- 使用Python 3.8+
- 安装性能优化库（numba, cython等）
- 使用虚拟环境管理依赖
- 定期清理临时文件

### 3. 标定策略优化

#### 算法参数调优

- 根据问题规模调整种群大小
- 优化交叉和变异概率
- 使用自适应参数调整
- 实现早停机制

#### 并行策略优化

- 根据CPU核心数设置并行度
- 使用进程池而非线程池
- 实现负载均衡
- 监控资源使用情况

## 🔮 高级功能

### 1. 批量标定

对于多个相似案例，可以使用批量标定功能：

```python
# 批量标定示例
cases = ["case_001", "case_002", "case_003"]
scenarios = ["high_traffic", "mixed_traffic", "low_traffic"]

for case_id, scenario in zip(cases, scenarios):
    # 创建标定任务
    task = create_calibration_task(case_id, scenario)
    # 监控任务状态
    monitor_task(task["task_id"])
```

### 2. 参数迁移

将已标定的参数应用到新案例：

```python
# 参数迁移示例
source_case = "case_001"
target_case = "case_002"

# 获取源案例的最优参数
source_params = get_best_parameters(source_case)

# 应用到目标案例
apply_parameters(target_case, source_params)
```

### 3. 标定结果对比

比较不同标定策略的效果：

```python
# 结果对比示例
strategies = ["ga_only", "ga_xgboost", "custom"]
results = {}

for strategy in strategies:
    result = run_calibration_with_strategy(case_id, strategy)
    results[strategy] = result

# 生成对比报告
generate_comparison_report(results)
```

## 📚 相关资源

### 1. 文档链接

- [标定策略设计](../design/calibration_strategy.md)
- [参数影响分析](../design/parameter_analysis.md)
- [评估指标定义](../design/evaluation_metrics.md)
- [API接口参考](./api_reference.md)
- [集成指南](./integration_guide.md)

### 2. 技术支持

- **技术文档**: 查看项目文档目录
- **问题反馈**: 通过GitHub Issues提交问题
- **功能建议**: 通过项目讨论区提出建议
- **技术支持**: 联系项目维护团队

### 3. 学习资源

- **SUMO官方文档**: https://sumo.dlr.de/docs/
- **遗传算法教程**: 推荐相关机器学习课程
- **交通仿真理论**: 了解交通流理论和仿真原理
- **Python编程**: 掌握Python基础编程技能

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2024-12-01 | 初始版本，包含基础标定功能 |
| v1.1.0 | 待定 | 计划添加批量标定和参数迁移功能 |
| v1.2.0 | 待定 | 计划添加更多优化算法和评估指标 |

---

**注意**: 本手册会随着功能更新持续完善，建议定期查看最新版本。如有疑问或建议，请通过项目渠道反馈。
