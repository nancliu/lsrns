# Phase 2 前端页面集成指南

**日期**: 2025-11-12
**状态**: ✅ COMPLETED

---

## 概述

Phase 2 前端页面与 Phase 1 的 `scenario_browser.html` 集成，形成完整的事件场景仿真工作流。

### 页面架构

```
frontend/scenarios/
├── scenario_browser.html          (Phase 1 - 场景浏览)
├── case_manager.html              (Phase 2 - 案例管理)
├── simulation_monitor.html        (Phase 2 - 仿真监控)
├── analysis_viewer.html           (Phase 2 - 分析结果)
├── scenario_browser.css           (共享样式)
├── scenario_browser.js            (Phase 1 逻辑)
└── PHASE_2_FRONTEND_GUIDE.md      (本文件)
```

---

## 工作流程

```
1️⃣ 场景浏览 (scenario_browser.html)
   ↓ 选择场景
   ↓ 点击"从场景创建案例"

2️⃣ 案例管理 (case_manager.html)
   ↓ 创建案例 (可编辑参数)
   ↓ 查看案例列表
   ↓ 点击"启动仿真"

3️⃣ 仿真监控 (simulation_monitor.html)
   ↓ 实时监控进度
   ↓ 查看单个仿真详情
   ↓ 仿真完成后自动分析

4️⃣ 分析结果 (analysis_viewer.html)
   ↓ 查看概览统计
   ↓ 浏览路段拥堵热力图
   ↓ 对比基准场景
   ↓ 导出结果报告
```

---

## 页面详细说明

### 1. scenario_browser.html (Phase 1 - 已有)

**功能**:
- 浏览 449 个预设场景
- 二维分类筛选 (事件类型 × 管控策略)
- 查看场景详情
- 创建案例

**导航**:
- 左侧边栏: "🎬 仿真场景库浏览器" (当前活跃)

**集成点**:
```html
<!-- scenario_browser.html 中添加: -->
<li><a href="case_manager.html" class="nav-item">📋 案例管理</a></li>
```

---

### 2. case_manager.html (新建)

**功能**:
- 创建新案例 (从场景)
- 查看案例列表
- 修改案例参数 (只允许修改可覆盖字段)
- 启动仿真

**关键字段**:
```json
{
  "scenario_id": "scenario_10754_vss",      // 来源场景
  "event_id": "10754",                      // 事件ID
  "event_type": "01_accident",              // 事件类型 (不可修改)
  "control_strategy_type": "VSS",           // 管控策略 (不可修改)
  "simulation_duration_hours": 2.0,         // 可修改
  "random_seed": 42                         // 可修改
}
```

**API 调用**:
```javascript
POST /api/v1/case/create-from-scenario
{
  scenario_id, event_id, event_type,
  control_strategy_type, simulation_duration_hours, random_seed
}
```

**导航**:
- 返回按钮: 回到 scenario_browser.html
- 启动仿真按钮: 跳转到 simulation_monitor.html

---

### 3. simulation_monitor.html (新建)

**功能**:
- 实时监控批次仿真进度
- 显示单个仿真状态
- 展示 ETA 预计完成时间
- 查看 SUMO 日志

**实时更新**:
- 10 秒轮询一次进度
- 仿真完成后自动停止轮询

**API 调用**:
```javascript
GET /api/v1/simulation/batch-status/{batch_id}

Response: {
  batch_id, total, completed, failed, in_progress, queued,
  estimated_completion, simulations: [...]
}
```

**状态颜色编码**:
- 🟠 Running (运行中): 橙色
- 🟢 Completed (已完成): 绿色
- 🔴 Failed (失败): 红色
- ⚪ Pending (等待): 灰色

**导航**:
- 返回按钮: 回到 case_manager.html
- 点击 "📋" 按钮: 展开日志
- 点击 "📊" 按钮: 查看分析结果

---

### 4. analysis_viewer.html (新建)

**功能**:
- 四个分析标签页:
  1. **概览**: 总体统计 (车辆数, 行程时间, 完成率, 平均速度)
  2. **路段分析**: 最拥堵的前 10 条路段 (EdgeData)
  3. **对比分析**: 与基准场景的对比
  4. **详细指标**: 全量指标表格

**API 调用**:
```javascript
GET /api/v1/analysis/results/{batch_id}

Response: {
  summary, edgedata, comparison, detail_metrics
}
```

**导出功能**:
- 📄 导出 PDF (后续版本)
- 📋 导出 JSON (立即可用)

**对比指标**:
- 平均速度 (km/h)
- 行程时间 (分钟)
- 拥堵指数
- 车辆完成率 (%)

---

## 组件使用说明

### shared-utils.js

共享工具函数:
```javascript
import {
  formatDate,        // 格式化日期
  formatTime,        // 秒数 → HH:MM:SS
  getStatusBadgeClass,
  getColorForStatus,
  calculatePercentage,
  delay,
  showError,
  showSuccess
} from '../components/shared-utils.js';
```

