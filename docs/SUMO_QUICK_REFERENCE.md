# SUMO XML快速参考指南

## 验证结果速览

```
📊 验证统计:
   总方案数:      14个
   ✅ 合规方案:    14个 (100%)
   ❌ 问题方案:    0个 (0%)
   错误数:        0
   警告数:        0

📈 策略分布:
   VSS (可变限速):   10个
   DHS (应急车道):   6个
   TEC (收费站管控):  6个
```

---

## 快速检查清单

当你修改或添加新的XML时，使用以下检查清单：

### VSS (可变限速) 检查清单

```xml
<variableSpeedSign id="my_vss_id" edges="edge1 edge2 edge3...">
  <step time="0" speed="25.0" />
  <step time="3600" speed="20.0" />
  <step time="86400" speed="25.0" />
</variableSpeedSign>
```

- [ ] `id` 属性唯一且描述性强
- [ ] `edges` 属性列表不为空（空格分隔）
- [ ] `time` 值范围: 0-86400秒
- [ ] `speed` 值范围: 0-50 m/s（-1表示恢复默认）
- [ ] 建议速度: 16.67-27.78 m/s (60-100 km/h)
- [ ] 时间顺序递增（可以重叠表示循环）

**转换参考**:
```
m/s → km/h:  乘以 3.6
km/h → m/s:  除以 3.6

常用转换:
60 km/h  = 16.67 m/s
80 km/h  = 22.22 m/s
100 km/h = 27.78 m/s
```

---

### DHS (应急车道) 检查清单

```xml
<rerouter id="my_dhs_id" edges="edge1 edge2...">
  <interval begin="0" end="25200">
    <closingLaneReroute id="0" allow="" />  <!-- 关闭 -->
  </interval>
  <interval begin="25200" end="86400" />     <!-- 开放 -->
</rerouter>
```

- [ ] `id` 属性唯一且描述性强
- [ ] `edges` 属性列表不为空（空格分隔）
- [ ] `<interval>` 的 `begin` 和 `end` 范围: 0-86400秒
- [ ] **关闭**状态: 包含 `<closingLaneReroute id="0" allow="" />`
- [ ] **开放**状态: **无** `<closingLaneReroute>` 元素
- [ ] `id="0"` 表示车道0（第一条车道，从0开始计数）
- [ ] `allow=""` 表示禁止所有车辆

**时间转换参考**:
```
秒数 → 时:分:秒
0     = 00:00
25200 = 07:00 (7小时)
36000 = 10:00
61200 = 17:00
68400 = 19:00
86400 = 24:00 (完整24小时)
```

---

### TEC (收费站管控) 检查清单

```xml
<calibrator id="my_tec_id" edge="edge_id" pos="0">
  <flow begin="0" end="21600" vehsPerHour="300" speed="15" />
  <flow begin="21600" end="86400" vehsPerHour="150" speed="10" />
</calibrator>
```

- [ ] `id` 属性唯一且描述性强
- [ ] `edge` 为单条边（不是列表）
- [ ] `pos` 通常为 0（边起点）
- [ ] `<flow>` 时间段无重叠，覆盖0-86400秒
- [ ] `vehsPerHour` 范围: 0-3000 (建议: 100-300)
- [ ] `speed` 范围: 0-50 m/s (建议: 6-15 m/s)
- [ ] 建议设置 `<flow>` 不超过5个时段（可管理性）

---

## 验证命令

### 检查单个XML文件

```bash
python scripts/validate_all_add_xml.py  # 检查所有文件
```

### 在SUMO中测试

```bash
# 加载特定方案
sumo --net-file network.net.xml \
     --route-files vehicles.rou.xml \
     --additional-files control_data/plans/plan_vss_morning_peak_simple/control.add.xml
```

---

## 文件位置映射

```
📁 项目结构:
   control_data/
   └── plans/
       ├── baseline_plan/
       │   └── control.add.xml
       ├── plan_vss_morning_peak_simple/
       │   └── control.add.xml
       ├── plan_dhs_morning_peak_severe/
       │   └── control.add.xml
       ├── plan_tec_evening_peak_severe/
       │   └── control.add.xml
       ├── plan_vss_dhs_morning_peak_severe/
       │   └── control.add.xml
       ├── plan_vss_dhs_evening_composite/
       │   └── control.add.xml
       ├── plan_vss_dhs_evening_peak_high_flow/
       │   └── control.add.xml
       ├── plan_vss_dhs_tec_allday_complex/
       │   └── control.add.xml
       ├── plan_vss_dhs_tec_allday_persistent_severe/
       │   └── control.add.xml
       ├── plan_vss_evening_peak_severe/
       │   └── control.add.xml
       ├── plan_vss_morning_peak_severe/
       │   └── control.add.xml
       ├── plan_vss_tec_morning_peak_severe/
       │   └── control.add.xml
       ├── plan_vss_tec_evening_peak_high_flow/
       │   └── control.add.xml
       └── plan_tec_morning_peak_severe/
           └── control.add.xml
```

---

## 常见问题解答

