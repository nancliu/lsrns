# Phase 2 实现总结与补充任务清单

**生成日期**: 2025-11-13
**版本**: v1.0
**状态**: 准备实现阶段

---

## 概览

基于对现有代码和需求的详细分析，Phase 2 事件场景仿真集成包含以下补充实现任务：

### 核心工作流
```
仿真推演场景集 (已有)
  ↓ [创建案例按键]
  ↓ (新增)
场景案例管理 (三个Tab: 案例列表 | 仿真监控 | 批次管理)
  ↓ [批量仿真按键] 或 从批次管理跳转
  ↓
影响分析 (自动启动分析 + 结果展示)
```

---

## 补充任务 (Tasks 2.7-2.16)

### Frontend Tasks (Task 2.8-2.13)

**Task 2.8: 场景浏览页面 - 创建案例功能** (1.5天)
- 在 scenario_browser.html 的场景表格中添加 [创建案例] 按键
- 实现模态框: 显示场景信息 + 仿真参数表单
- 表单验证和 API 调用 (POST /api/v1/case/create-from-scenario)
- 成功后跳转到 case-simulation-center.html

**Task 2.9: 案例管理页面 - 案例列表与筛选** (2天)
- 实现 case-simulation-center.html 的 Tab 1: 案例列表
- 显示从场景生成的案例 (支持场景ID筛选)
- 实现状态筛选、搜索功能
- 显示案例统计信息
- 支持 [查看详情]、[重新仿真]、[批量仿真] 操作

**Task 2.10: 案例管理页面 - 仿真监控** (2天)
- 实现 case-simulation-center.html 的 Tab 2: 仿真监控
- 集成 SimulationMonitor 组件
- 显示批次进度、仿真列表、实时更新
- 实现 [开始批量仿真]、[取消仿真] 按键
- 显示日志查看功能

**Task 2.11: 案例管理页面 - 批次管理** (1天)
- 实现 case-simulation-center.html 的 Tab 3: 批次管理
- 显示已完成的批次列表
- [分析结果] 按键 → 跳转到 analysis_viewer.html
- [导出] 功能

**Task 2.12: 分析结果页面 - 分析进度监控** (1.5天)
- 实现 analysis_viewer.html 的进度监控
- 从 URL 获取 batch_id 参数
- 自动启动分析 (如果未运行)
- 实时显示分析进度
- 自动加载完成后的结果

**Task 2.13: 分析结果页面 - 结果展示** (1.5天)
- 集成 AnalysisResultsDashboard 组件
- 从 API 获取分析结果并展示
- 支持多个 Tab: 概览 | 路段分析 | 对比分析 | 详细指标 | 导出

**小计**: 10天 Frontend 开发

### Backend Tasks (Task 2.14-2.16)

**Task 2.14: 案例列表 API 增强** (1天)
- 扩展 GET /api/v1/case/list 支持:
  - status 筛选
  - source_scenario_id 筛选
  - 搜索功能
  - 分页支持
- 新增 GET /api/v1/case/list-by-scenario 端点

**Task 2.15: 批量仿真 API 验证** (1天)
- 验证 /api/v1/simulation/batch-start 使用 SimulationOrchestrator
- 确保 auto_run_analysis 参数正确传递
- 验证响应结构正确

**Task 2.16: 分析自动启动集成** (1天)
- 在 SimulationOrchestrator 中实现分析自动启动
- 所有仿真完成时调用 AnalysisOrchestrationService
- 返回 analysis_batch_id

**小计**: 3天 Backend 开发

---

## 已完成部分 (Existing)

### Backend Services ✅
- SimulationOrchestrator (290 LOC) - 编排层
- AnalysisOrchestrationService - 适配器
- AnalysisResultsService (966 LOC) - 结果聚合
- 数据模型 (Pydantic)

### Frontend Components ✅
- shared-utils.js - 通用工具
- api-client.js - API 调用
- simulation-monitor.js - 进度监控
- analysis-results.js - 结果展示

### Pages ✅
- scenario_browser.html - 场景浏览 (部分功能)
- case-simulation-center.html - 框架已有，需完善
- analysis_viewer.html - 框架已有，需完善

---

## 实现时间线

### Week 1 (Frontend - 5天)
- Task 2.8: 创建案例功能 (1.5天)
- Task 2.9: 案例列表与筛选 (2天)
- Task 2.10: 仿真监控 (2天)

