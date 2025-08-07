# 仿真精度分析工具设计方案

## 项目概述

本工具用于分析SUMO交通仿真结果的精度，通过对比仿真输出的检测器数据与真实门架流量数据，计算MAPE和GEH精度指标。

## 需求分析

### 现有系统分析
- **仿真系统**：基于SUMO的交通仿真平台
- **数据源**：OD数据来自PostgreSQL数据库，表名为`dwd_od_weekly`或`dwd_od_g4202`
- **真实流量数据**：来自`gantry_table`（`dwd_flow_gantry`或`dwd_flow_gantry_weekly`）
- **仿真输出**：E1检测器XML格式数据，包含`nVehContrib`字段

### 关键需求
1. **自动时间范围获取**：从run文件夹自动解析仿真时间范围
2. **数据持久化**：防止仿真数据被覆盖，需要保存e1和gantry数据
3. **精度计算**：支持MAPE和GEH两种精度指标
4. **结果输出**：生成CSV报告和可视化图表

## 设计方案

### 1. 文件夹结构

```
accuracy_analysis/
├── __init__.py
├── analyzer.py              # 主分析器类
├── data_loader.py           # 数据加载模块
├── metrics.py              # 精度指标计算
├── report_generator.py     # 报告生成
├── utils.py                # 工具函数
└── accuracy_results_20250806_XXXXXX/  # 结果文件夹
    ├── accuracy_results.csv
    ├── mape_analysis.csv
    ├── geh_analysis.csv
    ├── charts/
    │   ├── mape_chart.png
    │   ├── geh_chart.png
    │   └── scatter_plot.png
    └── accuracy_report.html
```

### 2. 工作流程

```
1. 生成仿真配置 → run_20250804_152456/
2. 运行SUMO仿真 → 输出到sim_scripts/e1/
3. 仿真完成后 → 
   a. 复制e1到run_20250804_152456/e1_20250804_152456/
   b. 从gantry_table获取数据 → run_20250804_152456/gantry_20250804_152456/
4. 精度分析 → 
   a. 从e1_20250804_152456/读取仿真检测器数据
   b. 从gantry_20250804_152456/读取真实门架数据
   c. 生成accuracy_results_20250806_XXXXXX/
```

### 3. 核心功能设计

#### 3.1 自动时间范围获取
- **数据源**：run文件夹中的OD文件名
- **格式**：`dwd_od_weekly_YYYYMMDDHHMMSS_YYYYMMDDHHMMSS.od.xml`
- **解析逻辑**：使用正则表达式提取时间戳并转换为datetime对象

#### 3.2 E1文件夹管理
- **复制时机**：仿真完成后自动执行
- **命名规则**：`e1_YYYYMMDD_HHMMSS`
- **存储位置**：对应的run文件夹内
- **目的**：防止下次仿真覆盖数据

#### 3.3 Gantry数据保存
- **数据源**：PostgreSQL数据库的gantry_table
- **保存格式**：CSV文件
- **文件夹命名**：`gantry_YYYYMMDD_HHMMSS`
- **包含字段**：gantry_id, start_time, k1-k4, h1-h6, total_flow

#### 3.4 精度指标计算

##### MAPE (Mean Absolute Percentage Error)
```
MAPE = (1/n) * Σ(|(simulated - observed) / observed|) * 100%
```

##### GEH (Geoffrey E. Havers)
```
GEH = √((simulated - observed)² / ((simulated + observed) / 2))
```

### 4. API设计

#### 4.1 主分析器类
```python
class AccuracyAnalyzer:
    def __init__(self, run_folder, output_base_folder="accuracy_analysis"):
        self.run_folder = run_folder
        self.e1_folder = self._find_e1_folder()
        self.gantry_folder = self._find_gantry_folder()
        self.start_time, self.end_time = self._parse_time_from_run_folder()
        self.output_folder = self._create_output_folder()
    
    def analyze_accuracy(self):
        """执行完整的精度分析流程"""
        pass
    
    def _parse_time_from_run_folder(self):
        """从run文件夹解析时间范围"""
        pass
    
    def _find_e1_folder(self):
        """查找e1数据文件夹"""
        pass
    
    def _find_gantry_folder(self):
        """查找gantry数据文件夹"""
        pass
```

#### 4.2 数据加载模块
```python
class DataLoader:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def load_gantry_data(self, start_time, end_time, gantry_ids):
        """从数据库加载gantry数据"""
        pass
    
    def load_detector_data(self, e1_folder):
        """从XML文件加载检测器数据"""
        pass
    
    def save_gantry_data(self, data, output_folder):
        """保存gantry数据到本地"""
        pass
```

