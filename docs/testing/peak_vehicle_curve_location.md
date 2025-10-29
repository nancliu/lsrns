# 在网车辆峰值曲线位置说明

## Phase 2 Task 2.9: 在网车辆峰值曲线可视化

### 功能位置

**前端页面**: `frontend/control/simulations.html`

**视图**: 结果视图 (Results View)

**完整路径**:
```
批量仿真页面 (Simulations Page)
└── 结果视图 (#resultsView)
    └── 在网车辆峰值曲线部分 (#peakCurveSection)
        ├── 图表标题 (h3: "在网车辆峰值曲线")
        ├── Chart.js 折线图 (#peakCurveChart)
        └── 峰值指标卡片 (#peakMetrics)
```

---

## 如何查看峰值曲线

### 步骤 1: 访问批量仿真页面
- URL: `http://localhost:8000/control/simulations.html`
- 页面标题: "批量仿真 - 交通管控仿真优化系统"

### 步骤 2: 创建并运行批量仿真
1. **配置视图** (Config View):
   - 选择案例 (Case)
   - 选择多个方案 (包括基准方案)
   - 设置随机种子数 (num_seeds: 3)
   - 点击"创建批次"按钮

2. **进度视图** (Progress View):
   - 自动切换到进度监控
   - 实时显示仿真进度
   - 等待所有仿真完成

3. **结果视图** (Results View):
   - 仿真完成后自动切换
   - 或手动点击"结果视图"标签

### 步骤 3: 查看峰值曲线
- 在结果视图中向下滚动
- 找到"在网车辆峰值曲线"部分
- **注意**: 只有当批次结果包含时序数据时才会显示

---

## 峰值曲线显示逻辑

### 显示条件
```javascript
// 前端检查逻辑 (batch_simulation.js:505-514)
function renderPeakCurveChart(data) {
    // 检查是否有时序数据
    const hasTimeSeries = data.plan_results.some(plan => plan.time_series);

    if (!hasTimeSeries) {
        // 没有时序数据 → 隐藏峰值曲线部分
        document.getElementById('peakCurveSection').style.display = 'none';
        return;
    }

    // 有时序数据 → 显示峰值曲线部分
    document.getElementById('peakCurveSection').style.display = 'block';
    // ... 渲染图表
}
```

### 默认状态
- **初始状态**: `display: none` (隐藏)
- **数据加载后**:
  - 有时序数据 → `display: block` (显示)
  - 无时序数据 → 保持隐藏

---

## API 端点

### 获取包含时序数据的结果
```http
GET /api/v1/control/optimization/batch/{batch_id}/results?include_time_series=true
```

**响应结构**:
```json
{
  "batch_id": "batch_20251028_140530",
  "plan_results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "time_series": {
        "time_points": [0, 60, 120, 180, ...],
        "running_vehicles": {
          "mean": [0, 45, 120, 230, ...],
          "std": [0, 2.1, 5.3, 8.7, ...],
          "max": [0, 47, 125, 239, ...],
          "min": [0, 43, 115, 221, ...]
        },
        "loaded_vehicles": {...},
        "ended_vehicles": {...}
      }
    }
  ]
}
```

---

## 图表特性

### Chart.js 折线图
- **X轴**: 仿真时间 (秒)
- **Y轴**: 在网车辆数
- **多方案对比**: 不同颜色曲线
  - 蓝色 (rgb(54, 162, 235)) - 基准方案
  - 绿色 (rgb(75, 192, 192)) - 方案1
  - 橙色 (rgb(255, 159, 64)) - 方案2
  - 紫色 (rgb(153, 102, 255)) - 方案3
  - 红色 (rgb(255, 99, 132)) - 方案4

### 峰值指标卡片
显示每个方案的关键指标:
- **最大在网车辆数** (max_running_vehicles)
- **峰值时刻** (peak_time_hours)
- **平均在网车辆数** (avg_running_vehicles)

---

## E2E 测试

### 测试文件
- `tests/e2e/test_peak_vehicle_curve.spec.js`

### 测试覆盖
✅ **10个测试全部通过**:
1. Canvas 元素存在性
2. 峰值曲线部分结构完整性
3. 默认隐藏状态 (无数据时)
4. Chart.js 库加载
5. 峰值指标容器存在
6. 结果视图完整性
7. Canvas 样式正确性
8. 峰值曲线部分在结果视图内
9. CSS 类配置正确
10. 标题文本正确性

### 运行测试
```bash
npx playwright test tests/e2e/test_peak_vehicle_curve.spec.js --reporter=list
```

---

## 实现文件

### 后端
- `api/services/batch_optimization_service.py`:
  - `_extract_time_series_from_summary()` - 提取 summary.xml 时序数据
  - `_aggregate_time_series()` - 聚合多次仿真统计
  - `get_batch_results()` - 支持 `include_time_series` 参数

### 前端
- `frontend/control/simulations.html`:
  - `#peakCurveSection` - 峰值曲线容器
  - `#peakCurveChart` - Canvas 画布
  - `#peakMetrics` - 峰值指标容器

- `frontend/control/js/batch_simulation.js`:
  - `renderPeakCurveChart()` - 渲染图表主函数
  - `renderPeakMetrics()` - 渲染峰值指标卡片
  - `loadResults()` - 加载结果时请求时序数据

---

## 为什么可能看不到峰值曲线？

### 可能的原因

1. **仿真尚未完成**
   - 峰值曲线只在结果视图中显示
   - 必须等待批量仿真完成

2. **API 未返回时序数据**
   - 检查请求是否包含 `?include_time_series=true`
   - 查看浏览器开发者工具 Network 标签

3. **仿真未生成 summary.xml**
   - 检查仿真配置是否正确
   - 确认 SUMO 仿真成功完成

4. **结果视图未滚动到底部**
   - 峰值曲线在结果视图的下方
   - 对比表格下方

5. **JavaScript 错误**
   - 打开浏览器开发者工具 Console
   - 查看是否有错误信息

---

## 截图位置

建议截图位置:
1. 结果视图顶部 (对比表格)
2. 峰值曲线图表 (多方案对比)
3. 峰值指标卡片 (统计数据)

---

## 相关文档

- **设计文档**: `openspec/changes/implement-plan-management-and-batch-optimization/design.md`
- **规格文档**: `openspec/changes/implement-plan-management-and-batch-optimization/specs/batch-optimization/spec.md` (Requirement: 系统提取并可视化在网车辆峰值曲线)
- **任务文档**: `openspec/changes/implement-plan-management-and-batch-optimization/tasks.md` (Task 2.9)
- **API 文档**: 待完善 (Task 3.5)

---

**完成日期**: 2025-10-28
**完成状态**: ✅ 功能实现完成 + E2E 测试通过 (10/10)
**待完成**: Phase 3 文档完善和集成测试
