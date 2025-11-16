# 两层进度监控 - 快速参考

## 一句话总结
事件批次仿真的进度监控分为：**事件级**（所有simulation的完成率）和**场景级**（该场景simulation的完成率）。

---

## 三个关键公式

### 1️⃣ 事件级进度（最粗粒度）
```
EventProgress = (已完成的simulation总数 / 所有scenario的总simulation数) × 100
```
**示例**：6个simulation中2个完成 → 33%

---

### 2️⃣ 场景级进度（中等粒度）
```
ScenarioProgress = (该场景已完成simulation数 / 该场景总simulation数) × 100
```
**示例**：场景1有3个simulation，1个完成 → 33%

---

### 3️⃣ Simulation级进度（最细粒度）
```
SimProgress = progress.json 中的 percent 字段
```
**示例**：当前运行到 45% → 显示 45%

---

## 关键代码位置

| 功能 | 文件 | 行号 | 要点 |
|------|------|------|------|
| **后端计算** | `api/services/simulation_service.py` | 667-787 | 读取progress.json，计算统计 |
| **API端点** | `api/routes/simulation_routes.py` | 63-69 | GET /api/v1/simulation/simulation_progress/{case_id} |
| **前端刷新** | `case-simulation-center.html` | 1580-1660 | `refreshBatchStatus()` - 定时调用API |
| **前端渲染** | `case-simulation-center.html` | 1665-1825 | `renderSimulationTable()` - 分层渲染 |
| **显示面板** | `case-simulation-center.html` | 1077-1116 | `showMonitoringPanel()` - 启动监控 |

---

## 三层表格结构

```
📋 事件案例: case_event_10754                          [绿色] [粗体]
│ 总数: 6 | 进行: 3 | 完成: 2 | 进度: [===  ] 33%
│
├─ 场景1 (scenario_001)                              [灰色] [缩进40px]
│ 总数: 3 | 进行: 2 | 完成: 1 | 进度: [===  ] 33%
│ ├─ Simulation: sim_10754_001    状态: 已完成   进度: 100%
│ ├─ Simulation: sim_10754_002    状态: 仿真中   进度: 45%
│ └─ Simulation: sim_10754_003    状态: 等待中   进度: 0%
│
├─ 场景2 (scenario_002)
│ 总数: 2 | 进行: 1 | 完成: 1 | 进度: [======] 50%
│ ├─ Simulation: sim_10754_004    状态: 已完成   进度: 100%
│ └─ Simulation: sim_10754_005    状态: 仿真中   进度: 55%
│
└─ 场景3 (scenario_003)
  总数: 1 | 进行: 0 | 完成: 0 | 进度: [      ] 0%
  └─ Simulation: sim_10754_006    状态: 等待中   进度: 0%
```

---

## 数据流快图

```
用户启动 → API返回 → 刷新统计 → 计算进度 → 渲染表格 → 每1秒重复
                                          ↓
                                   自动停止
                                  (所有完成)
```

---

## 重要数据字段

| 字段 | 来源 | 用途 | 示例 |
|------|------|------|------|
| `case_id` | 用户输入 | 标识事件案例 | `case_event_10754` |
| `scenario_id` | 用户选择 | 标识场景 | `scenario_001` |
| `simulation_id` | 系统生成 | 标识单个simulation | `sim_10754_001` |
| `status` | progress.json | 状态 | `completed`, `running`, `queued`, `failed` |
| `progress` | progress.json | 即时进度 | `45` (百分比) |
| `progress_percentage` | 后端计算 | 事件级进度 | `33` (百分比) |

---

## 常见问题速查

**Q: 为什么场景进度显示33%，但simulation显示45%？**
```
A: 场景级是"计数法" (1/3=33%)，不是"平均法"。
   只有完全完成(status='completed')才算进度增加。
   simulation的45%只代表该simulation的个体进度。
```

**Q: 进度条多久更新一次？**
```
A: 每1秒自动刷新一次。
```

**Q: 监控什么时候自动停止？**
```
A: 当所有simulation都不在队列中(queued=0)且没有运行中的任务(in_progress=0)时。
```

**Q: 如何修改刷新间隔？**
```javascript
// 在 case-simulation-center.html 中找到：
setInterval(refreshBatchStatus, 1000);
// 改为：
setInterval(refreshBatchStatus, 2000);  // 2秒刷新
```

---

## 快速修复清单

如果出现以下问题，尝试：

| 问题 | 解决方案 |
|------|---------|
| 进度条不显示 | 检查是否已修复：`sim.progress` (not `sim.progress_percent`) |
| 场景进度为0但有运行中任务 | 正常现象，场景级基于完成计数 |
| 监控面板不显示 | 检查是否调用了 `showMonitoringPanel()` |
| 数字不更新 | 检查浏览器控制台是否有API错误，确认后端API是否可访问 |
| 与管控方案冲突 | 已验证隔离，不应该冲突；如有，检查DOM ID是否重复 |

---

## 测试快清

```bash
# 1. 验证 API 响应
curl http://localhost:8000/api/v1/simulation/simulation_progress/case_event_10754

# 2. 检查 progress.json 是否存在
ls -la cases/case_event_10754/simulations/*/progress.json

# 3. 查看 progress.json 内容
cat cases/case_event_10754/simulations/sim_10754_001/progress.json
```

```javascript
// 浏览器控制台验证
// 1. 检查进度百分比
document.getElementById('progressPercent').textContent

// 2. 检查表格行数
document.querySelectorAll('#simTableBody tr').length

// 3. 手动计算验证
let total = parseInt(document.getElementById('totalSims').textContent);
let completed = parseInt(document.getElementById('completedSims').textContent);
console.log('期望:', Math.round((completed/total)*100) + '%');
console.log('实际:', document.getElementById('progressPercent').textContent);
```

---

## 文档导航

```
┌─ 快速参考 (当前文件)
│  └─ 一句话总结、公式、快查表
│
├─ TWO_LEVEL_PROGRESS_MONITORING.md
│  └─ 完整的设计文档、数据流、常见问题
│
├─ PROGRESS_MONITORING_CHECKLIST.md
│  └─ 10+个测试用例、验证脚本、记录表
│
└─ PROGRESS_MONITORING_SUMMARY.md
   └─ 项目总结、质量指标、版本信息
```

---

## 版本信息

- **版本**: 1.0
- **日期**: 2025-11-16
- **状态**: ✅ 完成并已验证
- **可用性**: 生产就绪

---

💡 **提示**：需要更详细的信息？查看完整实现文档 `TWO_LEVEL_PROGRESS_MONITORING.md`