#### 4.3 精度指标计算
```python
class MetricsCalculator:
    @staticmethod
    def calculate_mape(simulated, observed):
        """计算MAPE指标"""
        pass
    
    @staticmethod
    def calculate_geh(simulated, observed):
        """计算GEH指标"""
        pass
    
    def calculate_all_metrics(self, df_sim, df_obs):
        """计算所有精度指标"""
        pass
```

#### 4.4 报告生成
```python
class ReportGenerator:
    def __init__(self, output_folder):
        self.output_folder = output_folder
    
    def generate_csv_report(self, results):
        """生成CSV报告"""
        pass
    
    def generate_html_report(self, results):
        """生成HTML报告"""
        pass
    
    def generate_charts(self, results):
        """生成可视化图表"""
        pass
```

### 5. 数据格式规范

#### 5.1 Gantry数据格式
```csv
gantry_id,start_time,k1,k2,k3,k4,h1,h2,h3,h4,h5,h6,total_flow
G420151001000510010,2025-07-21 08:00:00,120,80,60,40,30,25,20,15,10,5,495
G420151001000510010,2025-07-21 08:05:00,115,75,58,38,28,23,18,14,9,4,472
```

#### 5.2 检测器数据格式
```xml
<?xml version="1.0" encoding="UTF-8"?>
<detector>
    <interval begin="0" end="300" nVehContrib="25"/>
    <interval begin="300" end="600" nVehContrib="32"/>
</detector>
```

#### 5.3 精度结果格式
```csv
gantry_id,interval_start,sim_flow,obs_flow,mape,geh
G420151001000510010,0,25,28,10.71,0.58
G420151001000510010,300,32,30,6.67,0.36
```

### 6. 集成方案

#### 6.1 仿真API集成
```python
@app.post("/run_simulation/")
async def run_simulation(request: SimulationRequest):
    # 运行仿真
    result = run_sumo(...)
    
    # 仿真完成后自动保存数据
    if not request.gui:
        save_simulation_data(request.run_folder)
    
    return {"status": "completed", "run_folder": request.run_folder}
```

#### 6.2 精度分析API
```python
@app.post("/analyze_accuracy/")
async def analyze_accuracy(request: AccuracyAnalysisRequest):
    analyzer = AccuracyAnalyzer(request.run_folder)
    results = analyzer.analyze_accuracy()
    return {"success": True, "results": results}
```

### 7. 配置参数

#### 7.1 数据库配置
```python
DB_CONFIG = {
    "dbname": "sdzg",
    "user": "lsrns", 
    "password": "Abcd@1234",
    "host": "10.149.235.123",
    "port": "5432"
}
```

#### 7.2 精度分析配置
```python
ANALYSIS_CONFIG = {
    "time_interval": 5,  # 分钟
    "mape_threshold": 15,  # MAPE阈值
    "geh_threshold": 5,   # GEH阈值
    "output_formats": ["csv", "html", "charts"]
}
```

### 8. 错误处理

#### 8.1 数据缺失处理
- 检测器数据缺失：跳过对应时间段
- Gantry数据缺失：尝试从数据库重新获取
- 时间不匹配：按最近时间段对齐

#### 8.2 数据验证
- 检查时间范围有效性
- 验证数据完整性
- 处理异常值和缺失值

### 9. 性能优化

#### 9.1 数据缓存
- 缓存gantry数据避免重复查询
- 使用本地存储的检测器数据
- 增量式数据处理

#### 9.2 并发处理
- 支持多个检测器文件并行读取
- 数据库查询优化
- 批量数据处理

## 实施计划

1. **阶段1**：创建基础架构和文件夹结构
2. **阶段2**：实现数据加载和保存功能
3. **阶段3**：实现精度指标计算
4. **阶段4**：实现报告生成功能
5. **阶段5**：集成测试和优化

## 风险评估

1. **数据风险**：数据库连接失败、数据格式变化
2. **性能风险**：大量数据处理时间过长
3. **兼容性风险**：SUMO版本更新导致输出格式变化
4. **存储风险**：磁盘空间不足导致数据保存失败

## 扩展性考虑

1. **支持更多精度指标**：RMSE、MAE、R²等
2. **支持更多数据源**：其他类型的检测器数据
3. **分布式处理**：支持大规模数据处理
4. **实时分析**：支持实时精度监控