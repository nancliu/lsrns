# 门架数据CSV生成优化说明

## 概述

本文档说明门架数据CSV生成的优化方案，包括两个主要CSV文件的生成逻辑和门架-E1检测器映射关系的建立。

## 优化目标

1. **生成贴合数据库表结构的原始数据文件** (`gantry_data_raw.csv`)
2. **生成贴合XML数据的分析文件** (`e1_detector_data.csv`)
3. **建立门架ID和E1检测器ID的映射关系**

## CSV文件结构

### 1. gantry_data_raw.csv - 门架原始数据

**目标**: 贴合数据库表 `dwd.dwd_flow_gantry_weekly` 的结构

**包含字段**:
- `gantry_id`: 门架ID（对应 `start_gantryid`）
- `start_time`: 开始时间
- `flow`: 总流量（对应 `total`）
- `speed`: 平均速度（对应 `avg_speed`）
- `k1`, `k2`, `k3`, `k4`: 客车分类流量
- `h1`, `h2`, `h3`, `h4`, `h5`, `h6`: 货车分类流量
- `t1`, `t2`, `t3`, `t4`, `t5`, `t6`: 特种车分类流量
- `total_k`, `total_h`, `total_t`: 分类总流量
- `avg_duration`: 平均耗时
- `distance`: 距离

**用途**: 数据存档、原始数据查看、数据质量检查

### 2. e1_detector_data.csv - E1检测器数据

**目标**: 贴合仿真E1检测器XML数据的结构

**包含字段**:
- `gantry_id`: 门架ID（重命名自 `detector_id`）
- `start_time`: 开始时间（重命名自 `begin`）
- `end_time`: 结束时间（重命名自 `end`）
- `flow`: 流量
- `occupancy`: 占有率
- `speed`: 速度

**用途**: 精度分析、仿真数据对比、性能评估

## 门架-E1检测器映射关系

### 映射策略

1. **默认映射**: 门架ID = 检测器ID（1:1关系）
2. **手动配置**: 通过管理界面配置精确映射关系
3. **自动生成**: 基于地理位置和道路网络自动生成映射

### 映射实现

在 `GantryDataLoader` 类中实现：
- `load_gantry_detector_mapping()`: 加载映射关系
- `_create_default_mapping()`: 创建默认映射
- `get_detector_data_for_gantry()`: 根据门架ID获取检测器数据

## 技术实现

### 1. 门架数据加载器优化

**新增方法**:
- `load_gantry_data_for_analysis()`: 加载分析格式的门架数据
- `load_gantry_detector_mapping()`: 加载映射关系
- `_create_default_mapping()`: 创建默认映射

**数据格式**:
- 原始数据：保持数据库表结构，不添加计算字段
- 分析数据：适配精度分析需要的格式

### 2. 精度分析器CSV导出优化

**新增CSV文件**:
- `gantry_data_raw.csv`: 门架原始数据
- `e1_detector_data.csv`: E1检测器数据
- `gantry_accuracy_analysis.csv`: 门架级别精度分析
- `time_accuracy_analysis.csv`: 时间级别精度分析

**导出逻辑**:
```python
def _export_csvs(self, simulated_data, observed_data, metrics):
    exports = {}
    
    # 1. 精度指标汇总
    exports.update(self._export_basic_metrics(metrics))
    
    # 2. 门架原始数据（贴合数据库结构）
    exports.update(self._export_gantry_raw_data(observed_data))
    
    # 3. E1检测器数据（贴合XML结构）
    exports.update(self._export_e1_detector_data(simulated_data))
    
    # 4. 详细对比数据
    exports.update(self._export_detailed_comparison(simulated_data, observed_data))
    
    # 5. 门架级别精度分析
    exports.update(self._export_gantry_accuracy(simulated_data, observed_data))
    
    # 6. 时间级别精度分析
    exports.update(self._export_time_accuracy(simulated_data, observed_data))
    
    # 7. 异常检测结果
    exports.update(self._export_anomaly_detection(simulated_data, observed_data))
    
    return exports
```

## 使用流程

### 1. 精度分析执行

```python
# 分析服务会自动：
# 1. 检查现有门架数据
# 2. 从数据库加载门架数据（如果需要）
# 3. 建立门架-E1检测器映射
# 4. 执行精度分析
# 5. 生成优化的CSV文件
```

### 2. 结果查看

生成的分析结果包含：
- **HTML报告**: 可视化精度分析结果
- **图表文件**: 各种精度指标的可视化图表
- **CSV文件**: 结构化的数据文件，便于后续分析

## 优化效果

### 1. 数据一致性

- 门架原始数据完全贴合数据库表结构
- E1检测器数据贴合仿真XML数据结构
- 映射关系清晰，便于数据对齐

### 2. 分析精度

- 基于置信度的权重计算
- 多维度精度指标（门架级别、时间级别）
- 异常数据识别和标记

### 3. 可维护性

- 模块化的数据加载逻辑
- 清晰的映射关系管理
- 完善的错误处理和日志记录

## 注意事项

1. **映射关系维护**: 定期检查和更新门架-E1检测器映射关系
2. **数据同步**: 确保门架数据与仿真数据的时间范围一致
3. **性能优化**: 大量数据时考虑分批处理和缓存机制
4. **错误处理**: 映射失败时使用默认映射，确保分析流程不中断

## 后续扩展

1. **智能映射**: 基于机器学习自动优化映射关系
2. **实时更新**: 支持实时门架数据更新和分析
3. **多源数据**: 支持多种门架数据源的统一处理
4. **可视化映射**: 提供图形化界面管理映射关系

## 总结

通过本次优化，门架数据的CSV生成更加贴合实际需求：
- 原始数据文件保持数据库表结构的完整性，不添加不必要的计算字段
- 分析数据文件便于精度计算和分析
- 映射关系建立为后续分析提供数据对齐基础

这些优化为门架数据的精度分析提供了更加可靠和高效的数据基础。
