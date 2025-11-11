# 事件场景生成指南

## 概述

本指南介绍如何从真实交通事件数据批量生成事件场景库，用于交通控制策略的评估和仿真。

## 系统要求

- Python 3.10+
- SUMO 1.19+ (需设置 SUMO_HOME 环境变量)
- pandas, sumolib, xml库
- 网络文件 (sichuan202508v7.net.xml)
- 事件数据CSV (all_extracted_events.csv)

### 环境配置

```bash
# 设置SUMO环境
export SUMO_HOME=/path/to/sumo
export PATH=$SUMO_HOME/bin:$PATH

# 激活Python环境
conda activate od_project

# 验证安装
python scripts/generate_scenarios_from_events.py --help
```

## 快速开始

### 方法1：使用默认参数生成

```bash
cd /d/projects/OD_SIM
python scripts/generate_scenarios_from_events.py
```

这会：
1. 从 `events/all_extracted_events.csv` 加载399条事件
2. 应用默认筛选条件（事件时长0.5-3小时）
3. 选择18个代表性事件
4. 为每个事件生成3个控制策略（VSS、DHS、TEC）
5. 生成 ~54 个场景配置文件
6. 在 `output/scenarios/` 中输出结果

### 方法2：自定义参数

```bash
python scripts/generate_scenarios_from_events.py \
    --target-events 30 \
    --output-dir /path/to/output \
    --network-file templates/network_files/sichuan202508v7.net.xml
```

## 生成过程详解

### 第一步：事件筛选

系统根据以下条件筛选代表性事件：

**时间约束**：
- 事件持续时间：0.5-3小时
- 太短的事件（如临时车辆故障）缺乏代表性
- 太长的事件（>3小时）影响交通时间长，不适合测试

**数据完整性**：
- 必需字段：report_id, 类型, 开始/结束时间, edge_id
- 数据质量评分基于：
  - 时长优化度（1-2小时最优）
  - 字段完整度（所有必需字段都有）
  - 空间匹配（有有效的edge_id和junction_id）

**事件类型分布**：
- 优先选择交通事故（261个可用）
- 其次交通管制（89个可用）
- 然后交通阻塞（28个可用）
- 其他类型作为补充

### 第二步：策略映射

每个事件映射到3种控制策略：

**VSS (可变限速)**:
```
严重程度：主车道（第一/二车道）被占用 → 限速50 km/h
中等程度：应急车道被占用 → 限速70 km/h
默认：其他情况 → 限速60 km/h
```

**DHS (动态硬路肩)**:
```
条件：事件不占用应急车道时启用
作用：开放硬路肩增加车道容量
```

**TEC (收费站控制)**:
```
模式1：如果CSV中有"管控收费站"数据 → 使用实际收费站信息
模式2：否则 → 根据事件严重程度计算流量控制系数
```

### 第三步：XML生成

为每个事件-策略组合生成SUMO `.add.xml` 文件：

```xml
<additional>
  <!-- 事件注入 -->
  <closedLane id="accident_12547" edge="-4688" lanes="-4688_0"
              disallow="all" begin="0" end="5330"/>

  <!-- 控制策略 -->
  <variableSpeedSign id="vss_12547" lanes="-4688_0 -4688_1" />
</additional>
```

### 第四步：元数据生成

为每个场景生成4个JSON配置文件：

1. **event_description.json** - 事件详情
2. **traffic_input_config.json** - OD数据配置
3. **control_strategy_config.json** - 控制参数
4. **simulation.sumocfg** - SUMO仿真配置

### 第五步：场景库索引

生成全局索引文件 `scenario_index.json`：

```json
{
  "generated_at": "2025-11-11T12:00:00",
  "total_scenarios": 54,
  "scenarios": [
    {
      "event_id": "12547",
      "event_type": "交通事故",
      "strategy": "VSS",
      "scenario_id": "scenario_12547_vss",
      "scenario_dir": "01_交通事故/scenario_12547_vss",
      "time": {
        "start_time": "2025-07-14 01:53:49",
        "end_time": "2025-07-14 03:22:39"
      }
    },
    ...
  ],
  "by_event_type": {
    "交通事故": 18,
    "交通管制": 3,
    ...
  },
  "by_strategy": {
    "VSS": 18,
    "DHS": 12,
    "TEC": 18
  }
}
```

## 输出文件结构

```
output/scenarios/                                (场景库根目录)
├── 01_交通事故/                                 (按事件类型分类)
│   ├── scenario_12547_vss/                      (事件-策略组合)
│   │   ├── scenario_交通事故_vss_12547.add.xml  (SUMO XML)
│   │   ├── event_description.json               (事件描述)
│   │   ├── traffic_input_config.json            (OD时间范围)
│   │   ├── control_strategy_config.json         (控制参数)
│   │   ├── simulation.sumocfg                  (SUMO配置)
│   │   └── results/                            (仿真结果，若已运行)
│   ├── scenario_12547_dhs/
│   ├── scenario_12547_tec/
│   ├── scenario_12575_vss/
│   └── ...
├── 02_交通阻塞_流量激增/
│   └── ...
├── 03_交通管制/
│   └── ...
└── scenario_index.json                         (场景库索引)
```

## 理解OD时间范围

每个场景的OD数据时间范围如下计算：

