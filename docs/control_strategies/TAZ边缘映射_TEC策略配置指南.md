# TAZ边缘映射 - TEC策略配置指南

## 文档目的
本文档将 `dim.taz_demonstration_mapping` 表中的TAZ（交通分析区）ID映射到 `TAZ_6.add.xml` 文件中的实际SUMO边缘ID，用于在G5和G4202路线上实施TEC（收费站/入口管控）策略。

## SUMO中的TAZ结构

在TAZ.add.xml文件中，每个入口匝道TAZ包含：
```xml
<taz id="TAZ_ID" name="station_name toll(entrance)" color="blue">
    <tazSource id="EDGE_ID" weight="1.00"/>
    <tazSink id="EDGE_ID" weight="0.00"/>
</taz>
```

- **`tazSource id`**: 车辆生成的入口边缘ID
- **负数边缘ID**（如"-1232"）：边缘的反向方向
- **正数边缘ID**（如"E15"）：边缘的正向方向
- **weight="1.00"**: 主要入口边缘（TEC策略使用此边缘）

## G5路线 - 优先入口站点

### 🔴 P0优先级：成雅双流南站 (K1820.15)

**背景数据**:
- **门架ID**: G000551005000220010
- **峰值流量**: 296 veh/hr（8:00时段）
- **主线速度**: 21-25 km/h（严重拥堵）
- **关键问题**: 入口即为拥堵点

**TAZ映射**:
| TAZ ID | 类型 | 站点名称 | 入口边缘 | 备注 |
|--------|------|----------|---------|------|
| G00055100500301010 | toll_square | 双流南站C匝道 (shuangliunanzhanczadao) | **-1232** | ✅ 主要入口 |
| G00055100500301020 | toll_square | 双流南站A匝道 (shuangliunanzhanazadao) | **-17206** | 次要入口 |

**✅ 边缘验证** (2025-10-26):
- **边缘-1232**: 已验证 ✅
  - 类型: `highway.motorway_link`
  - 长度: 225.42 m
  - 车道数: 1条车道
  - 速度: 22.22 m/s (80 km/h)
  - 状态: 可用于TEC实施

**推荐TEC配置**:
```json
{
  "template_id": "tec_ramp_metering_001",
  "strategy_name": "G5双流南站TEC管控-P0",
  "configured_params": {
    "entrance_edge": "-1232",
    "position": 0,
    "tec_interval_array": [
      {
        "begin_hours": 0,
        "end_hours": 6,
        "vehsPerHour": 300,
        "target_speed": 30
      },
      {
        "begin_hours": 6,
        "end_hours": 10,
        "vehsPerHour": 120,
        "target_speed": 10
      },
      {
        "begin_hours": 10,
        "end_hours": 16,
        "vehsPerHour": 250,
        "target_speed": 20
      },
      {
        "begin_hours": 16,
        "end_hours": 20,
        "vehsPerHour": 100,
        "target_speed": 10
      },
      {
        "begin_hours": 20,
        "end_hours": 24,
        "vehsPerHour": 300,
        "target_speed": 30
      }
    ]
  }
}
```

**限流依据**:
- 平峰期（0-6点、10-16点）：允许250-300 veh/hr（正常容量）
- **早高峰（6-10点）：限制120 veh/hr**（削减60%）
- **晚高峰（16-20点）：限制100 veh/hr**（削减68%）
- 目标：大幅减少进入拥堵路段的车辆，配合VSS+DHS策略缓解拥堵

---

### 🟡 P1优先级：成雅白家站 (K1811.9)

**背景数据**:
- **门架ID**: G000551005003710010
- **峰值流量**: 330 veh/hr（8:00时段）- **G5全线最高**
- **主线速度**: 120 km/h（正常，但流量大）
- **问题**: 保护下游K1820拥堵点

