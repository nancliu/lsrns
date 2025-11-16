# Phase 2 前后端 API 端点确认 - 总体指南

**版本**: 1.0
**日期**: 2025-11-16
**状态**: ✅ 完成并验证

---

## 📌 本文档的目的

为 Phase 2 "事件场景案例管理 UI 重构" 项目提供：
- ✅ 完整的 API 端点清单
- ✅ 前后端接口对接规范
- ✅ 批次 ID 传递的正确方式
- ✅ 实现验证检查清单
- ✅ 范围和责任边界界定

---

## ⚠️ 核心原则

**case-simulation-center.html 只管理和监测事件案例批次。**

- ✅ case-simulation-center.html：管理事件批次的案例和仿真进度
- ❌ case-simulation-center.html 不用于管控方案优化批次
- ❌ case-simulation-center.html 不处理用户手动选择的优化仿真列表

详见 [SCOPE_CLARIFICATION.md](SCOPE_CLARIFICATION.md)

---

## 📂 文档导航

### 1️⃣ **API_ENDPOINTS_GUIDE.md** ⭐ 必读
最全面的 API 参考文档，包含：
- 所有 4 个核心 API 端点
- 完整的请求/响应格式
- 前端代码示例
- 后端服务实现指南
- 错误处理和验证清单

**适用于**: 前端开发、后端开发、接口联调

---

### 2️⃣ **API_QUICK_REFERENCE.md** ⭐ 推荐打印
快速参考卡片，包含：
- API 速查表
- 常见错误排查
- 前端调用示例（代码片段）
- curl 测试命令
- 性能指标

**适用于**: 开发过程中快速查阅

---

### 3️⃣ **BATCH_ID_CLARIFICATION.md** ⭐ 重要
澄清批次 ID 的两种传递方式：
- 事件批次（batch_event_...）vs 优化批次（batch_...）
- 两种工作流的对比
- 常见错误和修复
- 决策矩阵

**适用于**: 理解两种批次模式的区别

---

### 4️⃣ **IMPLEMENTATION_VERIFICATION_CHECKLIST.md** ⭐ 验收
详细的验收清单，包含：
- API 端点验证项
- 前端功能验证项
- 数据准确性验证
- 性能验证
- 浏览器兼容性
- 集成测试场景

**适用于**: QA 测试和最终验收

---

### 5️⃣ **SCOPE_CLARIFICATION.md** ⭐ 重要
明确范围和责任边界：
- Phase 2 包括什么
- Phase 2 不包括什么（管控方案优化）
- 与其他模块的关系
- 常见混淆点澄清

**适用于**: 项目管理、需求确认

---

### 6️⃣ **CASE_SIMULATION_CENTER_SCOPE.md** ⭐ 关键
明确 case-simulation-center.html 的单一职责：
- case-simulation-center.html 只管理事件批次
- 不处理优化批次和策略管理
- 不实现方案优化功能
- 实现检查清单

**适用于**: 前端开发、架构理解

---

### 7️⃣ **EVENT_SCENARIO_ENDPOINTS.md** ⭐ 核心
事件场景仿真的专用端点和接口：
- `/api/v1/batch/*` 事件批次管理端点
- `/api/v1/scenario/*` 场景管理端点
- 推荐的工作流示意
- API 选择矩阵
- 前端实现建议

**适用于**: 前端开发、后端开发、API 集成

---

## 🎯 核心 API 快速索引

### Phase 2 中使用的 4 个核心 API

| # | 端点 | 方法 | 功能 | 优先级 |
|---|------|------|------|--------|
| 1 | `/api/v1/simulation/simulation_progress/{case_id}` | GET | 获取进度 | 🔴 必须 |
| 2 | `/api/v1/analysis/comparison/{batch_id}` | GET | 对比分析 | 🔴 必须 |
| 3 | `/api/v1/simulation/simulations/{case_id}` | GET | 仿真列表 | 🟠 重要 |
| 4 | `/api/v1/simulation/batch-start` | POST | 启动批次 | 🟠 重要 |

---

## 📋 前后端分工清单

### 前端需要实现的

