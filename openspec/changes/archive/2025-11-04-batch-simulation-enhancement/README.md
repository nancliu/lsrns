# 批量仿真配置增强 - OpenSpec变更

**项目名称**: 批量仿真配置功能增强
**Status**: ✅ 需求确认完成，准备实施
**版本**: v1.0
**创建日期**: 2025-11-03
**预计工期**: 3个工作日
**优先级**: P0 (核心功能)

---

## 📌 快速导航

| 文档 | 描述 | 主要内容 |
|------|------|--------|
| **[spec.md](./spec.md)** | 需求规格书 | 功能详细描述、API规格、数据模型、验收标准 |
| **[plan.md](./plan.md)** | 实现计划 | 技术方案、代码组织、架构设计、风险评估 |
| **[tasks.md](./tasks.md)** | 任务清单 | 24个待实现任务、优先级、依赖关系、完成标准 |
| **[README.md](./README.md)** | 本文件 | 项目概述、变更摘要、快速开始 |

---

## 🎯 变更概览

本OpenSpec变更为**批量仿真配置页**增加4项核心功能，提升用户体验和系统灵活性。

### 功能 1: 仿真时长设置 ⏱️

**问题**: 用户无法自定义仿真时长，仅限于输入数据的时间范围

**解决方案**:
- 支持超过输入数据时长的仿真（已有车辆继续运行，但不再进入新车辆）
- 支持短于输入数据时长的仿真
- 默认使用输入数据时长（保持向后兼容）

**UI**:
```
时长配置：
(◉) 使用输入数据时长 - 当前: 7h30m (07:00-14:30)
(○) 自定义仿真时长  - [8]小时 [30]分钟
```

**应用场景**:
- 观察交通流长期稳定状态（延长仿真时间）
- 快速验证方案效果（缩短仿真时间）
- 特定时段仿真（例如仅模拟早高峰）

---

### 功能 2: Vehicle Types模板选择 🚗

**问题**: 所有batch使用相同的车辆参数，无法测试不同驾驶行为的影响

**解决方案**:
- 支持从 `templates/config_templates/vehicle_templates/` 选择不同的JSON模板
- 模板文件名格式：`vehicle_types.json`, `vehicle_types_tj1.json` 等
- 批量级别统一选择（整个batch使用同一模板）

**UI**:
```
车辆类型模板：
[▼ vehicle_types.json (默认参数)]
   其他可选: vehicle_types_tj1.json (激进驾驶参数)
           vehicle_types_tj2.json (保守驾驶参数)
```

**应用场景**:
- A/B对比：激进驾驶 vs 保守驾驶对流量影响
- 区域参数适配：不同城市的车辆参数差异
- 参数敏感性分析

---

### 功能 3: 输出配置简化 📊

**问题**: 当前的"minimal/standard/full"三级分类过于抽象，用户不清楚各级别包含哪些输出

**解决方案**:
- 移除抽象的3级分类
- 改为4个具体的输出项，用户一目了然
- Summary和E1检测器固定启用
- Edgedata和Tripinfo可选，带性能提示

**UI**:
```
仿真输出配置：
☑ summary.xml (基础统计) - 总是启用
☑ E1检测器数据 (门架流量) - 总是启用
☐ edgedata.xml (路段流量)  ⚠️ +20%仿真时间
☐ tripinfo.xml (车辆行程)  ⚠️ +30%仿真时间
```

**优势**:
- 用户明确知道输出文件类型
- 性能提示帮助决策
- 灵活组合而非固定预设
- 减少创建无用输出的浪费

---

### 功能 4: 批次任务预估简化 📈

**问题**: 批次任务预估显示过多信息，页面长度过长

**解决方案**:
- 移除"种子序列: 66, 67, 68"显示
- 保留关键信息：任务数量估算
- 减少页面纵向占用 ~10%

**UI变更**:
```
移除前: 1个方案 × 3个随机种子 = 3个并行仿真任务
       种子序列: 66, 67, 68

移除后: 1个方案 × 3个随机种子 = 3个并行仿真任务
```

---

## 🏗️ 技术实现总览

### 架构设计