### Week 2 (Frontend + Backend - 5天)
- Task 2.11: 批次管理 (1天)
- Task 2.12: 分析进度监控 (1.5天)
- Task 2.13: 分析结果展示 (1.5天)
- Task 2.14: 案例列表 API (1天)

### Week 3 (Backend Verification - 2天)
- Task 2.15: 批量仿真 API 验证 (1天)
- Task 2.16: 分析自动启动 (1天)

### 总计: 2-3周 (13天)

---

## 关键设计决策

### 创建案例功能 (Q1)
**位置**: scenario_browser.html
**理由**: 用户需要先选择场景，流程一致
**实现**: 行级 [创建案例] 按键 + 模态框

### 案例管理设计 (Q2)
**结构**: case-simulation-center.html 三个 Tab
**Tab 1**: 静态案例列表 (支持筛选)
**Tab 2**: 动态仿真监控 (实时更新)
**Tab 3**: 批次历史 (完成后导航)

### 场景筛选 (Q3)
**方案**: 后端 API + 前端缓存
**新API**: GET /api/v1/case/list-by-scenario?scenario_id=xxx
**好处**: 利用元数据索引，减少前端复杂度

### 分析自动启动 (Q4)
**参数**: auto_run_analysis=true
**流程**: 所有仿真完成 → 自动启动分析
**效果**: 减少用户操作，自动化工作流

### 分析功能复用 (Q5)
**方案**: AnalysisOrchestrationService 作为适配器
**好处**: 不修改现有分析服务，只创建适配层
**实现**: 前端调用 /analysis/run-batch 和 /analysis/results

---

## API 端点清单

### 新增端点

| 端点 | 方法 | 用途 | 优先级 |
|------|------|------|--------|
| /api/v1/case/list-by-scenario | GET | 按场景ID获取案例 | P0 |
| /api/v1/case/list (改进) | GET | 支持筛选和搜索 | P0 |
| /api/v1/simulation/batch-list | GET | 获取批次历史 | P1 |

### 已有端点 (验证)

| 端点 | 方法 | 用途 | 状态 |
|------|------|------|------|
| /api/v1/case/create-from-scenario | POST | 从场景创建案例 | ✅ |
| /api/v1/simulation/batch-start | POST | 启动批量仿真 | ⚠️ 验证 |
| /api/v1/simulation/batch-status | GET | 获取批量状态 | ✅ |
| /api/v1/analysis/run-batch | POST | 启动分析批处理 | ✅ |
| /api/v1/analysis/batch-progress | GET | 获取分析进度 | ✅ |
| /api/v1/analysis/results | GET | 获取分析结果 | ✅ |

---

## 数据流详解

### 创建案例流程
```
场景浏览页面
  ↓ 用户点击 [创建案例]
  ↓ 显示模态框 (预填场景信息)
  ↓ 用户填写可选参数 (仿真时长、随机种子等)
  ↓ 提交表单
  ↓ POST /api/v1/case/create-from-scenario
  ↓ 后端创建 case + simulation
  ↓ 返回 case_id
  ↓ 跳转 case-simulation-center.html?case_id={case_id}
```

### 批量仿真流程
```
案例管理页面 Tab 1
  ↓ 用户选择案例
  ↓ 点击 [批量仿真]
  ↓ 显示选择仿真的对话框
  ↓ 用户确认选择
  ↓ POST /api/v1/simulation/batch-start
  │ {
  │   simulation_ids: [...],
  │   parallel_workers: 4,
  │   auto_run_analysis: true
  │ }
  ↓ 返回 batch_id
  ↓ 自动切换到 Tab 2 (仿真监控)
  ↓ 开始轮询 /api/v1/simulation/batch-status/{batch_id}
  ↓ 所有仿真完成
  ↓ 如果 auto_run_analysis=true:
  │ └─ 自动启动分析 (调用 /api/v1/analysis/run-batch)
  ↓ 停止轮询
```

### 分析结果流程
```
批次管理 Tab 3
  ↓ 用户点击 [分析结果]
  ↓ 跳转 analysis_viewer.html?batch_id={batch_id}
  ↓ 或从仿真监控自动跳转
  ↓
分析结果页面
  ↓ 检查分析状态
  ├─ 如果未开始 → 自动启动分析
  │   └─ POST /api/v1/analysis/run-batch
  ├─ 如果运行中 → 轮询进度
  │   └─ 轮询 /api/v1/analysis/batch-progress/{batch_id}
  └─ 如果完成 → 获取结果
      └─ GET /api/v1/analysis/results/{batch_id}
  ↓
  ↓ 使用 AnalysisResultsDashboard 组件展示结果
```

