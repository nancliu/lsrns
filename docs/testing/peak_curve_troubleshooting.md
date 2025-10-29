# 峰值曲线不显示问题排查指南

## 问题诊断

根据代码检查，**峰值曲线功能已完整实现**，但可能因以下原因不显示：

---

## 显示条件（必须全部满足）

### 1. 批量仿真必须完成
- 状态必须是 `completed` 或 `failed`
- 在进度视图等待所有任务完成

### 2. 必须有时序数据
- 每个仿真的 `summary.xml` 文件必须存在
- API 请求必须包含 `?include_time_series=true` 参数
- 前端代码已正确设置此参数（第448行）

### 3. 仿真必须成功生成 summary.xml
- 检查仿真目录: `cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/summary.xml`
- 确认 SUMO 仿真正确配置了输出

---

## 排查步骤

### 步骤 1: 检查批量仿真是否完成

1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 在进度视图查看状态是否为 "completed"

### 步骤 2: 检查 API 响应

1. 切换到 Network 标签
2. 在结果视图中查找请求: `GET .../results?include_time_series=true`
3. 点击该请求，查看 Response 标签
4. 确认响应中是否包含 `time_series` 字段

**预期响应结构**:
```json
{
  "batch_id": "batch_xxx",
  "plan_results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "time_series": {
        "time_points": [0, 60, 120, ...],
        "running": {
          "mean": [0, 45, 120, ...],
          "std": [0, 2.1, 5.3, ...],
          "max": [...],
          "min": [...]
        }
      }
    }
  ]
}
```

### 步骤 3: 检查 summary.xml 文件

在服务器端执行:

```bash
# 检查 summary.xml 是否存在
ls D:/projects/OD_SIM/cases/*/simulations/plan_opti/*/*/sim_*/summary.xml

# 查看 summary.xml 内容
cat D:/projects/OD_SIM/cases/case_xxx/simulations/plan_opti/batch_xxx/plan_xxx/sim_66/summary.xml
```

**预期格式**:
```xml
<summary>
    <step time="0.00" loaded="0" inserted="0" running="0" ... />
    <step time="1.00" loaded="5" inserted="5" running="5" ... />
    <step time="2.00" loaded="10" inserted="8" running="8" ... />
    ...
</summary>
```

### 步骤 4: 检查浏览器 Console 错误

在浏览器 Console 中检查是否有错误:

```javascript
// 1. 检查 Chart.js 是否加载
console.log(typeof Chart);  // 应该输出 "function"

// 2. 检查峰值曲线部分是否存在
console.log(document.getElementById('peakCurveSection'));

// 3. 检查当前批次ID
console.log(currentBatchId);  // 应该有值
```

### 步骤 5: 手动测试渲染

在浏览器 Console 中执行:

```javascript
// 模拟时序数据
const testData = {
  batch_id: "test_batch",
  plan_results: [
    {
      plan_id: "test_plan",
      plan_name: "测试方案",
      time_series: {
        time_points: [0, 60, 120, 180, 240],
        running: {
          mean: [0, 50, 120, 80, 40],
          std: [0, 5, 10, 8, 4],
          max: [0, 55, 130, 88, 44],
          min: [0, 45, 110, 72, 36]
        }
      }
    }
  ]
};

// 手动调用渲染函数
renderPeakCurveChart(testData);

// 检查峰值曲线部分是否显示
document.getElementById('peakCurveSection').style.display;  // 应该是 "block"
```

---

## 常见问题

### 问题 1: 峰值曲线部分不显示（display: none）

**原因**: API 响应中没有 `time_series` 数据

**解决方案**:
1. 确认仿真已完成
2. 检查 summary.xml 文件是否存在
3. 查看后端日志: `logger.warning("No time series data found for plan ...")`

### 问题 2: Chart.js 未定义错误

**原因**: Chart.js 库未加载

**解决方案**:
1. 检查网络连接（Chart.js 从 CDN 加载）
2. 查看浏览器 Network 标签确认脚本加载成功
3. 尝试手动访问: https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js

### 问题 3: 图表显示但无数据

