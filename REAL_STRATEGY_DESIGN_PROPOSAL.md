# 真实策略实例设计方案

## 一、当前状况分析

### 现有演示策略特点
**共22个演示策略**：
- VSS（可变限速）：10个
- TEC（收费站管控）：6个
- DHS（动态硬路肩）：6个

**存在的问题**：
1. **路段选择随意**：edge_id（如`-9292`、`-8014`）未与实际路网对应
2. **参数值缺乏依据**：限速值、流量阈值没有基于真实交通数据
3. **时间段简化**：只考虑早/晚高峰，未考虑全天24小时变化
4. **缺少场景关联**：未与具体交通问题（拥堵、事故）关联

---

## 二、真实策略设计思路

### 🎯 核心原则

```
真实策略 = 真实交通问题 + 真实路网数据 + 科学参数设置 + 仿真验证
```

### 📊 设计流程（5个步骤）

```mermaid
flowchart LR
    A[识别交通问题] --> B[选择目标路段]
    B --> C[确定策略类型]
    C --> D[配置参数值]
    D --> E[仿真验证优化]
```

---

## 三、详细设计方案

### 步骤1：识别真实交通问题

#### 1.1 数据来源
- **历史仿真结果**：`cases/*/analysis/` 目录下的分析报告
- **路段拥堵数据**：EdgeData分析的速度、流量数据
- **门架观测数据**：数据库 `point_gantry` 表的实际观测

#### 1.2 问题分类
| 问题类型 | 适用策略 | 判断依据 |
|---------|---------|---------|
| 路段拥堵（速度<40km/h） | VSS 可变限速 | EdgeData speed < 40 |
| 入口排队（等待时间>5min） | TEC 入口管控 | 入口流量 > 容量 |
| 高峰期容量不足 | DHS 应急车道 | 流量/容量比 > 0.9 |

**实施建议**：
```python
# 伪代码：从历史仿真中提取问题路段
def identify_problem_edges():
    # 1. 加载EdgeData分析结果
    edgedata = load_edgedata_results('cases/case_001/analysis/edgedata/')

    # 2. 筛选拥堵路段（速度<40km/h持续30分钟以上）
    congested_edges = edgedata[
        (edgedata['speed'] < 40) &
        (edgedata['duration'] > 1800)
    ]

    # 3. 返回edge_id列表
    return congested_edges['edge_id'].tolist()
```

---

### 步骤2：选择目标路段

#### 2.1 路段选择标准
✅ **连续性**：策略路段应连续（通过from_junction/to_junction验证）
✅ **功能一致**：同一路段的lanes、speed_limit应相近
✅ **长度适中**：
   - VSS：2-5公里（避免太短导致驾驶员反应不及）
   - DHS：5-10公里（足够长以缓解拥堵）
   - TEC：单个入口匝道

#### 2.2 从数据库查询真实路段
```sql
-- 示例：查询G4202顺时针方向连续路段
SELECT edge_id, start_stake, end_stake, length, num_lanes
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND route_direction = 'CW'  -- 顺时针
  AND start_stake BETWEEN 10.0 AND 15.0  -- K10-K15区间
ORDER BY start_stake;
```

**实施建议**：
创建工具函数 `shared/control_tools/edge_selector.py`：
```python
def get_continuous_edges(route_code, direction, start_km, end_km):
    """获取连续路段"""
    # 从数据库查询指定桩号范围的边
    # 验证连续性（前一段的to_junction = 后一段的from_junction）
    # 返回edge_id列表
```

---

### 步骤3：确定策略类型和参数

#### 3.1 VSS（可变限速）参数设计

**科学依据**：
- 基于速度-流量关系（Fundamental Diagram）
- 参考《公路交通安全设施设计规范》（JTG D81-2017）

**参数配置示例**：
```json
{
  "strategy_type": "VSS",
  "configured_params": {
    "affected_edges": ["-xxxx", "-yyyy", "-zzzz"],  // 连续3-5个路段
    "speed_steps": [
      {"time_hours": 6, "speed_kmh": 120},  // 早高峰前：正常限速
      {"time_hours": 7, "speed_kmh": 100},  // 早高峰开始：降速
      {"time_hours": 8, "speed_kmh": 80},   // 高峰期：严格限速
      {"time_hours": 9, "speed_kmh": 100},  // 高峰结束：恢复
      {"time_hours": 10, "speed_kmh": 120}  // 平峰期：正常限速
    ],
    "applicable_vehicle_types": ["passenger", "truck"]  // 小客车+货车
  }
}
```