```
事件时间：08:00 - 09:00
│
├─ 缓冲前：-30分钟 → 07:30（捕捉基线交通）
│
├─ 事件期间：08:00 - 09:00（事件发生）
│
└─ 缓冲后：+30分钟 → 09:30（观察恢复）

OD时间范围：07:30 - 09:30（共2.5小时）
```

**为什么需要缓冲？**
- **前缓冲**：获得事件发生前的基线交通状态
- **后缓冲**：观察控制措施的恢复效果

## 控制策略参数说明

### VSS (可变限速)

| 参数 | 含义 | 范围 | 说明 |
|------|------|------|------|
| `speed_limit_kmh` | 限制速度 | 50-70 | 根据堵塞严重程度 |
| `response_delay_seconds` | 响应延迟 | 300 | 5分钟检测+决策 |
| `recovery_period_seconds` | 恢复期 | 600 | 10分钟交通稳定 |

### DHS (动态硬路肩)

| 参数 | 含义 | 范围 | 说明 |
|------|------|------|------|
| `open_shoulder` | 是否开放 | true | 打开硬路肩 |
| `response_delay_seconds` | 响应延迟 | 300 | 同上 |
| `recovery_period_seconds` | 恢复期 | 600 | 同上 |

### TEC (收费站控制)

| 参数 | 含义 | 范围 | 说明 |
|------|------|------|------|
| `flow_reduction` | 流量缩减 | 0.2-0.8 | 高程度0.8, 低程度0.2 |
| `entrance_edges` | 入口 | edge ID列表 | 受控收费站入口 |

## 常见任务

### 生成特定事件类型的场景

```bash
# 编辑脚本，修改筛选逻辑
# 在filter_representative_events()中添加：
if event_type != '交通事故':
    continue  # 只生成交通事故场景
```

### 调整事件筛选条件

```python
# 在scripts/generate_scenarios_from_events.py中修改：

# 时间范围筛选
DURATION_MIN = 0.5  # 改为0.25小时（15分钟）
DURATION_MAX = 3.0  # 改为6.0小时

# 质量评分权重
DURATION_SCORE_OPTIMAL_HOURS = 2.0  # 最优时长
```

### 自定义控制策略参数

```python
# 在map_event_to_strategies()中修改：

strategies.append({
    "strategy_type": "VSS",
    "params": {
        "speed_limit_kmh": 80,  # 改为80 km/h
        "affected_edges": [...],
        ...
    }
})
```

## 性能指标

### 典型生成时间

| 事件数 | 策略总数 | 预计时间 | 机器配置 |
|--------|---------|---------|---------|
| 18 | 54 | ~8分钟 | i7, 16GB RAM |
| 30 | 90 | ~14分钟 | i7, 16GB RAM |
| 50 | 150 | ~25分钟 | i7, 16GB RAM |

### 文件大小

| 文件类型 | 大小 | 数量 |
|---------|------|------|
| .add.xml | ~0.5-1 KB | 54 |
| JSON配置 | ~0.5-1 KB | 162 |
| scenario_index.json | ~20-50 KB | 1 |
| **总计** | **~200 KB** | **217** |

## 故障排除

### 问题1：生成失败 - "Unknown lane description"

```
WARNING - Unknown lane description: 匝道, skipping
```

**原因**：lane描述不在支持列表中

**解决**：
1. 更新 `event_injector.py` 中的 `lane_mapping` 字典
2. 添加新的lane类型 (例如 `"匝道": 0`)
3. 重新运行脚本

### 问题2：生成失败 - "No valid lanes resolved"

```
ERROR - ✗ Failed to generate scenario: Event 12575 + VSS:
        No valid lanes resolved for accident 12575.
```

**原因**：所有占用车道描述都无效

**解决**：
1. 检查CSV中的"占用车道情况"字段
2. 添加缺失的lane类型映射
3. 或在脚本中跳过此事件

### 问题3：仿真配置生成失败 - "Missing network file"

```
ERROR - Network file not found: templates/network_files/sichuan202508v7.net.xml
```

**原因**：网络文件不存在

**解决**：
```bash
# 检查文件是否存在
ls -la templates/network_files/sichuan202508v7.net.xml

# 如果不存在，使用替代文件或检查路径
```

### 问题4：性能缓慢

**症状**：脚本运行超过20分钟

**原因**：
- 硬盘IO缓慢
- 网络文件加载时间长
- 系统资源不足

**解决**：
```bash
# 1. 减少生成数量
python scripts/generate_scenarios_from_events.py --target-events 10

# 2. 使用SSD存储
# 3. 关闭其他程序释放内存

# 4. 检查资源占用
top  # 查看CPU/内存
```

## 下一步

1. **浏览场景**：在前端访问 `scenario_browser.html` 查看生成的场景
2. **创建案例**：从场景快速创建案例（需要network和OD数据）
3. **运行仿真**：执行仿真对比事件影响
4. **分析结果**：查看控制策略的效果

## 参考资源

- 事件数据说明：`docs/scenarios_library/事件数据字段说明.csv`
- API文档：`docs/api/event_scenario_api.md`
- 项目工作流：`docs/scenarios_library/PROJECT_WORKFLOW.md`
- SUMO官方：https://sumo.dlr.de/docs/