**TAZ映射**:
| TAZ ID | 类型 | 站点名称 | 入口边缘 | 备注 |
|--------|------|----------|---------|------|
| G00055100501601010 | toll_square | 白家站-黄晶方向 (baijia toll huangjing) | **E15** | ✅ 主要入口 |
| G00055100501602010 | toll_square | 白家站-曙光方向 (baijia toll shuguang) | **E17** (推测) | 次要入口 |

**✅ 边缘验证** (2025-10-26):
- **边缘E15**: 已验证 ✅
  - 类型: 入口匝道 (priority=-1)
  - 长度: 135.87 m
  - 车道数: 1条车道
  - 速度: 13.89 m/s (50 km/h)
  - 状态: 可用于TEC实施

**推荐TEC配置**:
```json
{
  "template_id": "tec_ramp_metering_001",
  "strategy_name": "G5白家站TEC管控-P1",
  "configured_params": {
    "entrance_edge": "E15",
    "position": 0,
    "tec_interval_array": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "vehsPerHour": 350,
        "target_speed": 30
      },
      {
        "begin_hours": 7,
        "end_hours": 10,
        "vehsPerHour": 250,
        "target_speed": 20
      },
      {
        "begin_hours": 10,
        "end_hours": 24,
        "vehsPerHour": 350,
        "target_speed": 30
      }
    ]
  }
}
```

**限流依据**:
- 平峰期（0-7点、10-24点）：允许350 veh/hr（正常容量）
- **早高峰（7-10点）：限制250 veh/hr**（削减24%）
- 目标：保护下游K1820拥堵路段，减少主线流量压力

---

### 🟡 P1优先级：成绵新都站 (K1768.55)

**背景数据**:
- **门架ID**: G000551044001320010
- **峰值流量**: 262 veh/hr（8:00时段）
- **主线速度**: 67 km/h（显示拥堵迹象）
- **问题**: 进入K1768.5拥堵区域

**TAZ映射**:
| TAZ ID | 类型 | 站点名称 | 入口边缘 | 备注 |
|--------|------|----------|---------|------|
| G00055104401101010 | toll_square | 新都站 (xindou toll) | **-15818** | ✅ 主要入口 |
| G00055104401001010 | toll_square | 新都北站1 (xindoubeizhan1) | **-15134** (推测) | 次要-相邻站点 |
| G00055104401001020 | toll_square | 新都北站2 (xindoubeizhan2) | **-6648** (推测) | 次要-相邻站点 |

**说明**: 在TAZ_6.add.xml中找到（约12000+行）。成绵段收费站序列：
- G00055104400901010 → 青白江站 (qingbaijiang)
- G00055104401001010/20 → 新都北站 (xindoubeizhan) - K1768.5
- **G00055104401101010 → 新都站 (xindou) - K1768.55** ← 我们的目标！

**✅ 边缘验证** (2025-10-26):
- **边缘-15818**: 已验证 ✅
  - 类型: `highway.motorway_link`
  - 长度: 89.74 m
  - 车道数: **2条车道**（更高容量！）
  - 速度: 22.22 m/s (80 km/h)
  - 状态: 可用于TEC实施
  - 🌟 **优势**: 2车道入口支持更高的计量容量

**推荐TEC配置**:
```json
{
  "template_id": "tec_ramp_metering_001",
  "strategy_name": "G5新都站TEC管控-P1",
  "configured_params": {
    "entrance_edge": "-15818",
    "position": 0,
    "tec_interval_array": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "vehsPerHour": 300,
        "target_speed": 30
      },
      {
        "begin_hours": 7,
        "end_hours": 10,
        "vehsPerHour": 180,
        "target_speed": 20
      },
      {
        "begin_hours": 10,
        "end_hours": 17,
        "vehsPerHour": 300,
        "target_speed": 30
      },
      {
        "begin_hours": 17,
        "end_hours": 20,
        "vehsPerHour": 150,
        "target_speed": 15
      },
      {
        "begin_hours": 20,
        "end_hours": 24,
        "vehsPerHour": 300,
        "target_speed": 30
      }
    ]
  }
}
```

