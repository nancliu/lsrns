# templates.html 脚本优化方案

## 当前状态分析

### 文件结构

```
frontend/control/templates.html (4279 行)
├── <head> 部分
│   ├── CSS 文件引用 (5个独立CSS文件)
│   └── JS 文件引用 (3个模块)
│       ├── timeline_converter.js
│       ├── timeline_visualizer.js
│       └── parameter_form.js
│
├── <body> HTML 结构 (1-380行)
│
├── 第一个 <script> 内联块 (381-4078行, **3698行代码**)
│   ├── 全局状态变量
│   ├── 初始化函数
│   ├── 模板管理 (fetch/render/select)
│   ├── 步骤控制 (wizard navigation)
│   ├── 参数表单生成
│   ├── 参数验证
│   ├── 策略名称/描述生成
│   ├── 策略实例管理 (CRUD)
│   └── EdgeDisplayTable 类
│
├── 外部JS文件引用 (4个模块，4070-4076行)
│   ├── notification.js
│   ├── edge_selector_embedded.js
│   ├── network_viz.js
│   └── strategy_manager.js
│
└── 第二个 <script> 内联块 (4079-4276行, **198行代码**)
    ├── 模块加载检查
    ├── network_viz 初始化
    └── loadVisualization() 函数
```

### 问题诊断

#### 1. **严重的代码组织问题**

**第一个 `<script>` 块 (3698行)** 包含 **83个函数**，职责混杂：

| 功能类别 | 函数数量 | 典型函数 | 应该属于的模块 |
|---------|---------|---------|---------------|
| 模板管理 | 6 | `fetchTemplates`, `renderTemplateCards`, `selectTemplate` | **template_selector.js** |
| 步骤控制 | 4 | `updateStepDisplay`, `nextStep`, `previousStep` | **wizard_controller.js** |
| 参数表单生成 | 10+ | `generateParamsForm`, `createStringControl`, `createSelectControl` | **parameter_form.js (已存在)** |
| 参数验证 | 5 | `validateParameterValue`, `validateAllParameters` | **form_validator.js** |
| 策略命名 | 4 | `setupNameChangeTracking`, `setupSuggestNameButton` | **strategy_namer.js** |
| 策略描述生成 | 8 | `autoPopulateStrategyDescription`, `StrategyDescriptionGenerator` 类 | **strategy_describer.js** |
| 策略实例管理 | 8 | `fetchStrategyInstances`, `createStrategy`, `deleteStrategy` | **strategy_crud.js** |
| 边缘显示 | 15 | `EdgeDisplayTable` 类及方法 | **edge_display.js (已存在)** |
| 其他工具函数 | 23 | `formatStake`, `translateDirection`, `collectParameterValues` | 各自所属模块 |

**第二个 `<script>` 块 (198行)** 包含：
- 模块加载检查代码（应该在开发/调试工具中）
- `loadVisualization()` 函数（应该在 `edge_selector_embedded.js` 或独立模块）

#### 2. **JS文件引用顺序混乱**

```html
<!-- 头部引用 (加载早) -->
<script src="js/timeline_converter.js"></script>
<script src="js/timeline_visualizer.js"></script>
<script src="js/parameter_form.js"></script>

<!-- 3698行内联代码 -->
<script>
  // 大量代码依赖上面的模块
</script>

<!-- 底部引用 (加载晚) -->
<script src="js/notification.js"></script>
<script src="js/edge_selector_embedded.js"></script>
<script src="js/network_viz.js"></script>
<script src="js/strategy_manager.js"></script>

<!-- 第二个内联块 -->
<script>
  // 依赖上面的模块
</script>
```

**问题**：
- 依赖关系不清晰
- 内联代码分散在外部引用之间
- 调试困难，缓存效率低

#### 3. **职责重复与冲突**

| 功能 | 内联脚本中 | 已有JS文件 | 问题 |
|-----|----------|-----------|------|
| 参数表单生成 | `generateParamsForm()` | `parameter_form.js` (1858行) | **重复**，应统一 |
| 边缘显示 | `EdgeDisplayTable` 类 | `edge_display.js` (425行) | **重复**，应使用edge_display.js |
| 策略管理 | 8个CRUD函数 | `strategy_manager.js` | **职责分散**，应整合 |
| 可视化加载 | `loadVisualization()` | `edge_selector_embedded.js` | **应移至edge_selector** |

---

## 优化目标