### api-client.js

统一 API 客户端:
```javascript
import { APIClient } from '../components/api-client.js';

const api = new APIClient();
const response = await api.request('/simulation/batch-status/{batch_id}');
```

### simulation-monitor.js (组件库)

若要在其他页面使用实时监控组件:
```javascript
import { SimulationMonitor } from '../components/simulation-monitor.js';

const monitor = new SimulationMonitor('containerId', {
  apiClient: api,
  updateInterval: 5000,
  autoStart: true
});
```

### analysis-results.js (组件库)

若要在其他页面使用分析结果组件:
```javascript
import { AnalysisResultsViewer } from '../components/analysis-results.js';

const viewer = new AnalysisResultsViewer('containerId', {
  apiClient: api
});

await viewer.loadResults(batchId);
```

---

## 集成检查清单

### ✅ 已完成

- [x] case_manager.html - 案例创建和管理
- [x] simulation_monitor.html - 仿真实时监控
- [x] analysis_viewer.html - 分析结果查看
- [x] 左侧导航栏集成
- [x] API 端点集成
- [x] 样式继承 (scenario_browser.css)

### ⚠️ 待完成 (后续优化)

- [ ] 缓存优化 (避免频繁 API 调用)
- [ ] 离线支持 (缓存已加载数据)
- [ ] 权限控制 (多用户隔离)
- [ ] 国际化 (i18n 支持)
- [ ] 深色主题支持

---

## 使用流程示例

### 完整工作流

1. **打开场景浏览**
   ```
   http://localhost:8000/frontend/scenarios/scenario_browser.html
   ```

2. **选择场景，创建案例**
   - 选择 "scenario_10754_vss" (事故 + VSS 管控)
   - 点击行动按钮 → "从场景创建案例"
   - 系统跳转到 case_manager.html

3. **在案例管理页修改参数 (可选)**
   - 修改仿真时长: 0.5 小时 (快速测试)
   - 设置随机种子: 42 (可复现)
   - 点击 "创建案例"

4. **监控仿真进度**
   - 系统跳转到 simulation_monitor.html?batch_id=batch_xxxxx
   - 实时查看进度条、预计完成时间
   - 每 10 秒自动更新一次

5. **查看分析结果**
   - 仿真完成后，点击 "📊" 查看结果
   - 系统跳转到 analysis_viewer.html?batch_id=batch_xxxxx
   - 浏览四个分析标签页
   - 点击 "📋 导出 JSON" 下载结果

---

## 本地开发指南

### 启动服务

```bash
# 激活环境
conda activate od_project

# 启动 API 服务
.\start_api.ps1

# API 会运行在 http://localhost:8000
```

### 访问页面

```
http://localhost:8000/frontend/scenarios/scenario_browser.html
```

### 调试工具

按 F12 打开浏览器开发者工具:
- Console: 查看错误日志
- Network: 监视 API 调用
- Application: 检查存储数据

---

## 常见问题

### Q: 如何从 scenario_browser.html 直接跳转到 case_manager.html？

A: 在 scenario_browser.html 中的"创建案例"按钮添加:
```javascript
window.location.href = `case_manager.html?scenario_id=${scenarioId}`;
```

### Q: 如何在离线环境下使用?

A: 修改 api-client.js，使用本地 mock 数据。

### Q: 支持批量创建多个案例吗?

A: 不支持。当前每次创建一个案例。可通过重复操作实现批量。

### Q: 分析结果会自动刷新吗?

A: 不会。需要手动点击 "🔄 刷新" 按钮或 F5 重新加载。

---

## 文件大小和性能

| 文件 | 大小 | 加载时间 |
|------|------|---------|
| case_manager.html | ~12 KB | <100ms |
| simulation_monitor.html | ~15 KB | <100ms |
| analysis_viewer.html | ~14 KB | <100ms |
| shared-utils.js | ~8 KB | <50ms |
| api-client.js | ~5 KB | <50ms |

**总计**: ~54 KB (远小于现有 script.js 的 74 KB)

---

## 后续扩展

### Week 5 计划

1. 添加用户认证和权限
2. 实现数据缓存和离线模式
3. 添加更多分析图表 (图形库集成)
4. 支持批量操作
5. 移动端适配优化

---

## 相关文档

- [PHASE_2_USER_GUIDE.md](../../docs/PHASE_2_USER_GUIDE.md) - 用户使用指南
- [PHASE_2_API_REFERENCE.md](../../docs/PHASE_2_API_REFERENCE.md) - API 参考
- [scenario_browser.html](./DEVELOPER_GUIDE.md) - Phase 1 开发指南

---

**最后更新**: 2025-11-12
**维护者**: Phase 2 开发团队
**反馈**: 提交 Issue 或 PR
