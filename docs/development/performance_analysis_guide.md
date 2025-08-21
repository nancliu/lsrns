# 性能分析功能使用指南

## 📋 功能概述

性能分析是OD生成脚本系统的三大核心分析功能之一，专门用于分析仿真运行效率、数据处理性能和输出结果统计。该功能保持简单实用，专注于从现有数据中提取有价值的性能指标。

## 🎯 核心功能

### 1. **仿真运行性能分析**
- **仿真统计**: 总步数、车辆数量（加载/插入/运行/等待/结束）
- **执行效率**: 仿真完成率、资源使用情况
- **性能对比**: 多仿真结果之间的性能对比

### 2. **数据处理性能分析**
- **E1文件统计**: 文件数量、大小分布、记录数统计
- **处理效率**: 数据文件处理效率评估
- **资源使用**: 文件大小分布和统计信息

### 3. **输出结果性能分析**
- **输出统计**: 图表数量、CSV文件数量、报告大小
- **生成效率**: 分析输出生成效率
- **文件管理**: 输出文件大小和数量统计

## 🏗️ 技术架构

### **核心组件**
```
PerformanceAnalyzer (性能分析器)
├── 仿真性能分析
├── 数据处理性能分析
├── 输出结果性能分析
├── 性能指标计算
├── 图表生成
├── 报告生成
└── CSV导出
```

### **数据流**
```
仿真结果 → summary.xml解析 → 性能指标计算 → 图表生成 → 报告输出
E1数据 → 文件统计 → 处理效率评估 → 性能分析
分析输出 → 文件统计 → 输出效率评估 → 性能报告
```

## 📊 性能指标体系

### **仿真运行指标**
- `total_steps`: 总仿真步数
- `total_loaded`: 总加载车辆数
- `total_inserted`: 总插入车辆数
- `max_running`: 最大运行车辆数
- `max_waiting`: 最大等待车辆数
- `total_ended`: 总结束车辆数

### **数据处理指标**
- `total_e1_files`: E1文件总数
- `total_e1_records`: 有效记录总数
- `e1_size_stats`: 文件大小统计（总大小、平均大小、最小/最大大小）

### **输出结果指标**
- `total_charts`: 图表总数
- `total_csv_files`: CSV文件总数
- `total_output_size_bytes`: 输出总大小

### **综合效率指标**
- `efficiency_score`: 综合效率评分 (0-1)
- `data_processing_efficiency`: 数据处理效率
- `output_efficiency`: 输出生成效率
- `efficiency_level`: 效率等级（优秀/良好/一般/待改进）

## 🚀 使用方法

### **API调用**
```python
# 性能分析请求
POST /api/v1/analyze_performance/
{
    "case_id": "case_001",
    "simulation_ids": ["sim_001", "sim_002"],
    "analysis_type": "performance"
}
```

### **Python代码调用**
```python
from shared.analysis_tools.performance_analysis import PerformanceAnalyzer

# 创建分析器
analyzer = PerformanceAnalyzer()
analyzer.set_output_dirs("charts", "reports")

# 执行分析
results = analyzer.analyze_performance(
    case_root=Path("cases/case_001"),
    simulation_folders=[Path("sim_001"), Path("sim_002")],
    simulation_ids=["sim_001", "sim_002"]
)
```

## 📈 输出内容

### **生成文件**
- **图表文件**: 仿真性能对比图、数据处理性能图、输出结果统计图
- **报告文件**: Markdown格式的性能分析报告
- **CSV文件**: 仿真性能数据、数据处理性能数据、输出结果性能数据

### **报告内容**
- 报告概览和总体效率评分
- 仿真运行性能详细分析
- 数据处理性能统计
- 输出结果性能评估
- 性能图表展示
- 性能优化建议

## 🔧 配置选项

### **输出目录设置**
```python
analyzer.set_output_dirs(
    charts_dir="path/to/charts",    # 图表输出目录
    reports_dir="path/to/reports"   # 报告输出目录
)
```

### **效率评分阈值**
- **优秀**: ≥ 0.8
- **良好**: ≥ 0.6
- **一般**: ≥ 0.4
- **待改进**: < 0.4

## 📝 使用示例

### **完整分析流程**
```python
# 1. 准备数据
case_root = Path("cases/test_case")
simulation_folders = [
    case_root / "simulations" / "sim_001",
    case_root / "simulations" / "sim_002"
]
simulation_ids = ["sim_001", "sim_002"]

# 2. 创建分析器
analyzer = PerformanceAnalyzer()
analyzer.set_output_dirs("output/charts", "output/reports")

# 3. 执行分析
results = analyzer.analyze_performance(
    case_root, simulation_folders, simulation_ids
)

# 4. 查看结果
print(f"分析完成，耗时: {results['analysis_duration_seconds']:.2f}秒")
print(f"生成图表: {len(results['chart_files'])} 个")
print(f"效率评分: {results['overall_performance']['efficiency_score']:.2f}")
```

## ⚠️ 注意事项

### **数据要求**
- 仿真结果必须包含 `summary.xml` 文件
- E1检测器数据应位于 `simulation/e1/` 目录
- 分析输出目录需要适当的写入权限

### **性能考虑**
- 大文件处理时注意内存使用
- 图表生成可能耗时较长
- 建议在后台异步执行长时间分析

### **错误处理**
- 文件不存在时会跳过相关分析
- 解析失败会记录错误日志
- 返回空结果表示分析失败

## 🔄 扩展功能

### **未来增强**
- 性能趋势分析
- 性能基准测试
- 自动化性能监控
- 性能告警机制

### **自定义指标**
- 支持用户定义性能指标
- 可配置的评分算法
- 灵活的图表样式

## 📚 相关文档

- [精度分析设计文档](accuracy_analysis_design.md)
- [机理分析模块](../shared/analysis_tools/mechanism_analysis.py)
- [API使用指南](../api_docs/README.md)

---

*文档版本: v1.0 | 最后更新: 2025-01-20*