---

## 页面间导航

### URL 参数约定

```javascript
// 从场景浏览到案例管理
window.location.href = `case-simulation-center.html?case_id=${case_id}`;

// 从案例管理到分析结果
window.location.href = `analysis_viewer.html?batch_id=${batch_id}`;

// 或从批次ID
window.location.href = `analysis_viewer.html?batch_id=${batch_id}&case_id=${case_id}`;
```

### SessionStorage 使用

```javascript
// 保存当前批次ID (用于Tab间共享)
sessionStorage.setItem('current_batch_id', batch_id);

// 保存当前案例ID (用于上下文)
sessionStorage.setItem('current_case_id', case_id);

// 获取批次ID
const batch_id = sessionStorage.getItem('current_batch_id');
```

---

## 前端组件使用示例

### SimulationMonitor 组件
```javascript
import { SimulationMonitor } from '../components/simulation-monitor.js';
import { APIClient } from '../components/api-client.js';

const api = new APIClient();
const monitor = new SimulationMonitor('simulationContainer', api);

// 开始监控
await monitor.startMonitoring(batch_id, 'event-scenario');

// 监听完成事件 (可选)
monitor.on('complete', () => {
    console.log('仿真完成，开始分析');
});
```

### AnalysisResultsDashboard 组件
```javascript
import { AnalysisResultsDashboard } from '../components/analysis-results.js';

const dashboard = new AnalysisResultsDashboard('analysisContainer', api);

// 渲染结果
dashboard.render({
    edgedata: results.data.edgedata,
    tripinfo: results.data.tripinfo,
    performance: results.data.performance,
    comparison: results.data.comparison
});

// 或仅显示进度
dashboard.updateProgress({
    total: 160,
    completed: 104,
    failed: 2,
    current: {
        simulation_id: 'sim_123',
        analysis_type: 'edgedata',
        progress: 72
    }
});
```

---

## 错误处理与重试

### 前端级别
- API 调用失败 → 显示用户友好的错误信息
- 提供 [重试] 按键
- 3次失败后放弃

### 后端级别 (需要实现)
- 临时性错误 (网络、文件锁) → 自动重试 (3次，指数退避)
- 验证错误 (文件不存在、无效XML) → 立即失败，无重试

### 实现位置
- 前端: api-client.js 中的请求包装器
- 后端: shared/utilities/retry_utils.py

---

## 测试计划

### 单元测试
- API 模型验证
- 工作流逻辑 (模拟 API)

### 集成测试
- 端到端工作流: 创建案例 → 启动仿真 → 查看分析

### 手工测试清单
- [ ] 创建案例: 从场景浏览页面创建
- [ ] 案例列表: 加载、筛选、搜索
- [ ] 批量仿真: 启动、监控进度、查看日志
- [ ] 分析结果: 自动启动、进度显示、结果展示
- [ ] 页面导航: 创建 → 案例 → 仿真 → 分析
- [ ] 错误处理: API 失败、网络错误

---

## 性能考量

### 轮询间隔
- 仿真监控: 5秒 (不要太频繁)
- 分析进度: 5秒
- 案例列表刷新: 10秒 (用户主动)

### 数据分页
- 案例列表: 50条/页
- 仿真列表: 20条/页
- 批次历史: 10条/页

### 缓存策略
- 场景数据: 在内存中缓存 (1分钟)
- API 响应: 不缓存 (实时性重要)

---

## 文档更新

需要更新的文档:
1. CLAUDE.md - 添加新的工作流部分
2. docs/PHASE_2_USER_GUIDE.md - 用户指南
3. docs/PHASE_2_API_REFERENCE.md - API 文档
4. WORKFLOW_DESIGN.md - 工作流设计 (已创建)

---

## 风险与缓解

### 高风险
- 分析耗时过长 → 提供进度和 ETA
- 网络不稳定 → 自动重试机制
- 用户误操作 → 确认对话框

### 中等风险
- 浏览器回退混乱状态 → 使用 URL 状态恢复
- 组件兼容性问题 → 充分测试各浏览器

---

## 交付清单

- [ ] WORKFLOW_DESIGN.md (已完成)
- [ ] tasks.md (Tasks 2.7-2.16, 已完成)
- [ ] Task 2.8-2.13 代码实现
- [ ] Task 2.14-2.16 代码实现
- [ ] 单元测试
- [ ] 集成测试
- [ ] 手工测试报告
- [ ] 用户文档更新
- [ ] API 文档更新

---

**实现总结完成。准备进入开发阶段。**