```
Frontend (HTML + JS + CSS)
    ↓ (HTTP POST /api/v1/control/batch-optimization/batch)
API Layer (routes)
    ↓ (验证请求)
Service Layer (batch_optimization_service)
    ↓ (业务逻辑)
Shared Layer (scheduler, sumo_utils)
    ↓ (生成配置)
SUMO Config (simulation.sumocfg)
    ↓ (执行)
Simulation Results
```

### 核心变更点

#### Frontend (3个文件修改)
- **simulations.html**: 更新表单UI（网格布局，4个output checkbox，时长radio，template dropdown）
- **batch_simulation.js**: 新增时长验证逻辑、模板加载、简化任务估算
- **simulations.css**: 网格布局样式、性能提示样式、响应式设计

#### Backend API (4个文件修改)
- **batch_optimization_routes.py**: 新增 `/template/vehicle-types/list` 端点，修改 `/batch` 端点
- **batch_request.py**: 新增 `SimulationDuration`, `OutputConfig` 模型
- **batch_optimization_service.py**: 处理新字段，保存到simulation_config.json
- **sumo_utils.py**: 支持自定义时长、vehicle templates、output_config

#### Data Format (simulation_config.json)

**旧格式** → **新格式**:
```python
# 旧 (v0.x)
{
  "output_level": "standard",  # ❌ 移除
  "num_seeds": 3,
  "base_seed": 66,
  "seed_sequence": [66, 67, 68]  # ❌ 移除
}

# 新 (v1.0)
{
  "num_seeds": 3,
  "base_seed": 66,
  "simulation_duration": {  # ✅ 新增
    "use_default": false,
    "hours": 8,
    "minutes": 30,
    "total_minutes": 510
  },
  "vehicle_types_template": "vehicle_types_tj1.json",  # ✅ 新增
  "output_config": {  # ✅ 新增
    "summary_xml": true,
    "e1_detector_data": true,
    "edgedata_xml": false,
    "tripinfo_xml": false
  }
}
```

---

## 🔄 向后兼容性

本变更完全向后兼容：

1. **旧API请求仍能工作** ✅
   - 保留 `output_level` 字段（deprecated）
   - 自动映射到新的 `output_config`
   - 示例：`output_level: "standard"` → `output_config: { edgedata_xml: true, tripinfo_xml: true }`

2. **旧批次仍可执行** ✅
   - 代码同时支持读取旧/新格式的 simulation_config.json
   - 执行时动态升级配置格式

3. **无数据损失** ✅
   - 现有batch文件夹结构不变
   - 仅配置文件格式升级（新字段追加，无删除）

---

## 📊 UI布局优化

采用**网格式布局**，相关参数横向排列：

