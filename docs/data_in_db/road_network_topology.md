# 路网拓扑特征说明

## 概述

本文档记录成都示范路网的拓扑特征，用于指导前端UI设计和数据查询优化。

---

## 路线方向分类

### 1. 环形高速（Ring Expressways）

**特征**：封闭环线，无明确起终点，车辆可循环行驶

**方向定义**：
- **顺时针** (clockwise): 沿环线顺时针方向行驶
- **逆时针** (counterclockwise): 沿环线逆时针方向行驶

**路线列表**：
| 路线代码 | 路线名称 | 说明 |
|---------|---------|------|
| **SA2** | 成都第二绕城高速（外环） | 封闭环线 |
| **G4202** | 成都绕城高速（中环） | 封闭环线 |

**代码示例**：
```javascript
const ringRoutes = new Set(['SA2', 'G4202']);
```

---

### 2. 线性高速（Linear Highways）

**特征**：有明确起点和终点的线性路段

**方向定义**：
- **上行** (upstream): 通常指向省会/中心城市方向，或桩号增加方向
- **下行** (downstream): 远离省会/中心城市方向，或桩号减少方向

**路线列表**（部分示例）**：
| 路线代码 | 路线名称 | 说明 |
|---------|---------|------|
| G4201 | 成都绕城高速（内环）连接线 | 线性路段 |
| G5 | 京昆高速成都段 | 南北向线性高速 |
| G42 | 沪蓉高速成都段 | 东西向线性高速 |
| S1 | 成都-彭州高速 | 放射状线性高速 |
| ... | 其他路线 | 均为线性拓扑 |

**桩号说明**：
- 桩号（stake）通常从起点向终点递增（如 K10+000 → K20+000）
- 上行方向一般与桩号增加方向一致
- 下行方向一般与桩号减少方向一致

---

## 数据库字段映射

### `dim.sim_network_edges` 表

| 字段名 | 类型 | 说明 | 示例值 |
|-------|------|------|--------|
| `route_code` | VARCHAR | 路线代码 | 'SA2', 'G4202', 'G5' |
| `route_direction` | VARCHAR | 路线方向 | 'clockwise', 'counterclockwise', 'upstream', 'downstream' |
| `start_stake` | FLOAT | 起始桩号（公里） | 10.523 |
| `end_stake` | FLOAT | 终止桩号（公里） | 15.678 |
| `section_code` | VARCHAR | 路段代码 | 'K10-K15', 'A段' |

### 方向值约束

```sql
-- route_direction 字段的枚举值
CHECK (route_direction IN (
    'upstream',           -- 上行
    'downstream',         -- 下行
    'clockwise',          -- 顺时针
    'counterclockwise'    -- 逆时针
));
```

---

## 前端应用

### 动态方向选项生成

**场景**：用户在路段选择器中选择路线后，方向下拉框应智能显示对应的方向选项。

**实现逻辑**：
```javascript
function updateDirectionOptions(selectedRoutes) {
    const ringRoutes = new Set(['SA2', 'G4202']);

    const hasRingRoute = selectedRoutes.some(r => ringRoutes.has(r));
    const hasLinearRoute = selectedRoutes.some(r => !ringRoutes.has(r));

    let options = '<option value="">全部</option>';

    if (hasLinearRoute) {
        // 线性高速：显示上行/下行
        options += '<option value="upstream">上行</option>';
        options += '<option value="downstream">下行</option>';
    }

    if (hasRingRoute) {
        // 环形高速：显示顺时针/逆时针
        options += '<option value="clockwise">顺时针</option>';
        options += '<option value="counterclockwise">逆时针</option>';
    }

    directionSelect.innerHTML = options;
}
```

**用户体验**：
- ✅ 选择 SA2 或 G4202 → 只显示顺时针/逆时针
- ✅ 选择 G5 或其他路线 → 只显示上行/下行
- ✅ 同时选择 SA2 + G5 → 显示全部4个选项
- ✅ 未选择路线 → 显示全部4个选项（默认状态）

---

## 性能优化说明

### 问题背景