**限流依据**:
- 平峰期（0-7点、10-17点、20-24点）：允许300 veh/hr
- **早高峰（7-10点）：限制180 veh/hr**（削减31%）
- **晚高峰（17-20点）：限制150 veh/hr**（削减42%，保护下游拥堵段）
- 目标：早晚高峰均进行管控，缓解下游拥堵

---

## G4202路线 - TEC入口（未来工作）

G4202（成都绕城高速）在数据库中也有toll_square TAZ条目：
- G42015100100101010, G42015100100102010（001段收费站）
- G42015100200101010, G42015100200102010（002段收费站）
- ...（更多）

可使用相同方法将这些TAZ映射到边缘。

---

## 查询方法

### 1. 查找某路线的toll_square TAZ ID

```sql
SELECT
  t.taz_id,
  t.source_type,
  t.source_id
FROM dim.taz_demonstration_mapping t
WHERE t.demonstration_route_code = 'G5'
  AND t.source_type = 'toll_square'
ORDER BY t.taz_id;
```

### 2. 查找桩号附近的门架

```sql
SELECT
  gantry_id,
  gantry_name,
  gantry_stake,
  route_code
FROM dim.point_gantry
WHERE route_code = 'G5'
  AND gantry_stake BETWEEN 1768 AND 1769
ORDER BY gantry_stake;
```

### 3. 从TAZ.add.xml提取边缘ID

```bash
grep -B1 -A3 'id="TAZ_ID"' templates/taz_files/TAZ_6.add.xml
```

查找 `<tazSource id="EDGE_ID" weight="1.00"/>` 这一行。

---

## 实施工作流程

1. **查询数据库**: 获取目标路线的toll_square TAZ ID
2. **解析TAZ文件**: 从TAZ_6.add.xml提取入口边缘ID
3. **创建策略**: 在TEC策略配置中使用边缘ID
4. **测试**: 启用TEC策略运行仿真
5. **验证**: 检查车辆是否在入口匝道处进行计量

---

## 边缘ID命名规则

- **负数ID**（如"-1232"）：
  - 原始边缘的反向方向
  - 常见于以相反方向加入主线的匝道

- **正数ID**（如"E15"）：
  - 正向方向
  - "E"前缀可能表示外部/入口边缘

- **权重参数**：
  - `weight="1.00"`: 主要入口（TEC使用此边缘）
  - `weight="0.00"`: 出口或次要边缘（TEC忽略）

---

## 状态与下一步

✅ **已完成**:
- 从baseline数据分析中识别G5优先入口站点
- 找到全部3个优先站点的TAZ ID：双流南站、白家站、新都站
- 提取入口边缘ID：
  - 双流南站: 边缘"-1232" ✅
  - 白家站: 边缘"E15" ✅
  - 新都站: 边缘"-15818" ✅
- 创建包含实际边缘ID的完整TEC配置模板
- **✅ 验证所有边缘ID** (2025-10-26):
  - 全部3个边缘在 `dim.sim_network_edges` 数据库中确认 ✅
  - 全部3个边缘在 `sichuan202508v7.net.xml` 网络文件中确认 ✅
  - 详细验证报告: `TEC边缘验证报告.md`

⚠️ **待完成**:
- 通过控制策略API创建实际策略实例
- 在仿真运行中测试TEC策略
- 扩展到G4202路线入口（识别优先匝道）
- 记录额外的次要入口（P2优先级）

---

## 参考资料

- 数据库表: `dim.taz_demonstration_mapping`
- TAZ文件: `templates/taz_files/TAZ_6.add.xml`
- 网络文件: `templates/network_files/sichuan202508v7.net.xml`
- 真实数据分析: `docs/真实数据分析与策略建议_G4202_G5综合.md`

---

**文档版本**: 1.0
**最后更新**: 2025-10-26
**作者**: Claude Code 分析
