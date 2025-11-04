# 第一层结果页面 - 交通指标对比详细说明

**文档日期**: 2025-11-04
**范围**: Layer 1 结果分析（基于 summary.xml）
**数据来源**: SUMO 仿真输出的 summary.xml 文件

---

## 📊 对比的交通指标清单

第一层结果页面从 SUMO summary.xml 中提取并对比以下 **9 个关键交通指标**：

### 1️⃣ **step** - 仿真步数
- **单位**: 秒 (s)
- **含义**: 整个仿真运行的总时长
- **改进方向**: 越低越好（相同流量下耗时越少越好）
- **来源**: `summary.xml` → `timestep[-1]/@time`
- **计算方式**: 取最后一个 timestep 的时间属性
- **示例**: 3600 = 模拟运行了1小时

---

### 2️⃣ **loaded** - 已加载车辆数
- **单位**: 辆 (vehicles)
- **含义**: 整个仿真周期内被加载到网络中的总车数
- **改进方向**: 取决于应用场景
  - 如果是对流量容纳能力的测试：越高越好
  - 如果是相同流量下的能力测试：应该相等（基数）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@loaded`
- **典型值**: 2000-5000 辆
- **备注**: 这是配置参数，通常批次内所有方案相同

---

### 3️⃣ **inserted** - 已插入车辆数
- **单位**: 辆 (vehicles)
- **含义**: 成功插入到网络的车辆数
- **改进方向**: 越高越好（插入成功率高）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@inserted`
- **关系**: `inserted ≤ loaded`（有些车可能因为拥堵或网络问题无法插入）
- **性能指标**: `insertion_rate = inserted / loaded * 100%`
- **典型值**: 1500-4500 辆

---

### 4️⃣ **ended** - 已完成车辆数  ⭐ 重要
- **单位**: 辆 (vehicles)
- **含义**: 成功完成行程、离开网络的车数
- **改进方向**: 越高越好（流量通过效率）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@ended`
- **性能指标**: `throughput = ended / inserted * 100%`
- **示例**:
  - baseline: ended = 2200 辆
  - 控制方案: ended = 2250 辆
  - 改进率: +2.3% ✅
- **典型值**: 1000-4000 辆
- **交通意义**: 表示"绿灯效应"，完成率越高说明流动性越好

---

### 5️⃣ **running** - 当前运行车数
- **单位**: 辆 (vehicles)
- **含义**: 仿真结束时，仍在网络中运行的车辆数
- **改进方向**: 越低越好（说明大部分车完成了行程）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@running`
- **含义**: `running = inserted - ended`
- **示例**:
  - baseline: running = 450 辆
  - 控制方案: running = 380 辆
  - 改进率: -15.6% ✅（减少了滞留车）
- **性能含义**: 越多滞留车说明拥堵越严重

---

### 6️⃣ **waiting** - 等待车数  ⭐ 重要
- **单位**: 辆 (vehicles)
- **含义**: 因为信号灯、拥堵等原因停止等待的车数
- **改进方向**: 越低越好（停止的车越少越好）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@waiting`
- **性能指标**: `waiting_rate = waiting / running * 100%`
- **示例**:
  - baseline: waiting = 120 辆
  - 可变限速方案: waiting = 95 辆
  - 改进率: -20.8% ✅（等待减少）
- **交通意义**: 反映交通流的平顺性
  - waiting 多 → 交通拥堵严重
  - waiting 少 → 交通流畅

---

### 7️⃣ **teleports** - 传送次数  ⭐ 拥堵指标
- **单位**: 次 (times)
- **含义**: SUMO 模拟器进行的"传送"操作次数
- **改进方向**: 越低越好（零为理想）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@teleports`
- **原理**: 当某车长时间被卡在网络中无法移动时，SUMO 会将其"传送"到前方，避免死锁
- **性能指标**: 传送 = 网络严重拥堵的代理指标
- **示例**:
  - baseline: teleports = 45 次
  - 动态硬路肩方案: teleports = 12 次
  - 改进率: -73.3% ✅（拥堵大幅改善）
- **交通意义**:
  - 0-10 次 → 路网通畅
  - 10-50 次 → 轻度拥堵
  - 50+ 次 → 严重拥堵