早期实现中，`updateDirectionOptions()` 函数通过查询数据库动态获取可用方向：
```javascript
// ❌ 旧方案：耗时2-4秒
const response = await fetch(`/api/v1/control/edges/query?route_codes=${routeCode}&limit=50`);
const data = await response.json();
// 遍历50条边数据提取 route_direction 字段...
```

这导致每次选择路线时增加2-4秒延迟。

### 优化方案

由于路网拓扑是**静态**的（SA2和G4202永远是环形，其他路线永远是线性），可以通过**静态分类**替代动态查询：

```javascript
// ✅ 新方案：0ms响应
const ringRoutes = new Set(['SA2', 'G4202']);  // 硬编码环形路线
if (ringRoutes.has(routeCode)) {
    // 环形高速 → 显示顺时针/逆时针
} else {
    // 线性高速 → 显示上行/下行
}
```

**性能提升**：
- 旧方案：2-4秒（数据库查询 + 数据处理）
- 新方案：0ms（内存查找 Set）
- **提升倍数**：无限倍（从可感知延迟到瞬时响应）

### 维护成本

**新增路线时**：
1. 确定路线拓扑类型（环形 or 线性）
2. 如果是环形，更新 `ringRoutes` Set：
   ```javascript
   const ringRoutes = new Set(['SA2', 'G4202', 'NEW_RING_ROUTE']);
   ```
3. 无需修改数据库查询或API

**变更频率**：极低（路网拓扑变化频率：数年一次或更长）

---

## 数据验证

### 验证查询1：确认环形路线方向分布

```sql
-- 验证 SA2 和 G4202 只有顺时针/逆时针方向
SELECT
    route_code,
    route_direction,
    COUNT(*) as edge_count
FROM dim.sim_network_edges
WHERE route_code IN ('SA2', 'G4202')
GROUP BY route_code, route_direction
ORDER BY route_code, route_direction;
```

**预期结果**：
```
route_code | route_direction   | edge_count
-----------+-------------------+-----------
G4202      | clockwise         | 150
G4202      | counterclockwise  | 150
SA2        | clockwise         | 200
SA2        | counterclockwise  | 200
```

**异常情况**：如果出现 `upstream` 或 `downstream`，说明数据录入错误。

---

### 验证查询2：确认线性路线方向分布

```sql
-- 验证其他路线只有上行/下行方向
SELECT
    route_code,
    route_direction,
    COUNT(*) as edge_count
FROM dim.sim_network_edges
WHERE route_code NOT IN ('SA2', 'G4202')
  AND route_direction IN ('clockwise', 'counterclockwise')
GROUP BY route_code, route_direction;
```

**预期结果**：空集（0 rows）

**异常情况**：如果有记录返回，说明某些线性路线错误地标注了环形方向。

---

## 相关文档

- [示范路网基础设施静态数据说明](./示范路网基础设施静态数据说明.md)
- [多尺度分析单元数据说明](./多尺度分析单元数据说明.md)
- [数据清单与使用指南](./数据清单与使用指南.md)

---

## 变更历史

| 日期 | 变更内容 | 变更人 |
|------|---------|--------|
| 2025-10-22 | 创建文档，记录环形/线性路线分类 | Claude |

---

## 附录：路网可视化

### 环形高速示意图

```
        北
         ↑
    ┌────┴────┐
    │  G4202  │  ← 中环（绕城高速）
西 ←┤         ├→ 东
    │         │
    └────┬────┘
         ↓
        南

顺时针：北→东→南→西→北
逆时针：北→西→南→东→北

    ┌──────────┐
    │   SA2    │  ← 外环（第二绕城）
    │ ┌──────┐ │
    │ │ G4202│ │
    │ └──────┘ │
    └──────────┘
```

### 线性高速示意图

```
起点 ────────→ 终点
K0          K100

上行方向：→（桩号增加）
下行方向：←（桩号减少）

示例：G5 京昆高速成都段
成都（K0）─→ 雅安（K100）
  上行        下行
```

---

**文档版本**：1.0
**最后更新**：2025-10-22
