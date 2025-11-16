# Phase 2 API 快速参考卡片

## 核心端点速查表

### 进度监控面板

| 功能 | 端点 | 方法 | 刷新频率 | 用途 |
|------|------|------|---------|------|
| 获取进度 | `/api/v1/simulation/simulation_progress/{case_id}` | GET | 5-10s (展开)<br>30s (折叠) | 更新统计、进度条、表格 |
| 获取仿真列表 | `/api/v1/simulation/simulations/{case_id}` | GET | 初始加载 | 加载全部仿真 |
| 获取详情 | `/api/v1/simulation/simulation/{simulation_id}` | GET | 按需 | 跳转分析前确认 |
| 批量启动 | `/api/v1/simulation/batch-start` | POST | 一次性 | 启动多个仿真 |

### 对比分析

| 功能 | 端点 | 方法 | 用途 |
|------|------|------|------|
| 聚合结果 | `/api/v1/analysis/results/{batch_id}?case_id=...` | GET | 多案例指标卡片 |
| 对比报告 | `/api/v1/analysis/comparison/{batch_id}?case_id=...` | GET | 对比表格 + 差异% |

---

## 前端调用示例

### 进度监控（展开状态）

```javascript
// 每 10 秒刷新一次
setInterval(async () => {
  const res = await fetch(`/api/v1/simulation/simulation_progress/${caseId}`);
  const data = await res.json();

  // 更新卡片
  document.getElementById('total').textContent = data.data.total_simulations;
  document.getElementById('completed').textContent = data.data.completed;
  document.getElementById('running').textContent = data.data.running;

  // 更新进度条
  document.getElementById('progressBar').style.width =
    `${data.data.progress_percentage}%`;

  // 更新表格
  renderTable(data.data.simulations);
}, 10000);
```

### 对比分析加载

```javascript
// 用户选择多个案例后调用
async function loadComparison(caseIds) {
  const batchId = "batch_20251112_100000";  // 从批量启动响应或 URL 获取

  // 并行加载两个 API
  const [resultsRes, comparisonRes] = await Promise.all([
    fetch(`/api/v1/analysis/results/${batchId}?case_id=${caseIds[0]}`),
    fetch(`/api/v1/analysis/comparison/${batchId}?case_id=${caseIds[0]}`)
  ]);

  const results = await resultsRes.json();
  const comparison = await comparisonRes.json();

  // 渲染对比表格
  renderComparisonTable(comparison.data.comparison_table);
}
```

### 表格中的查看分析

```javascript
// 点击"查看分析"按钮
async function viewAnalysis(simulationId, caseId) {
  // 确认仿真已完成
  const res = await fetch(`/api/v1/simulation/simulation/${simulationId}`);
  const data = await res.json();

  if (data.data.status === 'completed') {
    // 跳转到分析页面
    window.location.href =
      `/scenarios/analysis_viewer.html?case_id=${caseId}&simulation_id=${simulationId}`;
  } else {
    alert('仿真尚未完成，请稍后');
  }
}
```

---

## 响应数据字段速查

### 仿真进度响应

```javascript
{
  code: 200,
  data: {
    case_id: "case_001",
    total_simulations: 10,
    completed: 3,
    running: 2,
    failed: 0,
    created: 5,
    progress_percentage: 30,  // ← 用于进度条
    simulations: [
      {
        simulation_id: "sim_001",
        status: "completed",        // ← 状态值
        progress: 100,              // ← 百分比
        started_at: "2025-11-16T10:00:00",
        completed_at: "2025-11-16T10:05:00",
        duration: "5m 30s"
      }
    ]
  }
}
```

### 对比报告响应

```javascript
{
  code: 200,
  data: {
    comparison_table: [
      {
        metric_name: "总车辆数",
        case_a_value: 1000,
        case_b_value: 1050,
        difference: 50,
        difference_percentage: 5.0,    // ← 用于差异显示
        improvement: "negative"        // ← "positive" 或 "negative"
      }
    ]
  }
}
```

---

## 常见问题排查

### 进度不更新

| 问题 | 检查 |
|------|------|
| 数据没有变化 | 确认后端 `simulation_progress` 正确读取仿真状态 |
| 频率太慢 | 检查 setInterval 是否为 5-10s（展开）或 30s（折叠） |
| 刷新卡顿 | 后端 API 响应时间是否 > 2s，优化查询 |

### 对比分析不显示

| 问题 | 检查 |
|------|------|
| 表格为空 | 确认 `batch_id` 正确，且仿真已完成 |
| 数据不对齐 | 检查响应中的 `case_id` 是否匹配 |
| 差异计算错 | 验证后端计算公式：`(B-A)/A*100` |

---

## 前后端对接检查清单

### 后端提供

- [ ] `/api/v1/simulation/simulation_progress/{case_id}` 正确返回进度数据
- [ ] `/api/v1/analysis/results/{batch_id}` 支持 ?case_id 参数
- [ ] `/api/v1/analysis/comparison/{batch_id}` 计算 difference_percentage
- [ ] 所有状态码返回正确（200/400/404/500）
- [ ] 响应时间 < 2 秒

### 前端实现

- [ ] 展开/折叠按钮切换状态
- [ ] 刷新频率根据状态自动调整
- [ ] 进度条宽度 = progress_percentage
- [ ] 表格通过 status 字段显示颜色
- [ ] 差异 > 10% 的行高亮显示

---

## 环境变量和配置

```python
# .env
API_BASE_URL=http://localhost:8000/api/v1
SIMULATION_PROGRESS_REFRESH_EXPANDED=10000  # ms (展开)
SIMULATION_PROGRESS_REFRESH_COLLAPSED=30000 # ms (折叠)
ANALYSIS_COMPARISON_BATCH_TIMEOUT=30000     # ms (超时)
```

```javascript
// frontend/config.js
const API_CONFIG = {
  baseURL: 'http://localhost:8000/api/v1',
  refreshRates: {
    expanded: 10000,   // 10秒 (展开时)
    collapsed: 30000   // 30秒 (折叠时)
  },
  timeout: 30000
};
```

---

## 测试 curl 命令

```bash
# 测试进度端点
curl -X GET "http://localhost:8000/api/v1/simulation/simulation_progress/case_20251112_001"

# 测试对比报告
curl -X GET "http://localhost:8000/api/v1/analysis/comparison/batch_20251112_100000?case_id=case_20251112_001"

# 批量启动
curl -X POST "http://localhost:8000/api/v1/simulation/batch-start" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_ids": ["sim_001", "sim_002"],
    "case_id": "case_20251112_001",
    "parallel_workers": 4,
    "auto_run_analysis": true
  }'
```

---

**打印版本**: 建议打印此页面作为开发时的快速参考
**最后更新**: 2025-11-16