### 1. **代码组织目标**
- ✅ **消除内联 `<script>` 块**：所有JavaScript移至外部文件
- ✅ **单一职责原则**：每个JS文件职责清晰，函数不超过30行
- ✅ **清晰的依赖关系**：模块化架构，依赖顺序明确
- ✅ **消除重复代码**：统一功能实现

### 2. **性能目标**
- ✅ 支持浏览器缓存（外部JS文件）
- ✅ 减少首屏加载时间（按需加载非关键模块）
- ✅ 便于压缩和优化（独立文件）

### 3. **可维护性目标**
- ✅ 清晰的文件结构和命名
- ✅ 便于单元测试
- ✅ 便于协作开发（避免merge冲突）

---

## 详细优化方案

### Phase 1: 模块拆分与迁移

#### 1.1 创建新的JS模块

```
frontend/control/js/
├── [现有文件保持]
│   ├── edge_selector_embedded.js (863行) ✅
│   ├── edge_display.js (425行) ✅
│   ├── network_viz.js (1246行) ✅
│   ├── parameter_form.js (1858行) ⚠️ 需要重构
│   ├── timeline_visualizer.js (356行) ✅
│   ├── timeline_converter.js (189行) ✅
│   └── notification.js (257行) ✅
│
├── [新建文件 - 从内联脚本拆分]
│   ├── template_selector.js (~200行)
│   │   - fetchTemplates()
│   │   - renderTemplateCards()
│   │   - createTemplateCard()
│   │   - selectTemplate()
│   │   - showTemplateInfo()
│   │   - changeTemplate()
│   │
│   ├── wizard_controller.js (~150行)
│   │   - updateStepDisplay()
│   │   - nextStep()
│   │   - previousStep()
│   │   - validateStep()
│   │   - 步骤状态管理
│   │
│   ├── form_validator.js (~300行)
│   │   - validateParameterValue()
│   │   - validateAllParameters()
│   │   - validateEdgeSelection()
│   │   - validateStrategyInput()
│   │   - validateStrategyParameters()
│   │
│   ├── strategy_namer.js (~250行)
│   │   - setupNameChangeTracking()
│   │   - setupSuggestNameButton()
│   │   - generateStrategyName()
│   │   - fetchExistingStrategyNames()
│   │   - validateUniqueName()
│   │
│   ├── strategy_describer.js (~400行)
│   │   - StrategyDescriptionGenerator 类
│   │   - autoPopulateStrategyDescription()
│   │   - setupDescriptionChangeTracking()
│   │   - setupRegenerateDescriptionButton()
│   │   - generateVSSDescription()
│   │   - generateDHSDescription()
│   │   - generateTECDescription()
│   │
│   ├── strategy_crud.js (~350行)
│   │   - fetchStrategyInstances()
│   │   - createStrategy()
│   │   - editStrategy()
│   │   - deleteStrategy()
│   │   - prepareStrategySubmission()
│   │   - handleStrategyCreationResponse()
│   │
│   ├── templates_app.js (~200行) [主入口]
│   │   - 全局状态管理
│   │   - DOMContentLoaded 初始化
│   │   - 模块协调与事件分发
│   │   - 暴露必要的全局API
│   │
│   └── viz_loader.js (~150行)
│       - loadVisualization()
│       - 可视化加载状态管理
│       - 与 network_viz.js 集成
│
└── [重构现有文件]
    └── parameter_form.js (拆分为3个文件)
        ├── form_generator.js (~600行)
        │   - generateFormFromTemplate()
        │   - 创建各类控件的函数
        │
        ├── form_controls.js (~800行)
        │   - renderStepArrayControl()
        │   - renderDHSIntervalControl()
        │   - renderFlowIntervalControl()
        │   - 复杂控件的UI渲染
        │
        └── xml_preview.js (~400行)
            - generateXMLPreview()
            - XML格式化与预览
```

#### 1.2 模块间依赖关系

```
templates_app.js (主入口)
├── notification.js (独立，无依赖)
├── template_selector.js
│   └── notification.js
├── wizard_controller.js
│   └── form_validator.js
├── form_generator.js
│   ├── form_controls.js
│   ├── timeline_visualizer.js
│   └── timeline_converter.js
├── form_validator.js
│   └── notification.js
├── strategy_namer.js
│   └── notification.js
├── strategy_describer.js
│   └── notification.js
├── strategy_crud.js
│   ├── notification.js
│   └── form_validator.js
├── edge_selector_embedded.js
│   ├── network_viz.js
│   └── viz_loader.js
├── edge_display.js (独立)
└── xml_preview.js (独立)
```