**参数选择依据**：
| 参数 | 取值依据 | 数据来源 |
|------|---------|---------|
| affected_edges | 拥堵路段+上游1km | EdgeData分析 |
| speed_kmh | 自由流速度 × (0.6-0.8) | 历史仿真速度分布 |
| time_hours | 拥堵时段 ±1小时 | EdgeData时序分析 |

---

#### 3.2 TEC（入口管控）参数设计

**科学依据**：
- 基于入口匝道流量控制理论（Ramp Metering）
- 目标：主线流量维持在容量90%以下

**参数配置示例**：
```json
{
  "strategy_type": "TEC",
  "configured_params": {
    "entrance_edge": "-10592",  // 单个入口匝道
    "position": 0,  // 控制点位置（匝道起点）
    "flow_intervals": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "vehsPerHour": 600,      // 平峰期：正常通行
        "target_speed": 20
      },
      {
        "begin_hours": 7,
        "end_hours": 9,
        "vehsPerHour": 240,      // 早高峰：严格限流
        "target_speed": 10       // 降低速度增加排队
      },
      {
        "begin_hours": 9,
        "end_hours": 17,
        "vehsPerHour": 600,
        "target_speed": 20
      },
      {
        "begin_hours": 17,
        "end_hours": 19,
        "vehsPerHour": 300,      // 晚高峰：中度限流
        "target_speed": 15
      },
      {
        "begin_hours": 19,
        "end_hours": 24,
        "vehsPerHour": 600,
        "target_speed": 20
      }
    ]
  }
}
```

**参数选择依据**：
| 参数 | 计算公式 | 说明 |
|------|---------|------|
| vehsPerHour | (主线容量 - 当前流量) × 0.9 | 保留10%安全余量 |
| target_speed | 10-20 km/h | 匝道建议速度 |

---

#### 3.3 DHS（动态硬路肩）参数设计

**科学依据**：
- 参考德国、荷兰动态车道管理经验
- 应急车道开放需严格条件（拥堵+低事故率）

**参数配置示例**：
```json
{
  "strategy_type": "DHS",
  "configured_params": {
    "affected_edges": ["-13154", "-5004", "-9292", "-8014"],  // 4-6个连续路段
    "hard_shoulder_lane_index": 0,  // 最右侧应急车道
    "intervals": [
      {
        "begin_hours": 0,
        "end_hours": 6,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency"]  // 仅应急车辆
      },
      {
        "begin_hours": 6,
        "end_hours": 10,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus"]  // 仅小客车+公交
      },
      {
        "begin_hours": 10,
        "end_hours": 16,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency"]
      },
      {
        "begin_hours": 16,
        "end_hours": 20,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus", "truck"]  // 含货车
      },
      {
        "begin_hours": 20,
        "end_hours": 24,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency"]
      }
    ]
  }
}
```

**开放条件**：
- ✅ 主线流量 > 90% 容量
- ✅ 速度 < 60 km/h
- ✅ 近期无事故（安全考虑）
- ✅ 路段长度 ≥ 5km

---

### 步骤4：仿真验证和优化

#### 4.1 验证流程
```
1. 创建基准场景（baseline）：无策略
2. 创建策略场景：应用策略
3. 对比分析：
   - 平均速度提升
   - 总延误减少
   - 排队长度变化
4. 参数调优：
   - 微调限速值
   - 调整时间段
   - 优化路段范围
```

#### 4.2 评估指标
| 指标 | 计算方法 | 目标改善 |
|------|---------|---------|
| 平均速度 | EdgeData分析 | +10-20% |
| 总延误时间 | Σ(实际时间-自由流时间) | -15-30% |
| 最大排队长度 | E1 detector数据 | -20-40% |
| 通行能力 | 流量/设计容量 | +5-10% |

---

## 四、实施路线图

### 🚀 Phase 1: 数据准备（1-2天）

**任务清单**：
- [ ] 运行1-2个历史case，生成EdgeData分析结果
- [ ] 识别Top 10拥堵路段（速度<40km/h）
- [ ] 查询数据库，获取路段详细信息（桩号、车道数）
- [ ] 绘制路段地图，标注问题区域

**输出**：
- `problem_edges.csv`：问题路段清单
- `edge_details.json`：路段详细属性

---

### 🔧 Phase 2: 策略设计（2-3天）

**任务清单**：
- [ ] 选择3-5个典型问题场景
- [ ] 为每个场景设计对应策略类型（VSS/TEC/DHS）
- [ ] 基于科学公式计算初始参数值
- [ ] 编写策略配置JSON文件

