# 前端调试指南 - 批量仿真曲线显示问题

## 问题症状
```
liveTimeSeries: {time_points: Array(0), total_running: Array(0), ...}
No live time series data, hiding chart
```

## 根本原因
前端使用的是**旧的缓存数据**，而后端API已经返回了正确的数据。

### 原因分析
1. **浏览器HTTP缓存** - HTTP响应被缓存，导致后续请求返回缓存数据
2. **轮询间隔太长** (10秒) - 数据更新不及时
3. **fetch没有缓存破坏参数** - 没有强制获取最新数据

## 修复方案

### 修复1: 增加轮询频率
**文件**: `frontend/control/js/batch_simulation.js` (第253行)
```javascript
// 之前: 每10秒更新
progressPollInterval = setInterval(updateProgress, 10000);

// 修复后: 每2秒更新
progressPollInterval = setInterval(updateProgress, 2000);
```

### 修复2: 添加缓存破坏参数
**文件**: `frontend/control/js/batch_simulation.js` (第268-276行)
```javascript
// 添加时间戳参数和缓存头
const response = await fetch(
    `${API_BASE}/control/optimization/batch/${currentBatchId}/progress?t=${Date.now()}`,
    {
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    }
);
```

## 验证步骤

### 步骤1: 清除浏览器缓存
```
方法A - 强制刷新
  按 Ctrl+Shift+R (Windows/Linux) 或 Cmd+Shift+R (Mac)
  
方法B - 开发者工具清除
  1. 打开 F12
  2. 右键点击刷新按钮
  3. 选择 "Empty cache and hard refresh"
```

### 步骤2: 打开调试控制台
```
1. 按 F12 打开 Developer Tools
2. 点击 Console 标签
3. 清除之前的日志
```

### 步骤3: 观察日志输出
在Console中应该看到：

```
✅ 正确的日志
=== API Progress Response ===
Status: running
Running tasks count: 3
Has live_time_series: true
  - time_points length: 600    ← 应该 > 0
  - total_running length: 600  ← 应该 > 0

=== renderLiveCurve called ===
liveTimeSeries: {time_points: Array(600), total_running: Array(600), ...}
Showing live curve chart with 600 data points  ← 曲线显示

❌ 错误的日志（需要强制刷新）
liveTimeSeries: {time_points: Array(0), total_running: Array(0), ...}
No live time series data, hiding chart
```

### 步骤4: 检查图表显示
```
向下滚动页面，检查是否显示"实时在网车辆曲线"图表
期望: 显示折线图，显示600个数据点的车辆数变化趋势
```

## 网络请求验证

### 检查API响应
```
1. 打开 F12
2. 点击 Network 标签
3. 查找 progress?t=... 的请求
4. 点击响应，查看 Response 数据
5. 验证 live_time_series 中的时间点和数据
```

### 预期API响应
```json
{
  "live_time_series": {
    "time_points": [0, 1, 2, ..., 599],
    "total_running": [702, 708, 984, ..., 27438],
    "task_count": 3,
    "last_update": "2025-10-30T00:29:36.049863"
  }
}
```

## 常见问题排查

### 问题: 仍然显示空数组
**原因**: 浏览器仍然使用缓存
**解决方案**:
1. 再次进行强制刷新 (Ctrl+Shift+R)
2. 打开浏览器的隐私窗口/无痕模式重新访问
3. 清除所有浏览器缓存 (Settings → Privacy → Clear browsing data)
4. 检查HTTP服务器的缓存设置

### 问题: 轮询停止或不更新
**原因**: JavaScript错误或轮询间隔设置错误
**解决方案**:
1. 检查 Console 中是否有错误信息（红色）
2. 确认 `progressPollInterval` 已设置
3. 检查网络请求是否正常发送

### 问题: API返回数据但前端未显示
**原因**: JSON解析错误或renderLiveCurve函数问题
**解决方案**:
1. 在 Console 中输入: `console.log(data.live_time_series)` 查看数据
2. 检查 renderLiveCurve 函数是否被调用
3. 查看是否有JavaScript错误

## 测试验证清单

- ✅ 强制刷新后显示新的缓存破坏参数 (t=...)
- ✅ Console日志显示 time_points length > 0
- ✅ 曲线图表区域显示（不是"No live time series data"）
- ✅ 曲线图表能够渲染600个数据点
- ✅ 每2秒自动更新一次进度

## 修改的文件

- **`frontend/control/js/batch_simulation.js`**
  - 修改轮询间隔: 10秒 → 2秒
  - 修改fetch调用: 添加时间戳缓存破坏和缓存头

## 相关资源

- **问题诊断报告**: `BATCH_PROGRESS_ENHANCEMENT_REPORT.md`
- **API文档**: `docs/api_docs/新架构API指南.md`
- **前端代码**: `frontend/control/js/batch_simulation.js`

---
**更新日期**: 2025-10-30
**版本**: 1.1
**状态**: 已修复并验证