---

### Phase 2: HTML文件优化

#### 2.1 优化后的 `<script>` 引用顺序

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>策略管理</title>

    <!-- CSS文件 (保持不变) -->
    <link rel="stylesheet" href="css/templates-base.css">
    <link rel="stylesheet" href="css/templates-layout.css">
    <link rel="stylesheet" href="css/templates-forms.css">
    <link rel="stylesheet" href="css/templates-results.css">
    <link rel="stylesheet" href="css/templates-inline-utilities.css">
</head>
<body>
    <!-- HTML内容 (保持不变) -->

    <!-- JavaScript模块 - 按依赖顺序加载 -->

    <!-- 1. 基础工具模块 (无依赖) -->
    <script src="js/notification.js"></script>
    <script src="js/timeline_converter.js"></script>
    <script src="js/timeline_visualizer.js"></script>

    <!-- 2. 核心功能模块 -->
    <script src="js/form_controls.js"></script>
    <script src="js/form_generator.js"></script>
    <script src="js/form_validator.js"></script>
    <script src="js/xml_preview.js"></script>

    <!-- 3. 业务逻辑模块 -->
    <script src="js/template_selector.js"></script>
    <script src="js/strategy_namer.js"></script>
    <script src="js/strategy_describer.js"></script>
    <script src="js/strategy_crud.js"></script>

    <!-- 4. 可视化模块 -->
    <script src="js/network_viz.js"></script>
    <script src="js/viz_loader.js"></script>
    <script src="js/edge_selector_embedded.js"></script>
    <script src="js/edge_display.js"></script>

    <!-- 5. 流程控制模块 -->
    <script src="js/wizard_controller.js"></script>

    <!-- 6. 主应用入口 (最后加载) -->
    <script src="js/templates_app.js"></script>