#### case-simulation-center.html
```
☐ 展开/折叠式进度监控面板
  ├─ 折叠状态：进度条 + 4 个统计卡片
  ├─ 展开状态：详细表格 + 筛选 + 排序
  ├─ 动态刷新频率（展开5-10s，折叠30s）
  └─ "查看分析"按钮跳转到 analysis_viewer.html

☐ 响应式设计
  ├─ 移动设备：单列、可滚动表格
  ├─ 平板：双列网格
  └─ 桌面：四列网格
```

#### analysis_viewer.html
```
☐ 批次对比分析标签页
  ├─ 案例选择器（多选）
  ├─ 对比表格（含差异百分比）
  ├─ 改善/恶化颜色标记
  └─ URL 参数支持 (?case_ids=...)

☐ 响应式设计优化
  └─ 各断点下正常显示
```

### 后端需要验证的

```
☐ /api/v1/simulation/simulation_progress/{case_id}
  ├─ 返回格式完整
  ├─ progress_percentage 计算正确（0-100）
  ├─ simulations 数组包含所有必需字段
  └─ 响应时间 < 2s

☐ /api/v1/analysis/comparison/{batch_id}
  ├─ 支持 ?case_id 参数
  ├─ 差异百分比计算正确
  ├─ improvement 字段正确判断
  └─ 响应时间 < 2s

☐ 其他端点
  ├─ /api/v1/simulation/simulations/{case_id}
  ├─ /api/v1/simulation/batch-start
  └─ /api/v1/simulation/simulation/{simulation_id}
```

---

## 🚀 快速开发指南

### Day 1: 后端准备

```bash
1. 验证 /api/v1/simulation/simulation_progress/{case_id} 工作正常
   curl -X GET "http://localhost:8000/api/v1/simulation/simulation_progress/case_001"

2. 验证 /api/v1/analysis/comparison/{batch_id} 工作正常
   curl -X GET "http://localhost:8000/api/v1/analysis/comparison/batch_001?case_id=case_001"

3. 验证响应格式和性能 < 2s
```

### Day 2-3: 前端开发

```
1. 实现进度监控面板展开/折叠
2. 实现动态刷新（5-10s vs 30s）
3. 实现表格筛选和排序
4. 实现"查看分析"导航
```

### Day 4-5: 对比分析功能

```
1. 实现案例选择器
2. 实现对比表格
3. 实现颜色标记（改善/恶化）
4. 实现 URL 参数
```

### Day 6: 响应式设计和测试

```
1. 优化响应式断点
2. 运行 IMPLEMENTATION_VERIFICATION_CHECKLIST.md 中的所有项
3. 多浏览器测试
4. 性能测试
```

---

## ⚠️ 关键注意事项

### 1️⃣ 批次 ID 的正确用法

```javascript
✅ 进度查询：用 case_id
   GET /api/v1/simulation/simulation_progress/{case_id}

✅ 对比分析：用 batch_id
   GET /api/v1/analysis/comparison/{batch_id}?case_id=...

❌ 不要混淆 simulation_ids 和 batch_id
❌ 不要用 batch_id 替代 case_id 查询进度
```

### 2️⃣ 响应式设计的标准断点

```css
/* 统一使用这些断点 */
@media (max-width: 767px) { ... }      /* 移动 */
@media (min-width: 768px) { ... }      /* 平板 */
@media (min-width: 1200px) { ... }     /* 桌面 */
@media (min-width: 1920px) { ... }     /* 超大屏 */
```

### 3️⃣ 进度百分比的刷新频率

```javascript
if (monitoringPanelIsExpanded) {
  刷新频率 = 5-10 秒  // 用户可以看到动作
} else {
  刷新频率 = 30 秒   // 节省服务器资源
}
```

### 4️⃣ 范围界定：事件分析 ≠ 方案优化

```
✅ Phase 2 包括：事件影响分析 UI
❌ Phase 2 不包括：管控方案优化管理
❌ Phase 2 不包括：控制策略库维护

→ 查看 SCOPE_CLARIFICATION.md 了解详情
```

---

## 📊 验收标准概览

完成 Phase 2 时，需要通过：

- [ ] **API 验证** (API_ENDPOINTS_GUIDE.md)
  - 4 个核心 API 端点全部可用
  - 响应格式正确
  - 响应时间 < 2s

- [ ] **功能验证** (IMPLEMENTATION_VERIFICATION_CHECKLIST.md)
  - 进度监控面板展开/折叠正常
  - 表格筛选和排序正常
  - 对比分析表格正确
  - "查看分析"按钮跳转正常