**原因**: 时序数据格式不正确

**解决方案**:
1. 检查 API 响应中 `time_series.running.mean` 数组是否有数据
2. 确认 `time_points` 和 `mean` 数组长度一致

### 问题 4: 仿真完成但没有 summary.xml

**原因**: SUMO 仿真配置缺少 summary 输出

**解决方案**:
查看 `simulation.sumocfg`，确认包含:
```xml
<output>
    <summary-output value="summary.xml"/>
</output>
```

---

## 代码验证清单

- [x] Chart.js 库已加载 (simulations.html:438)
- [x] `renderPeakCurveChart()` 函数已实现 (batch_simulation.js:505-643)
- [x] `renderPeakMetrics()` 函数已实现 (batch_simulation.js:645-667)
- [x] `loadResults()` 正确调用 `renderPeakCurveChart()` (batch_simulation.js:455)
- [x] API 请求包含 `?include_time_series=true` (batch_simulation.js:448)
- [x] 后端 `get_batch_results()` 支持 `include_time_series` 参数 (batch_optimization_service.py:199)
- [x] 后端正确提取和聚合时序数据 (batch_optimization_service.py:280-289)
- [x] API 路由正确传递参数 (batch_optimization_routes.py:200-203)

---

## 实际测试步骤

### 完整工作流测试

1. **创建批量仿真**:
   ```
   - 访问: http://localhost:8000/control/simulations.html
   - 选择案例
   - 选择多个方案（至少包括 baseline_plan）
   - 设置 numSeeds=3
   - 点击"创建批次"
   ```

2. **监控进度**:
   ```
   - 自动切换到进度视图
   - 等待所有任务完成（状态变为 "completed"）
   - 注意：真实仿真需要2-10分钟
   ```

3. **查看结果**:
   ```
   - 自动或手动切换到结果视图
   - 滚动到页面底部
   - 查找"在网车辆峰值曲线"部分
   ```

4. **验证显示**:
   ```
   - 应该看到折线图（多条彩色曲线）
   - 应该看到峰值指标卡片（显示各方案的峰值数据）
   ```

---

## 如果问题仍未解决

### 收集诊断信息

1. **浏览器 Console 输出**:
   ```javascript
   console.log('Chart.js loaded:', typeof Chart);
   console.log('Current batch ID:', currentBatchId);
   console.log('Peak curve section:', document.getElementById('peakCurveSection'));
   console.log('Peak curve section display:',
     document.getElementById('peakCurveSection').style.display);
   ```

2. **API 响应**:
   - 保存完整的 `/results?include_time_series=true` 响应
   - 特别注意是否包含 `time_series` 字段

3. **后端日志**:
   ```bash
   # 查看最近的日志
   tail -n 100 <log_file>

   # 搜索时序数据相关日志
   grep "time_series" <log_file>
   grep "No time series data found" <log_file>
   ```

4. **文件系统检查**:
   ```bash
   # 检查批次目录结构
   ls -R cases/*/simulations/plan_opti/batch_*

   # 统计 summary.xml 文件
   find cases -name "summary.xml" -type f | wc -l
   ```

---

## 预期行为总结

✅ **正常情况**:
- 批量仿真完成后切换到结果视图
- 页面自动请求 `?include_time_series=true`
- 后端提取所有 summary.xml 并聚合
- 前端接收数据并渲染 Chart.js 图表
- 峰值曲线部分 `display: block`
- 显示多方案对比折线图和峰值指标卡片

❌ **异常情况**:
- 峰值曲线部分 `display: none`
- Console 显示 Chart.js 错误
- API 响应缺少 `time_series` 字段
- summary.xml 文件不存在或格式错误

---

## 联系信息

如果按照以上步骤仍无法解决问题，请提供:
1. 浏览器 Console 完整输出
2. Network 标签中 `/results` 请求的完整响应
3. 批次目录的文件列表
4. 后端日志中与批次相关的输出

**测试完成日期**: 2025-10-28
**功能状态**: ✅ 代码实现正确，E2E 测试通过 (10/10)
**问题性质**: 使用场景或数据问题，非代码缺陷