</body>
</html>
```

**关键改进**：
- ✅ **无内联 `<script>` 块**
- ✅ **清晰的加载顺序**：基础工具 → 核心功能 → 业务逻辑 → 可视化 → 流程控制 → 主入口
- ✅ **支持版本控制与缓存**：所有JS文件可添加 `?v=xxx` 参数

---

### Phase 3: 代码迁移规则

#### 3.1 函数迁移映射表

| 源位置 (templates.html 内联) | 目标文件 | 行号范围 | 说明 |
|---------------------------|---------|---------|------|
| `fetchTemplates()` | `template_selector.js` | L402-444 | 模板数据获取 |
| `renderTemplateCards()` | `template_selector.js` | L447-459 | 模板卡片渲染 |
| `createTemplateCard()` | `template_selector.js` | L462-495 | 创建单个卡片 |
| `selectTemplate()` | `template_selector.js` | L497-519 | 模板选择逻辑 |
| `showTemplateInfo()` | `template_selector.js` | L564-591 | 显示模板信息 |
| `changeTemplate()` | `template_selector.js` | L593-597 | 更改模板 |
| `updateStepDisplay()` | `wizard_controller.js` | L521-562 | 步骤指示器更新 |
| `nextStep()` | `wizard_controller.js` | L646-661 | 下一步验证 |
| `previousStep()` | `wizard_controller.js` | L663-669 | 上一步 |
| `validateEdgeSelection()` | `form_validator.js` | L599-644 | 边缘选择验证 |
| `generateParamsForm()` | **删除** | L671-887 | **已由parameter_form.js替代** |
| `createStringControl()` | `form_controls.js` | L1024-1068 | 字符串输入控件 |
| `createNumberControl()` | `form_controls.js` | L1070-1117 | 数字输入控件 |
| `createSelectControl()` | `form_controls.js` | L1119-1176 | 下拉选择控件 |
| `createStepArrayControl()` | `form_controls.js` | L1178-1274 | 步骤数组控件 |
| `createDHSIntervalControl()` | `form_controls.js` | L1276-1384 | DHS区间控件 |
| `createFlowIntervalControl()` | `form_controls.js` | L1386-1488 | 流量区间控件 |
| `createVehicleTypeControl()` | `form_controls.js` | L1490-1559 | 车辆类型控件 |
| `validateParameterValue()` | `form_validator.js` | L1710-1771 | 参数值验证 |
| `validateAllParameters()` | `form_validator.js` | L1811-1855 | 全部参数验证 |
| `setupNameChangeTracking()` | `strategy_namer.js` | L2641-2668 | 名称变更追踪 |
| `setupSuggestNameButton()` | `strategy_namer.js` | L2670-2771 | 智能命名按钮 |
| `fetchExistingStrategyNames()` | `strategy_namer.js` | L2556-2589 | 获取已有名称 |
| `StrategyDescriptionGenerator` | `strategy_describer.js` | L2773-3145 | 描述生成器类 |
| `autoPopulateStrategyDescription()` | `strategy_describer.js` | L3147-3205 | 自动填充描述 |
| `setupDescriptionChangeTracking()` | `strategy_describer.js` | L2982-3010 | 描述变更追踪 |
| `setupRegenerateDescriptionButton()` | `strategy_describer.js` | L3012-3079 | 重新生成按钮 |
| `fetchStrategyInstances()` | `strategy_crud.js` | L3477-3596 | 获取策略列表 |
| `createStrategy()` | `strategy_crud.js` | L3429-3475 | 创建策略 |
| `editStrategy()` | `strategy_crud.js` | L4013-4039 | 编辑策略 |
| `deleteStrategy()` | `strategy_crud.js` | L4041-4074 | 删除策略 |
| `prepareStrategySubmission()` | `strategy_crud.js` | L1857-1890 | 准备提交数据 |
| `handleStrategyCreationResponse()` | `strategy_crud.js` | L3412-3427 | 处理创建响应 |
| `EdgeDisplayTable` 类 | **迁移到** `edge_display.js` | L1892-2247 | **合并到已有文件** |
| `loadVisualization()` | `viz_loader.js` | 第二个script块 | 从第二个内联块迁移 |

#### 3.2 全局状态管理

**当前问题**：全局变量散落在内联脚本中

```javascript
// templates.html 第一个 <script> (L382-387)
let currentStep = 1;
let templates = [];
let selectedTemplate = null;
let selectedEdges = [];
let strategyInstances = [];
let currentPage = 1;
let pageSize = 20;
let totalCount = 0;
let allStrategyInstances = [];
```

**优化方案**：集中管理在 `templates_app.js`

```javascript
// templates_app.js
const TemplatesApp = {
    state: {
        currentStep: 1,
        templates: [],
        selectedTemplate: null,
        selectedEdges: [],
        strategyInstances: {
            all: [],
            currentPage: 1,
            pageSize: 20,
            totalCount: 0
        }
    },

    init() {
        console.log('=== Templates App Initializing ===');
        this.loadModules();
        this.bindEvents();
        this.fetchInitialData();
    },

    loadModules() {
        // 检查所有依赖模块是否加载
        const required = [
            'Notification',
            'TemplateSelector',
            'WizardController',
            'FormValidator',
            'StrategyNamer',
            'StrategyDescriber',
            'StrategyCRUD',
            'EdgeSelector',
            'EdgeDisplayTable',
            'networkViz'
        ];

        required.forEach(module => {
            if (typeof window[module] === 'undefined') {
                console.error(`❌ Module ${module} not loaded!`);
            } else {
                console.log(`✅ Module ${module} loaded`);
            }
        });
    },

    bindEvents() {
        // 全局事件监听
        document.addEventListener('template:selected', (e) => {
            this.state.selectedTemplate = e.detail;
        });

        document.addEventListener('edges:selected', (e) => {
            this.state.selectedEdges = e.detail;
        });

        // ... 更多事件
    },

    fetchInitialData() {
        TemplateSelector.fetchTemplates();
        StrategyCRUD.fetchStrategyInstances();
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    TemplatesApp.init();
});
```

---

### Phase 4: 事件驱动架构

#### 4.1 模块间通信机制

**当前问题**：函数直接调用，耦合度高

```javascript
// 当前方式 (紧耦合)
function selectTemplate(template) {
    selectedTemplate = template;
    updateStepDisplay();  // 直接调用
    showTemplateInfo(template);  // 直接调用
    // ...
}
```

**优化方案**：使用自定义事件解耦

```javascript
// template_selector.js
function selectTemplate(template) {
    TemplatesApp.state.selectedTemplate = template;

    // 发布事件
    document.dispatchEvent(new CustomEvent('template:selected', {
        detail: template
    }));
}

// wizard_controller.js
document.addEventListener('template:selected', (e) => {
    updateStepDisplay();
});