### Q: 我的VSS速度值应该是多少？
**A**: 根据实际交通数据建议：
- 自由流: 27.78 m/s (100 km/h)
- 中等拥堵: 22.22 m/s (80 km/h)
- 严重拥堵: 16.67 m/s (60 km/h)
- 极限管控: 13.89 m/s (50 km/h)

### Q: DHS的车道ID（id属性）应该如何设置？
**A**: 在项目中，我们使用 `id="0"` 代表硬路肩（Lane 0）。
- 这对应于SUMO网络中的第一条车道
- 可以通过策略的 `hard_shoulder_lane_index` 参数自定义

### Q: 能否在同一文件中混合VSS、DHS和TEC？
**A**: **可以**，而且推荐这样做！SUMO完全支持在单个 `control.add.xml` 中定义多种策略：
```xml
<additional>
  <variableSpeedSign .../>
  <rerouter .../>
  <calibrator .../>
</additional>
```

### Q: TEC中的 `route` 属性是必需的吗？
**A**: **不是必需的**。Flow中常见属性：
- 必需: `begin`, `end`, `vehsPerHour` 或 `speed`
- 可选: `route`, `type`, `departPos`, `departSpeed`

### Q: 我的time值是0-86400还是0-24小时？
**A**: **必须是秒数（0-86400）**，不是小时。
转换: 小时数 × 3600 = 秒数

### Q: 如何验证我的XML是否正确？
**A**:
```bash
python scripts/validate_all_add_xml.py
```
或检查错误消息中是否有:
- ❌ XML解析错误
- ❌ 时间范围错误 (begin/end < 0 或 > 86400)
- ❌ 速度范围错误 (speed > 50 m/s)
- ❌ 流量范围错误 (vehsPerHour > 3000)

---

## 实际示例

### 示例1: 简单VSS方案

**场景**: G4202绕城高速早高峰限速

```xml
<additional>
  <variableSpeedSign id="vss_g4202_morning" edges="-8712 -15452 -9350">
    <!-- 凌晨到早7点: 100 km/h (正常) -->
    <step time="0" speed="27.78" />

    <!-- 早7点到早10点: 60 km/h (高峰限速) -->
    <step time="25200" speed="16.67" />

    <!-- 早10点到晚5点: 100 km/h (恢复) -->
    <step time="36000" speed="27.78" />

    <!-- 晚5点到晚7点: 80 km/h (傍晚限速) -->
    <step time="61200" speed="22.22" />

    <!-- 晚7点到次日凌晨: 100 km/h (恢复) -->
    <step time="68400" speed="27.78" />
  </variableSpeedSign>
</additional>
```

### 示例2: VSS+DHS组合

**场景**: G4202应急车道开放+同步限速

```xml
<additional>
  <!-- VSS限速 -->
  <variableSpeedSign id="vss_g4202_combined" edges="-8712 -15452">
    <step time="0" speed="27.78" />      <!-- 正常 -->
    <step time="25200" speed="16.67" />  <!-- 限速 -->
    <step time="36000" speed="27.78" />  <!-- 恢复 -->
  </variableSpeedSign>

  <!-- DHS应急车道 - 与VSS同期开放 -->
  <rerouter id="dhs_g4202_combined" edges="-8712 -15452">
    <!-- 0:00-7:00: 关闭 -->
    <interval begin="0" end="25200">
      <closingLaneReroute id="0" allow="" />
    </interval>

    <!-- 7:00-10:00: 开放 (无元素) -->
    <interval begin="25200" end="36000" />

    <!-- 10:00-24:00: 关闭 -->
    <interval begin="36000" end="86400">
      <closingLaneReroute id="0" allow="" />
    </interval>
  </rerouter>
</additional>
```

### 示例3: TEC入口管控

**场景**: G5成雅段入口流量控制

```xml
<additional>
  <calibrator id="tec_g5_entrance" edge="-1232" pos="0">
    <!-- 0:00-6:00: 夜间自由流 (300车/h) -->
    <flow begin="0" end="21600" vehsPerHour="300" speed="15" />

    <!-- 6:00-10:00: 早高峰严格限流 (120车/h) -->
    <flow begin="21600" end="36000" vehsPerHour="120" speed="8" />

    <!-- 10:00-16:00: 午间平衡流量 (250车/h) -->
    <flow begin="36000" end="57600" vehsPerHour="250" speed="12" />

    <!-- 16:00-20:00: 晚高峰极限管控 (100车/h) -->
    <flow begin="57600" end="72000" vehsPerHour="100" speed="6" />

    <!-- 20:00-24:00: 夜间恢复 (300车/h) -->
    <flow begin="72000" end="86400" vehsPerHour="300" speed="15" />
  </calibrator>
</additional>
```

---

## 相关文档

- 📄 **完整验证报告**: `docs/SUMO_XML_COMPATIBILITY_REPORT.md`
- 🔧 **验证脚本**: `scripts/validate_all_add_xml.py`
- 📊 **验证器模块**: `shared/control_tools/xml_validator.py`
- 🌐 **SUMO官方文档**: https://sumo.dlr.de/

---

**最后更新**: 2025-11-02
**验证状态**: ✅ ALL COMPLIANT
**准备就绪**: ✅ READY FOR SIMULATION