- **备注**: 这是 SUMO 特有的指标，反映仿真的物理约束

---

### 8️⃣ **collisions** - 碰撞次数
- **单位**: 次 (collisions)
- **含义**: 仿真中发生的车辆碰撞事件数
- **改进方向**: 越低越好（零为理想）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@collisions`
- **性能指标**: 碰撞次数越多 = 仿真参数越激进（不现实）
- **示例**:
  - baseline: collisions = 3 次
  - 控制方案: collisions = 1 次
  - 改进率: -66.7%（更安全）
- **交通意义**: 反映控制策略的安全性
- **典型值**: 0-5 次（好的仿真参数）

---

### 9️⃣ **avgSpeed** - 平均速度  ⭐ 核心指标
- **单位**: m/s 或 km/h（根据配置）
- **含义**: 整个仿真周期内，所有已完成车辆的平均行驶速度
- **改进方向**: 越高越好（速度越高流量越大）
- **来源**: `summary.xml` → `timestep[-1]/vehicleSummary/@avgSpeed`
- **计算方式**: 所有已完成车的行驶速度平均值
- **示例**:
  - baseline: avgSpeed = 15.2 m/s (~55 km/h)
  - 可变限速方案: avgSpeed = 18.7 m/s (~67 km/h)
  - 改进率: +22.8% ✅（速度提升）
- **交通意义**:
  - 最直观的性能指标
  - 高速度 = 高通行效率
  - 反映了控制策略的有效性

---

## 📈 指标之间的关系

```
总流量 (loaded)
    ↓
插入成功 (inserted)
    ↓
完成/等待 (ended vs running)
    ↓
等待程度 (waiting) ← 拥堵指标 → 传送 (teleports)
    ↓
速度 (avgSpeed)
```

**实际流动等式**:
```
loaded = inserted + (未能插入的车)
inserted = ended + running
running = waiting + (正在行驶的车)
```

---

## 🎯 改进率计算规则

### 对于"越低越好"的指标 (waiting, teleports, collisions, running)

```
改进率 = (baseline_值 - test_值) / baseline_值 × 100%

- 正改进率 (+) = test_值 更低 = 更好 ✅
- 负改进率 (-) = test_值 更高 = 更差 ❌
```

**例子**:
- baseline waiting = 100 辆
- 控制方案 waiting = 80 辆
- 改进率 = (100 - 80) / 100 × 100% = +20% ✅

### 对于"越高越好"的指标 (ended, avgSpeed)

```
改进率 = (test_值 - baseline_值) / baseline_值 × 100%

