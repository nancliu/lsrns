# SUMO 1.24 DHS 限制说明

**问题**: SUMO 1.24 的 `<rerouter>` 元素不支持 `<interval>` 子元素
**状态**: ✅ 已修复（适配SUMO 1.24）
**修复日期**: 2025-11-16

---

## SUMO Schema 限制

### 不支持的格式（SUMO 1.24 错误）

```xml
<!-- ❌ 错误：SUMO 1.24 不允许 interval 元素 -->
<rerouter id="dhs_control" edges="edge1 edge2">
  <interval begin="3300" end="5400">  <!-- ❌ 不支持 -->
    <closingLaneReroute id="edge1_0" allow="" />
  </interval>
</rerouter>
```

**错误信息**:
```
Error: element 'interval' is not allowed for content model
'(closingReroute|closingLaneReroute|destProbReroute|...)'
```

### 支持的格式（SUMO 1.24 兼容）

```xml
<!-- ✅ 正确：直接添加 closingLaneReroute，无时间包装 -->
<rerouter id="dhs_control" edges="edge1 edge2">
  <closingLaneReroute id="edge1_0" allow="" />
  <closingLaneReroute id="edge2_0" allow="" />
</rerouter>
```

---

## 实现的解决方案

### 修改内容
**文件**: `shared/control_tools/additional_generator.py:603-660`

**关键变更**:
1. ❌ 移除 `<interval>` 元素包装
2. ✅ `<closingLaneReroute>` 直接作为 `<rerouter>` 的子元素
3. ✅ 使用第一个间隔的状态（CLOSED/OPEN）
4. 📝 在日志中记录时间信息（便于外部处理）

### 生成的 XML 示例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <rerouter id="dhs_strategy_001" edges="-12680 -10376.203 -10376 -6906 -1438 -3324 -4360 -10188">
        <closingLaneReroute id="-12680_0" allow="" />
        <closingLaneReroute id="-10376.203_0" allow="" />
        <closingLaneReroute id="-10376_0" allow="" />
        <closingLaneReroute id="-6906_0" allow="" />
        <closingLaneReroute id="-1438_0" allow="" />
        <closingLaneReroute id="-3324_0" allow="" />
        <closingLaneReroute id="-4360_0" allow="" />
        <closingLaneReroute id="-10188_0" allow="" />
    </rerouter>
</additional>
```

---

## SUMO 1.24 限制

### XML 中的 DHS 控制特性

| 特性 | 支持 | 说明 |
|------|------|------|
| 硬路肩关闭 (CLOSED) | ✅ 是 | 通过 closingLaneReroute 实现 |
| 硬路肩开放 (OPEN) | ✅ 是 | 不添加 closingLaneReroute 元素 |
| 时间相关控制 | ❌ 否 | SUMO XML Schema 不支持 |
| 动态启用/禁用 | ❌ 否 | 需要 TraCI 脚本 |
| 多个时间段 | ❌ 否 | 需要多个仿真运行 |

### 当前行为

- **XML 方式**: DHS 控制在整个仿真期间生效
- **初始状态**: 基于 activation_schedule 中的第一个间隔
- **时间信息**: 记录在仿真日志中，但不编码到 SUMO XML

**示例日志输出**:
```
INFO: DHS strategy_001: Using first interval status='CLOSED'
      (time info: 3300-5400s not encoded in SUMO XML)
```

---

## 时间相关控制的替代方案

### 方案 1: TraCI Python 脚本（推荐）

使用 SUMO TraCI API 在仿真运行时动态控制 DHS：

```python
import traci

# Start SUMO simulation
traci.start(["sumo", "-c", "config.sumocfg"])

# 模拟时间
for step in range(5400):  # 90 分钟
    # 在 3300-5400 秒之间应用 DHS 控制
    if 3300 <= step <= 5400:
        # 执行 DHS CLOSED 操作
        # 示例：限制硬路肩上的车辆类型
        ...

    traci.simulationStep()

traci.close()
```

### 方案 2: 多个仿真运行

为不同的时间段创建多个仿真配置：

```
- scenario_dhs_CLOSED_early.add.xml   # 0-3300秒：关闭
- scenario_dhs_OPEN_peak.add.xml      # 3300-5400秒：开放
- scenario_dhs_CLOSED_late.add.xml    # 5400-结束：关闭
```

然后按顺序运行，或在场景脚本中组合。

### 方案 3: 外部控制脚本

创建 Python/SUMO 脚本，根据时间条件动态应用控制：

```python
# sumo_dhs_control.py
import subprocess
import sys

def run_dhs_scenario_with_time_control():
    """Run SUMO with time-based DHS control via TraCI"""
    # 启动 SUMO，连接 TraCI
    # 在适当时间应用 DHS 关闭
    # ...
```

---

## 时间精度的权衡

### 当前方案的优势
✅ 简单：仅需一个 XML 文件
✅ 快速：无需额外脚本或 TraCI
✅ 可重现：完全由配置文件确定
✅ 兼容：与 SUMO 1.24 完全兼容

### 当前方案的限制
❌ 时间精度：全仿真期间控制（不分段）
❌ 动态性：无法在运行时改变控制状态
❌ 复杂场景：多阶段控制需要多次仿真

---

## 对项目的影响

### DHS 参数中的时间字段

虽然 `activation_schedule` 中的 `begin`/`end` 时间不在 SUMO XML 中编码，但在系统内部仍然保留：

```python
activation_schedule = [
    {
        "begin": 3300,        # 秒数（记录但不用于SUMO XML）
        "end": 5400,          # 秒数（记录但不用于SUMO XML）
        "status": "CLOSED",   # ✅ 使用（编码到XML）
        "allowed_vehicle_types": ["delivery"]
    }
]
```

**用途**:
- 记录在 `control_strategy_config.json` 中
- 用于报告和审计
- 可用于 TraCI 脚本中的实现
- 便于未来升级到支持时间间隔的 SUMO 版本

---

## SUMO 1.24 验证

### 验证命令

```bash
# 测试生成的 DHS XML 是否被 SUMO 接受
sumo -c scenario_config.sumocfg --additional-files scenario_flowsurge_dhs_xxx.add.xml --check-only

# 预期输出：不应该有 "Error: element 'interval'" 错误
```

### 已验证的配置

✅ SUMO 1.24
✅ 不带 interval 的 rerouter
✅ 多个 closingLaneReroute 元素
✅ 空的 allow 属性（禁止所有车辆）

---

## 后续改进建议

### 短期（当前版本）
1. ✅ 已完成：XML 方式兼容 SUMO 1.24
2. 文档化：时间信息仍在系统中记录
3. 监控：日志中显示时间信息

### 中期（1-2 个月）
1. 创建 TraCI 脚本支持时间相关控制
2. 为流量激增场景实现分段仿真
3. 增强 control_strategy_config.json 以支持时间注释

### 长期（版本升级时）
1. 升级到支持时间间隔的 SUMO 版本
2. 在 rerouter 中重新启用 interval 支持
3. 无需修改 activation_schedule 参数结构

---

## 总结

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| XML 格式 | ❌ 包含 interval（错误）| ✅ 无 interval（正确）|
| SUMO 兼容性 | ❌ 失败 | ✅ SUMO 1.24 通过 |
| 时间精度 | ❌ 不适用 | 📝 记录但未编码 |
| 系统集成 | ❌ 失败 | ✅ 完全集成 |

修复确保了 DHS 场景能够在 SUMO 1.24 中正确加载和执行，同时保留了时间信息供未来使用。