**工具开发**（可选）：
```python
# shared/control_tools/strategy_designer.py
def design_vss_strategy(edge_ids, congestion_times, baseline_speed):
    """基于拥堵数据自动生成VSS策略"""
    pass

def design_tec_strategy(entrance_edge, mainline_capacity, peak_demand):
    """基于容量和需求自动生成TEC策略"""
    pass
```

**输出**：
- `strategy_real_vss_001.json` - 真实VSS策略
- `strategy_real_tec_001.json` - 真实TEC策略
- `strategy_real_dhs_001.json` - 真实DHS策略

---

### 🧪 Phase 3: 仿真验证（3-5天）

**任务清单**：
- [ ] 创建baseline case（无策略）
- [ ] 创建strategy case（应用策略）
- [ ] 运行仿真，生成结果
- [ ] 对比分析EdgeData、E1数据
- [ ] 评估策略效果

**评估脚本**：
```python
# scripts/evaluate_strategy_effect.py
def compare_scenarios(baseline_case, strategy_case):
    # 对比速度、延误、排队等指标
    # 生成对比图表
    # 输出改善百分比
```

---

### 📈 Phase 4: 参数优化（2-3天）

**任务清单**：
- [ ] 根据仿真结果调整参数
- [ ] 重新运行仿真验证
- [ ] 迭代优化2-3轮
- [ ] 文档化最优参数

**优化方向**：
- 限速值调整（±10 km/h）
- 时间段边界调整（±30分钟）
- 路段范围调整（增减1-2个edge）

---

## 五、推荐的首批真实策略

基于G4202成都绕城高速（假设已有该路网数据），建议创建以下策略：

### 策略1：G4202北段早高峰可变限速（VSS）
```
- 问题：K10-K15路段早高峰拥堵
- 策略：7:00-9:00降速至80km/h，提高车流稳定性
- 预期效果：速度提升15%，延误减少20%
```

### 策略2：G4202东入口流量控制（TEC）
```
- 问题：东入口匝道早高峰排队溢出
- 策略：7:30-8:30限流至240车/小时
- 预期效果：主线速度提升10%，入口排队减少30%
```

### 策略3：G4202南段应急车道开放（DHS）
```
- 问题：K20-K28路段双向高峰期容量不足
- 策略：早晚高峰开放应急车道（仅小客车）
- 预期效果：通行能力提升12%，延误减少25%
```

---

## 六、需要确认的问题

在开始实施前，请您确认：

### ❓ 数据可用性
1. **历史仿真数据**：是否有已完成的case可供分析？
2. **路网数据**：数据库中G4202/SA2等路线数据是否完整？
3. **门架数据**：是否有真实观测数据可作为参考？

### ❓ 实施范围
4. **策略数量**：计划创建多少个真实策略？（建议先3-5个）
5. **路线范围**：重点关注哪些路线？（G4202/SA2/其他）
6. **场景类型**：优先处理哪类问题？（拥堵/事故/特殊天气）

### ❓ 工具开发
7. **自动化程度**：是否需要开发辅助工具自动生成策略？
8. **可视化需求**：是否需要策略效果可视化对比？

---

## 七、建议的工作方式

### 方式A：手动设计（快速验证）
**适用**：策略数量<5个，快速验证思路
**流程**：
1. 人工分析1-2个case结果
2. 手动编写JSON配置文件
3. 通过前端UI创建策略
4. 运行仿真验证

**优点**：快速灵活，无需开发
**缺点**：难以批量处理

---

### 方式B：半自动化（推荐）
**适用**：策略数量5-20个，需要迭代优化
**流程**：
1. 开发数据分析脚本（识别问题路段）
2. 提供参数建议（基于公式计算）
3. 人工审核调整
4. 批量创建策略
5. 自动化评估对比

**优点**：效率高，可复用
**缺点**：需要1-2天开发时间

---

### 方式C：全自动化（长期）
**适用**：策略数量>20个，持续优化
**流程**：
1. 开发完整策略设计工具链
2. 机器学习优化参数
3. 自动化A/B测试
4. 持续迭代优化

**优点**：完全自动化，最优效果
**缺点**：开发周期长（1-2周）

---

## 八、下一步行动

请您确认以下内容，我将据此开展工作：

### ✅ 确认事项
1. **设计思路认可度**：本方案是否符合您的预期？
2. **实施方式选择**：方式A/B/C，您倾向哪种？
3. **数据准备状态**：是否有可用的历史仿真数据？
4. **首批策略范围**：建议从3-5个策略开始，您是否同意？
5. **时间计划**：预期多久完成首批真实策略？

---

**等待您的反馈后，我将立即开始实施！** 🚀