- [ ] **数据准确性验证**
  - 进度百分比计算正确
  - 差异百分比计算正确 `(B-A)/A*100`
  - 改善/恶化判断正确

- [ ] **响应式设计验证**
  - 移动设备正常显示
  - 平板设备正常显示
  - 桌面设备正常显示
  - 各断点无布局抖动

- [ ] **浏览器兼容性验证**
  - Chrome ✅
  - Firefox ✅
  - Edge ✅
  - Safari (如可用) ✅

- [ ] **集成测试**
  - 完整工作流测试
  - 批次模式测试
  - 错误情况测试

---

## 🔍 常见问题速查

### Q1: 进度不更新？
**A**: 查看 API_QUICK_REFERENCE.md 中的"进度不更新"排查

### Q2: 对比数据不显示？
**A**: 查看 API_QUICK_REFERENCE.md 中的"对比分析不显示"排查

### Q3: 应该用哪个批次 API？
**A**: 查看 BATCH_ID_CLARIFICATION.md 中的"决策矩阵"

### Q4: 性能太慢？
**A**: 查看 API_ENDPOINTS_GUIDE.md 中的"性能验证"部分

### Q5: 这是否包括方案优化功能？
**A**: 不包括。查看 SCOPE_CLARIFICATION.md 了解范围界定

---

## 📞 文件速查表

| 我想... | 看这个文件 |
|--------|-----------|
| 了解所有 API 端点 | API_ENDPOINTS_GUIDE.md |
| 快速查看示例代码 | API_QUICK_REFERENCE.md |
| 理解批次 ID 的用法 | BATCH_ID_CLARIFICATION.md |
| 理解事件场景仿真接口 | EVENT_SCENARIO_ENDPOINTS.md |
| 确认 case-simulation-center.html 范围 | CASE_SIMULATION_CENTER_SCOPE.md |
| 进行测试验收 | IMPLEMENTATION_VERIFICATION_CHECKLIST.md |
| 确认项目范围 | SCOPE_CLARIFICATION.md |
| 查看详细规范 | specs/ 目录中的三个文件 |
| 查看实现任务 | tasks.md |
| 查看项目提案 | proposal.md |

---

## ✅ 成功标志

当你看到以下情况时，说明 Phase 2 成功实现：

- ✅ 用户可以在 case-simulation-center.html 展开/折叠进度监控
- ✅ 进度条平滑更新，统计卡片数字正确
- ✅ 表格支持筛选和排序
- ✅ 用户可以点击"查看分析"跳转到分析页面
- ✅ 在 analysis_viewer.html 可以选择多个案例进行对比
- ✅ 对比表格显示差异百分比，颜色标记正确
- ✅ 在移动设备上也能正常使用（表格可滚动）
- ✅ URL 参数支持书签和分享
- ✅ 所有 4 个核心 API 响应时间 < 2s
- ✅ 通过完整的验收清单检查

---

## 🎓 相关文档阅读顺序

**首次阅读建议**:

1. **本文件** (README.md) - 10 分钟 - 全面了解
2. **SCOPE_CLARIFICATION.md** - 15 分钟 - 理解范围
3. **API_QUICK_REFERENCE.md** - 5 分钟 - 快速参考
4. **API_ENDPOINTS_GUIDE.md** - 30 分钟 - 深入理解
5. **BATCH_ID_CLARIFICATION.md** - 20 分钟 - 批次模式
6. **IMPLEMENTATION_VERIFICATION_CHECKLIST.md** - 查阅 - 逐项验证

**日常查阅**:
- 开发时：API_QUICK_REFERENCE.md
- 调试时：API_ENDPOINTS_GUIDE.md
- 测试时：IMPLEMENTATION_VERIFICATION_CHECKLIST.md

---

## 📝 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2025-11-16 | 1.0 | 初始版本，包含 5 份详细文档 |

---

## 📞 联系方式

遇到问题？

1. 🔍 先查看本 README 的常见问题部分
2. 📖 查阅对应的详细文档
3. 💬 与前后端开发人员沟通

---

## 🎉 致谢

感谢所有参与 Phase 2 项目的开发、测试和管理人员的努力！

---

**最后更新**: 2025-11-16
**文档负责人**: 系统架构团队
**适用版本**: Phase 2 及以后