- 正改进率 (+) = test_值 更高 = 更好 ✅
- 负改进率 (-) = test_值 更低 = 更差 ❌
```

**例子**:
- baseline avgSpeed = 50 km/h
- 控制方案 avgSpeed = 58 km/h
- 改进率 = (58 - 50) / 50 × 100% = +16% ✅

---

## 🚦 典型改进场景示例

### 场景 1: 可变限速 (VSS) 控制 - 高速公路拥堵缓解

| 指标 | baseline | VSS 方案 | 改进率 | 解释 |
|------|----------|---------|--------|------|
| **ended** | 2200 | 2280 | +3.6% ✅ | 更多车完成行程 |
| **avgSpeed** | 48 km/h | 62 km/h | +29.2% ✅ | 速度显著提升 |
| **waiting** | 120 | 85 | -29.2% ✅ | 等待减少 |
| **teleports** | 35 | 8 | -77.1% ✅ | 拥堵大幅改善 |
| **running** | 250 | 180 | -28% ✅ | 滞留车减少 |

**结论**: VSS 方案效果显著，各项指标都改善 ✅

---

### 场景 2: 动态硬路肩 (DHS) 控制 - 应急车道开放

| 指标 | baseline | DHS 方案 | 改进率 | 解释 |
|------|----------|---------|--------|------|
| **ended** | 2100 | 2320 | +10.5% ✅ | 吞吐量提升 |
| **avgSpeed** | 42 km/h | 58 km/h | +38.1% ✅ | 速度大幅提升 |
| **teleports** | 52 | 6 | -88.5% ✅ | 严重拥堵缓解 |
| **collisions** | 2 | 1 | -50% ✅ | 更安全 |
| **running** | 380 | 260 | -31.6% ✅ | 滞留减少 |

**结论**: DHS 在高拥堵场景下效果最显著 ⭐

---

### 场景 3: 收费站管控 (TEC) - 坡度缓冲

| 指标 | baseline | TEC 方案 | 改进率 | 解释 |
|------|----------|---------|--------|------|
| **waiting** | 95 | 102 | +7.4% ❌ | 等待反而增加 |
| **running** | 150 | 145 | -3.3% ✅ | 轻微改善 |
| **avgSpeed** | 52 km/h | 51 km/h | -1.9% ❌ | 速度略降 |

**结论**: TEC 在此场景效果有限，可能不适用 ⚠️

---

## 🔧 Layer 1 与 Layer 2 的区别

### Layer 1 - 快速概览（当前实现）
- **数据源**: summary.xml（最终统计）
- **指标数**: 9 个汇总指标
- **计算速度**: 极快（<1 秒）
- **显示方式**: 对比表 + 柱状图
- **用途**: 快速评估方案效果

### Layer 2 - 详细分析（未来实现）
- **数据源**: tripinfo.xml + edgedata.xml（逐车/逐路段）
- **指标数**: 50+ 个详细指标
- **计算速度**: 较慢（10-30 秒）
- **显示方式**: 分布直方图、热力图、时序曲线
- **用途**: 深度诊断、调优参数

---

## 📍 代码实现位置

### 后端指标定义

**文件**: `api/services/batch_optimization_service.py`

```python
def _parse_summary_xml(self, file_path: Path) -> Dict[str, Any]:
    """提取以下指标:
    - total_vehicles (loaded)
    - avg_speed
    """

def _parse_tripinfo_xml(self, file_path: Path) -> Dict[str, Any]:
    """提取:
    - avg_travel_time
    - total_delay
    """
```

**文件**: `shared/analysis_tools/batch_result_analyzer.py`

```python
def _extract_summary_metrics(self, summary_path: Path) -> Dict[str, Any]:
    """提取所有9个指标"""
    metrics = {
        "step": int(last_step.get("time", 0)),
        "loaded": int(vehicle.get("loaded", 0)),
        "inserted": int(vehicle.get("inserted", 0)),
        "ended": int(vehicle.get("ended", 0)),
        "running": int(vehicle.get("running", 0)),
        "waiting": int(vehicle.get("waiting", 0)),
        "teleports": int(vehicle.get("teleports", 0)),
        "collisions": int(vehicle.get("collisions", 0)),
        "avgSpeed": float(vehicle.get("avgSpeed", 0.0))
    }
```

### 前端显示

**文件**: `frontend/control/js/batch_results.js`

```javascript
function renderNewBatchResults(planResults) {
    // metricKeys 自动从 aggregated_metrics 提取
    // 显示所有可用的指标
    metricKeys.forEach(metricKey => {
        // 构建表格行和计算改进率
    });
}
```

**文件**: `frontend/control/css/simulations.css`

```css
.comparison-table {
    /* 表格样式 */
}

.improvement.positive {
    color: #27ae60;  /* 绿色 - 改进 */
    background: #d5f4e6;
}

.improvement.negative {
    color: #c0392b;  /* 红色 - 恶化 */
    background: #ffebee;
}
```

---

## 💡 使用指南

### 如何解读结果表

1. **看基准方案的绝对值** → 了解当前路网状况
2. **看控制方案的改进率** → 判断方案效果
3. **综合多个指标** → 全面评估方案
   - 如果大多数指标都改进 → 方案很好 ✅
   - 如果有指标恶化 → 需要调整参数 ⚠️

### 优先关注的指标排序

1. **avgSpeed** - 最直观的性能指标
2. **ended** - 通行效率
3. **waiting** - 拥堵程度
4. **teleports** - 拥堵严重程度
5. **running** - 滞留车数

---

## 🔗 相关文档

- 提案: `proposal.md`
- 设计: `design.md`
- 实现报告: `LAYER1_RESULTS_PAGE_REVIEW.md`
- API 文档: `docs/api_docs/新架构API指南.md`

---

**文档版本**: 1.0
**最后更新**: 2025-11-04