// strategy_describer.js
document.addEventListener('template:selected', (e) => {
    const template = e.detail;
    showTemplateInfo(template);
});
```

#### 4.2 标准事件清单

| 事件名 | 触发时机 | 携带数据 | 监听模块 |
|-------|---------|---------|---------|
| `template:selected` | 选择模板 | `template` 对象 | wizard_controller, strategy_describer |
| `template:changed` | 更改模板 | 无 | wizard_controller |
| `edges:selected` | 选择边缘 | `edges` 数组 | edge_display, form_validator |
| `edges:updated` | 更新边缘列表 | `edges` 数组 | edge_display |
| `step:changed` | 步骤切换 | `{current, previous}` | wizard_controller, form_validator |
| `form:validated` | 表单验证完成 | `{valid, errors}` | wizard_controller, strategy_crud |
| `strategy:created` | 创建策略成功 | `strategy` 对象 | strategy_crud, notification |
| `strategy:deleted` | 删除策略成功 | `strategy_id` | strategy_crud, notification |
| `viz:loaded` | 可视化加载完成 | 无 | viz_loader |

---

## 实施计划

### 优先级 P0 (核心重构)

**目标**：消除内联脚本，建立模块化架构

#### Step 1: 创建主入口文件 (1小时)
- [ ] 创建 `templates_app.js`
- [ ] 迁移全局状态管理
- [ ] 实现模块加载检查
- [ ] 实现事件总线机制

#### Step 2: 拆分模板选择器 (2小时)
- [ ] 创建 `template_selector.js`
- [ ] 迁移 6个模板相关函数
- [ ] 发布 `template:selected` 事件
- [ ] 测试模板选择流程

#### Step 3: 拆分步骤控制器 (1.5小时)
- [ ] 创建 `wizard_controller.js`
- [ ] 迁移 4个步骤控制函数
- [ ] 监听 `template:selected` 事件
- [ ] 测试步骤切换逻辑

#### Step 4: 拆分表单验证器 (2小时)
- [ ] 创建 `form_validator.js`
- [ ] 迁移 5个验证函数
- [ ] 发布 `form:validated` 事件
- [ ] 编写验证单元测试

#### Step 5: 拆分策略CRUD (3小时)
- [ ] 创建 `strategy_crud.js`
- [ ] 迁移 8个CRUD函数
- [ ] 集成 `notification.js`
- [ ] 测试完整CRUD流程

#### Step 6: 更新HTML引用 (1小时)
- [ ] 删除两个内联 `<script>` 块
- [ ] 按依赖顺序添加外部JS引用
- [ ] 测试页面加载与功能完整性

**P0 总耗时估计：10.5小时**

---

### 优先级 P1 (细化重构)

#### Step 7: 拆分策略命名器 (2小时)
- [ ] 创建 `strategy_namer.js`
- [ ] 迁移名称生成与验证逻辑
- [ ] 测试智能命名功能

#### Step 8: 拆分策略描述生成器 (3小时)
- [ ] 创建 `strategy_describer.js`
- [ ] 迁移 `StrategyDescriptionGenerator` 类
- [ ] 测试三种策略类型描述生成

#### Step 9: 拆分可视化加载器 (2小时)
- [ ] 创建 `viz_loader.js`
- [ ] 从第二个内联块迁移 `loadVisualization()`
- [ ] 优化可视化加载状态管理

#### Step 10: 整合边缘显示组件 (2小时)
- [ ] 将内联 `EdgeDisplayTable` 类迁移到 `edge_display.js`
- [ ] 删除重复代码
- [ ] 测试边缘显示与统计功能

**P1 总耗时估计：9小时**

---

### 优先级 P2 (深度优化)

#### Step 11: 重构 parameter_form.js (5小时)
- [ ] 拆分为 `form_generator.js`
- [ ] 拆分为 `form_controls.js`
- [ ] 拆分为 `xml_preview.js`
- [ ] 更新所有引用
- [ ] 测试参数表单生成

#### Step 12: 函数长度优化 (3小时)
- [ ] 识别所有 >30行 的函数
- [ ] 按SRP拆分为小函数
- [ ] 编写单元测试

#### Step 13: 编写E2E测试 (4小时)
- [ ] Playwright测试：模板选择流程
- [ ] Playwright测试：边缘选择流程
- [ ] Playwright测试：参数配置流程
- [ ] Playwright测试：策略创建完整流程

**P2 总耗时估计：12小时**

---

## 验收标准

### 代码质量标准
- ✅ 无内联 `<script>` 块
- ✅ 所有JS文件 <1000 行
- ✅ 所有函数 <30 行
- ✅ 所有函数有明确的单一职责
- ✅ 模块间通过事件通信，低耦合

### 功能完整性标准
- ✅ 模板选择流程正常
- ✅ 边缘选择与显示正常
- ✅ 参数表单生成与验证正常
- ✅ 策略创建/编辑/删除正常
- ✅ 可视化加载与交互正常

### 性能标准
- ✅ 首屏加载时间 <2秒
- ✅ 模板切换响应 <200ms
- ✅ 表单验证响应 <100ms
- ✅ 可视化渲染 <1秒 (500边缘内)

### 测试覆盖率标准
- ✅ 单元测试覆盖率 >80%
- ✅ E2E测试覆盖关键流程 100%

---

## 风险与缓解

### 风险1: 重构期间功能中断
**缓解措施**：
- 使用Git分支开发 (`feature/templates-refactor`)
- 保持旧版本可用（不删除内联脚本直到新版本验证完成）
- 逐步迁移，每个模块独立测试

### 风险2: 全局变量冲突
**缓解措施**：
- 使用命名空间（如 `TemplatesApp`, `TemplateSelector`）
- 避免污染全局作用域
- 使用模块模式封装私有变量

### 风险3: 事件监听器内存泄漏
**缓解措施**：
- 使用命名事件（不用匿名函数）
- 在适当时机移除事件监听器
- 使用 `once: true` 选项（如果适用）

---

## 后续优化建议

### 1. 引入模块打包工具
- 使用 **Webpack** 或 **Rollup** 打包JS模块
- 代码分割与按需加载
- Tree-shaking 去除未使用代码

### 2. 迁移到TypeScript
- 类型安全
- 更好的IDE支持
- 编译时错误检测

### 3. 引入状态管理库
- 考虑使用轻量级状态管理（如 **Zustand** 或 **Pinia**）
- 集中管理应用状态
- 时间旅行调试

### 4. 组件化改造
- 考虑使用 **Vue 3** 或 **React** 组件化
- 更好的代码复用
- 声明式UI

---

## 总结

### 当前状态
- **templates.html**: 4279行，包含3896行内联JavaScript
- **职责混杂**：83个函数分散在一个文件中
- **维护困难**：调试、测试、协作困难

### 优化后状态
- **templates.html**: ~400行，仅包含HTML结构
- **17个独立JS模块**：职责清晰，易于维护
- **事件驱动架构**：低耦合，高内聚
- **完整测试覆盖**：单元测试 + E2E测试

### 预期收益
- ⚡ **性能提升**：浏览器缓存，加载速度提升30%+
- 🛠️ **开发效率**：模块独立开发，协作无冲突
- 🐛 **调试便利**：问题定位快速，错误堆栈清晰
- ✅ **代码质量**：符合SRP，可测试性强

---

## 附录：快速参考

### 模块加载顺序速查表
```
1. notification.js (独立)
2. timeline_converter.js (独立)
3. timeline_visualizer.js (依赖 timeline_converter)
4. form_controls.js (依赖 timeline_visualizer)
5. form_generator.js (依赖 form_controls)
6. form_validator.js (依赖 notification)
7. xml_preview.js (独立)
8. template_selector.js (依赖 notification)
9. strategy_namer.js (依赖 notification)
10. strategy_describer.js (依赖 notification)
11. strategy_crud.js (依赖 notification, form_validator)
12. network_viz.js (独立)
13. viz_loader.js (依赖 network_viz)
14. edge_selector_embedded.js (依赖 network_viz, viz_loader)
15. edge_display.js (独立)
16. wizard_controller.js (依赖 form_validator)
17. templates_app.js (依赖所有模块)
```

### 文件大小估算
| 文件 | 预估行数 | 函数数量 |
|-----|---------|---------|
| templates_app.js | 200 | 8 |
| template_selector.js | 200 | 6 |
| wizard_controller.js | 150 | 4 |
| form_validator.js | 300 | 5 |
| strategy_namer.js | 250 | 5 |
| strategy_describer.js | 400 | 8 |
| strategy_crud.js | 350 | 8 |
| viz_loader.js | 150 | 3 |
| form_generator.js | 600 | 12 |
| form_controls.js | 800 | 15 |
| xml_preview.js | 400 | 5 |
| **总计** | **3800** | **79** |

*注：总行数略多于原3698行，因为增加了模块导出/导入代码和注释*

---

**文档版本**: v1.0
**创建日期**: 2025-10-30
**作者**: Claude Code
**状态**: 待审核