```
┌─────────────────────────────────────────────────────────┐
│ 仿真配置                                          [+展开] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [案例选择]           [方案选择 ☑baseline ☐plan_vss]   │
│                                                         │
│ [使用数据时长]       [自定义时长 8小时 30分钟]        │
│ 当前: 7h30m          ℹ️ 可设1分-24小时                  │
│                                                         │
│ [vehicle_types.json] [☑summary ☑E1检测器 ☐edgedata]   │
│ (默认参数)           [☐tripinfo +30%仿真时间]          │
│                                                         │
│ 随机种子数: [3]      起始种子: [66]                    │
│                                                         │
│ ┌──────────────────────────────────────────────────┐  │
│ │ 3个方案 × 3个随机种子 = 9个并行仿真任务         │  │
│ └──────────────────────────────────────────────────┘  │
│                                                         │
│              [清除配置]  [创建批次 →]                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**优势**:
- ✅ 相关配置项横向并排，逻辑清晰
- ✅ 页面高度减少40-50%
- ✅ 响应式设计（在小屏幕自动堆叠）
- ✅ 视觉层级分明（分成5个逻辑行）

---

## 📋 实施计划

| Phase | 内容 | 工作量 | 预计时间 |
|-------|------|--------|---------|
| **1** | 输出配置简化 | 6h | 1天 |
| **2** | Vehicle模板选择 | 4h | 0.5天 |
| **3** | 仿真时长设置 | 5h | 1天 |
| **4** | 任务预估简化 | 0.5h | <1h |
| **5** | E2E测试 + 文档 | 3h | 0.5天 |
| **总计** | | **18.5h** | **3天** |

### 关键里程碑
- **Day 1 EOD**: Phase 1完成，批次创建功能仍可用
- **Day 2 EOD**: Phase 2和3完成，所有核心功能可用
- **Day 3 EOD**: 完整测试和文档交付

---

## 🧪 测试策略

### 测试覆盖范围

| 测试类型 | 数量 | 优先级 |
|---------|------|--------|
| 单元测试 | 15+ | P0 |
| 集成测试 | 10+ | P0 |
| E2E测试 | 6+ | P1 |
| 向后兼容性测试 | 3+ | P0 |

### 关键测试用例

1. **创建batch with自定义时长8h30m** - 验证时长计算
2. **创建batch with vehicle_types_tj1.json** - 验证模板加载
3. **创建batch仅启用edgedata** - 验证SUMO配置
4. **输入25小时** - 验证错误提示
5. **使用旧API格式（output_level）** - 验证兼容性
6. **读取旧format的simulation_config.json** - 验证兼容性

---

## 📚 相关文档

### 项目文档
- [CLAUDE.md](../../CLAUDE.md) - 项目规范和架构
- [新架构API指南](../../docs/api_docs/新架构API指南.md) - API文档
- [架构重构完成报告](../../docs/development/架构重构完成报告.md) - 架构说明

### 实现文档
- [spec.md](./spec.md) - 详细需求规格
- [plan.md](./plan.md) - 技术实现方案
- [tasks.md](./tasks.md) - 24个待实现任务清单

---

## ✅ 验收标准

**最终交付物需满足**:

- [ ] 所有4项功能正常工作
- [ ] UI符合设计规格（网格布局、2列并排）
- [ ] 单元测试覆盖率 ≥90%
- [ ] 所有E2E测试通过
- [ ] 向后兼容性验证完成
- [ ] 零回归缺陷
- [ ] API文档更新完整
- [ ] 用户指南编写完成
- [ ] Release Notes编写完成

---

## 🚀 快速开始

### 1️⃣ 了解需求
```bash
# 查看需求规格
cat spec.md

# 关键内容：
# - 4个新功能的详细描述
# - API规格和数据模型
# - UI设计和交互细节
```

### 2️⃣ 理解实现方案
```bash
# 查看实现计划
cat plan.md

# 关键内容：
# - 前后端代码修改清单
# - HTML/JS/CSS结构
# - 数据库/文件系统变更
```

### 3️⃣ 执行任务清单
```bash
# 查看待实现任务
cat tasks.md

# 按优先级执行：
# Phase 1: Output Config (1天)
# Phase 2: Vehicle Template (0.5天)
# Phase 3: Duration Setting (1天)
# Phase 4: UI Cleanup (<1h)
# Phase 5: Testing & Docs (0.5天)
```

### 4️⃣ 测试验证
```bash
# 运行单元测试
pytest tests/unit/test_output_config.py
pytest tests/unit/test_simulation_duration.py
pytest tests/unit/test_vehicle_template_loading.py

# 运行集成测试
pytest tests/integration/test_batch_creation_output_config.py

# 运行E2E测试
npx playwright test tests/e2e/test_batch_simulation_enhancements.spec.js
```

---

## 📞 联系和反馈

- **问题或阻力**: 创建issue或更新 [ISSUES.md](./ISSUES.md)
- **设计讨论**: 查看 spec.md 中的"风险评估"部分
- **代码评审**: PR时参考 tasks.md 中的"完成标准"

---

## 📝 变更历史

| 版本 | 日期 | 状态 | 备注 |
|------|------|------|------|
| v1.0 | 2025-11-03 | ✅ 需求确认 | 初始OpenSpec文档 |

---

## 🎓 学习资源

### 相关代码文件
- Frontend: `frontend/control/simulations.html`, `batch_simulation.js`
- Backend: `api/routes/batch_optimization_routes.py`, `api/services/batch_optimization_service.py`
- Shared: `shared/utilities/sumo_utils.py`

### 相关概念
- **SUMO Configuration**: `simulation.sumocfg` XML格式
- **Pydantic Models**: 请求/响应数据验证
- **Grid Layout**: CSS网格系统布局
- **向后兼容**: 字段映射、版本管理

---

**Prepared by**: Traffic Simulation Team
**Last Updated**: 2025-11-03
**Status**: ✅ Ready for Implementation

---

> 💡 **提示**: 如需快速了解全貌，建议先读README.md（本文），再深入阅读spec.md和tasks.md
