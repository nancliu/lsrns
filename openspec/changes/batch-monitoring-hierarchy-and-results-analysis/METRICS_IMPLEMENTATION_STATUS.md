# 交通指标实现状态分析

**问题**: 前端页面是否缺少指标？
**答案**: 不是前端缺少，而是**后端返回的指标不完整**

---

## ✅ 目前实现的指标

根据实际代码检查，API 当前只返回 4 个指标：

1. **total_vehicles** (已加载车数) - 来自 summary.xml
2. **avg_speed** (平均速度) - 来自 summary.xml
3. **avg_travel_time** (平均行程时间) - 来自 tripinfo.xml
4. **total_delay** (总延误) - 来自 tripinfo.xml

---

## ❌ 缺少的指标（5 个）

根据需求，应该还有以下指标来自 summary.xml：

1. **step** - 仿真步数 (秒)
2. **inserted** - 已插入车数 (辆)
3. **ended** - 已完成车数 (辆) ⭐ 关键
4. **running** - 当前运行车数 (辆)
5. **waiting** - 等待车数 (辆) ⭐ 关键
6. **teleports** - 传送次数 (次) ⭐ 拥堵指标
7. **collisions** - 碰撞次数 (次)

---

## 📍 问题代码位置

**文件**: `api/services/batch_optimization_service.py`
**方法**: `_parse_summary_xml()` (第 1430-1450 行)

当前代码只提取了：
```python
return {
    "total_vehicles": int(step_elem.get("loaded", 0)),
    "avg_speed": float(step_elem.get("meanSpeed", 0.0)),
}
```

应该提取：
```python
return {
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

---

## 🔧 修复方案

### 步骤 1: 修复后端返回完整指标

修改 `_parse_summary_xml()` 从 7 个增加到 9 个指标。

**工作量**: 1-2 小时
**优先级**: P0 (关键)

### 步骤 2: 添加指标元数据（可选但推荐）

后端返回指标配置，告诉前端：
- 中文标签 (label)
- 单位 (unit)
- 改进方向 (direction: higher/lower/neutral)

**工作量**: 2-3 小时
**优先级**: P1 (重要)

### 步骤 3: 前端使用元数据

前端改进表格：
- 显示中文标签而不是英文键名
- 显示单位
- 根据 direction 正确计算改进率

**工作量**: 1-2 小时
**优先级**: P1 (重要)

---

## 📊 用户看到的结果

**修复前**: 表格显示 4 个指标，用户看不懂
**修复后**: 表格显示 9 个指标，都有中文标签和单位

---

## ✨ 前端没有问题

前端实现是**智能的**：
- 自动从 API 返回的 aggregated_metrics 提取所有指标
- 无需修改前端代码就能支持新增指标
- 只要后端返回更多指标，前端就自动显示

所以问题不在前端，而在**后端的数据提取**不完整。

