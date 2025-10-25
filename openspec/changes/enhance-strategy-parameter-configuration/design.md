# 设计：增强策略参数配置

## 概述

本文档详细说明了增强策略参数配置页面（第3步）的技术设计，以解决当前的可用性问题并支持成功创建策略实例。

## 架构

### 组件结构

```
frontend/control/
├── templates.html                    # 主页面（增强第3步）
├── js/
│   ├── strategy_manager.js          # 核心策略CRUD（增强）
│   ├── parameter_form_builder.js    # 新增：动态表单生成
│   ├── edge_display_table.js        # 新增：路段信息表格
│   ├── name_generator.js            # 新增：自动命名逻辑
│   └── description_generator.js     # 新增：自动描述逻辑
└── css/
    └── strategy_config.css           # 新增：第3步专用样式
```

### 数据流

```
用户输入（第3步）
    ↓
参数表单构建器
    ↓ （验证）
参数验证器
    ↓ （如果有效）
名称生成器 + 描述生成器
    ↓
XML预览生成器
    ↓ （用户确认）
策略管理器（保存）
    ↓
POST /api/v1/control/strategy-instances
    ↓
后端验证 + 存储
```

## 组件设计

### 1. 参数表单构建器 (`parameter_form_builder.js`)

**目的**：基于模板参数schema动态生成表单输入

**核心方法**：

```javascript
class ParameterFormBuilder {
    constructor(templateSchema) {
        this.schema = templateSchema;
        this.formContainer = null;
        this.validators = new Map();
    }

    /**
     * 构建完整的参数表单
     * @param {HTMLElement} container - 表单容器元素
     * @param {Object} existingValues - 编辑模式的预填值
     */
    buildForm(container, existingValues = {}) {
        // 按类别分组参数
        const grouped = this.groupParameters(this.schema.parameters_schema);

        // 渲染每个组
        for (const [category, params] of Object.entries(grouped)) {
            this.renderGroup(container, category, params, existingValues);
        }

        // 附加事件监听器
        this.attachValidators();
    }

    /**
     * 按类别分组参数（位置、时间、控制、其他）
     */
    groupParameters(parameters) {
        const categories = {
            location: [], // affected_edges, entrance_edges等
            time: [],     // time_intervals, intervals等
            control: [],  // speed_steps, allowed_vehicle_types等
            other: []
        };

        parameters.forEach(param => {
            const category = this.categorizeParameter(param.parameter_name);
            categories[category].push(param);
        });

        return categories;
    }

    /**
     * 基于参数类型创建输入组件
     */
    createInputComponent(paramSchema, existingValue) {
        const type = paramSchema.parameter_type;

        switch(type) {
            case 'array':
                return this.createArrayInput(paramSchema, existingValue);
            case 'time_range_array':
                return this.createTimeIntervalInput(paramSchema, existingValue);
            case 'step_array':
                return this.createStepArrayInput(paramSchema, existingValue);
            case 'integer':
            case 'float':
                return this.createNumberInput(paramSchema, existingValue);
            case 'string':
                return this.createTextInput(paramSchema, existingValue);
            case 'boolean':
                return this.createBooleanInput(paramSchema, existingValue);
            case 'enum':
                return this.createEnumInput(paramSchema, existingValue);
            default:
                return this.createTextInput(paramSchema, existingValue);
        }
    }

    /**
     * 创建带智能占位符的数组输入
     */
    createArrayInput(paramSchema, existingValue) {
        const textarea = document.createElement('textarea');
        textarea.id = `param-${paramSchema.parameter_name}`;
        textarea.name = paramSchema.parameter_name;
        textarea.rows = 6;
        textarea.className = 'array-input';

        // 基于参数名称和默认值设置占位符
        textarea.placeholder = this.generateArrayPlaceholder(paramSchema);

        // 预填充值
        if (existingValue && Array.isArray(existingValue)) {
            if (existingValue.length > 0 && Array.isArray(existingValue[0])) {
                // 嵌套数组 - 使用JSON
                textarea.value = JSON.stringify(existingValue, null, 2);
            } else {
                // 简单数组 - 换行分隔
                textarea.value = existingValue.join('\n');
            }
        }

        // 附加验证器
        textarea.addEventListener('blur', () => this.validateArrayField(paramSchema, textarea));

        return textarea;
    }

    /**
     * 为数组输入生成智能占位符
     */
    generateArrayPlaceholder(paramSchema) {
        const name = paramSchema.parameter_name.toLowerCase();

        // 时间相关参数
        if (name.includes('time') || name.includes('interval')) {
            return `时段格式示例:\n[\n  [7, 9],\n  [17, 19]\n]\n\n每行一个时间段 [开始小时, 结束小时]`;
        }

        // 速度相关参数
        if (name.includes('speed')) {
            return `限速值示例(每行一个):\n80\n60\n40\n\n或JSON格式:[80, 60, 40]`;
        }

        // 车型参数
        if (name.includes('vehicle') || name.includes('type')) {
            return `车型列表示例:\npassenger\ntruck\nbus\n\n或用逗号分隔:passenger, truck, bus`;
        }

        // Edge相关参数
        if (name.includes('edge') || name.includes('segment')) {
            return `路段ID列表示例:\n-5880\n-5881\n-5882\n\n或用逗号分隔:-5880, -5881, -5882`;
        }

        // 入口参数
        if (name.includes('entrance')) {
            return `入口列表示例:\nentrance_1\nentrance_2\n\n或用逗号分隔:entrance_1, entrance_2`;
        }

        // 通用后备
        return `多个值,每行一个:\nvalue1\nvalue2\nvalue3\n\n或JSON格式:["value1", "value2", "value3"]`;
    }

    /**
     * 在失焦时验证数组字段
     */
    validateArrayField(paramSchema, textarea) {
        const value = textarea.value.trim();
        const errorEl = document.getElementById(`error-${paramSchema.parameter_name}`);

        if (!value && paramSchema.required) {
            this.showError(errorEl, '此字段为必填项');
            return false;
        }

        if (!value) {
            this.clearError(errorEl);
            return true;
        }

        try {
            let parsed;

            // 首先尝试JSON解析
            if (value.startsWith('[')) {
                parsed = JSON.parse(value);
                if (!Array.isArray(parsed)) {
                    this.showError(errorEl, 'JSON格式需要是数组');
                    return false;
                }
            } else {
                // 解析为换行/逗号分隔
                parsed = value.split(/[,\n]/).map(s => s.trim()).filter(s => s);
            }

            // 检查最小项数
            if (paramSchema.min_items && parsed.length < paramSchema.min_items) {
                this.showError(errorEl, `至少需要 ${paramSchema.min_items} 个项目,当前: ${parsed.length}`);
                return false;
            }

            this.clearError(errorEl);
            return true;

        } catch (e) {
            this.showError(errorEl, `JSON格式不正确: ${e.message}`);
            return false;
        }
    }
}
```

### 2. 路段展示表格 (`edge_display_table.js`)

**目的**：显示已选路段的完整信息以供验证

**核心方法**：

```javascript
class EdgeDisplayTable {
    constructor(containerEl, strategyType) {
        this.container = containerEl;
        this.strategyType = strategyType;
        this.edges = [];
    }

    /**
     * 加载并显示路段
     * @param {Array<string>} edgeIds - 要显示的路段ID
     */
    async loadEdges(edgeIds) {
        // 从API获取完整的路段信息
        const response = await fetch('/api/v1/control/edges/batch-info', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({edge_ids: edgeIds})
        });

        this.edges = await response.json();
        this.render();
        this.checkValidation();
    }

    /**
     * 渲染摘要部分
     */
    renderSummary() {
        const summary = document.createElement('div');
        summary.className = 'edge-summary';

        const totalLength = this.edges.reduce((sum, e) => sum + e.length_m, 0) / 1000;
        const routes = [...new Set(this.edges.map(e => e.route_code))];
        const laneRange = {
            min: Math.min(...this.edges.map(e => e.lane_count)),
            max: Math.max(...this.edges.map(e => e.lane_count))
        };

        summary.innerHTML = `
            <div class="summary-item">
                <span class="summary-label">已选择</span>
                <span class="summary-value">${this.edges.length} 个路段</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">总长度</span>
                <span class="summary-value">${totalLength.toFixed(2)} km</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">覆盖路线</span>
                <span class="summary-value">${routes.join(', ')}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">车道数范围</span>
                <span class="summary-value">${laneRange.min}-${laneRange.max} 车道</span>
            </div>
        `;

        return summary;
    }

    /**
     * 检查路段是否形成连续路径
     * @returns {Array<string>} 不连续描述列表
     */
    checkEdgeContinuity() {
        const gaps = [];
        const sorted = [...this.edges].sort((a, b) => a.start_stake - b.start_stake);

        for (let i = 0; i < sorted.length - 1; i++) {
            const current = sorted[i];
            const next = sorted[i + 1];

            if (current.end_stake < next.start_stake) {
                const gapSize = next.start_stake - current.end_stake;
                gaps.push(`K${(current.end_stake/1000).toFixed(1)} 到 K${(next.start_stake/1000).toFixed(1)} 之间存在 ${gapSize}m 间隙`);
            }
        }

        return gaps;
    }

    /**
     * 检查验证并渲染警告
     */
    checkValidation() {
        this.validationIssues = [];

        // DHS特定验证
        if (this.strategyType === 'DHS') {
            // 检查车道数 >= 4
            const invalidLanes = this.edges.filter(e => e.lane_count < 4);
            if (invalidLanes.length > 0) {
                this.validationIssues.push({
                    type: 'error',
                    message: 'DHS策略要求车道数≥4,以下路段不符合:',
                    details: invalidLanes.map(e => `${e.edge_id} (${e.lane_count}车道)`)
                });
            }

            // 检查路段连续性
            const discontinuities = this.checkEdgeContinuity();
            if (discontinuities.length > 0) {
                this.validationIssues.push({
                    type: 'warning',
                    message: '警告:所选路段不连续,DHS策略可能效果降低',
                    details: discontinuities
                });
            }
        }
    }
}
```

### 3. 名称生成器 (`name_generator.js`)

**目的**：基于模板规则和参数生成策略名称

**核心方法**：

```javascript
class StrategyNameGenerator {
    /**
     * 基于类型和参数生成策略名称
     * @param {string} strategyType - VSS, DHS或TEC
     * @param {Object} parameters - 策略参数
     * @param {Array<Object>} edges - 已选路段信息
     * @returns {Promise<string>} 生成的名称
     */
    static async generate(strategyType, parameters, edges) {
        switch(strategyType) {
            case 'VSS':
                return this.generateVSSName(parameters, edges);
            case 'DHS':
                return this.generateDHSName(parameters, edges);
            case 'TEC':
                return this.generateTECName(parameters, edges);
            default:
                return `${strategyType}策略_${Date.now()}`;
        }
    }

    /**
     * 生成VSS策略名称
     * 格式："{路线} {路段} 限速{速度}km/h ({时段})"
     */
    static generateVSSName(params, edges) {
        const location = this.extractLocation(edges);
        const speed = params.speed_limit || (params.speed_steps && params.speed_steps[1]?.speed) || '变速';
        const time = this.extractTimePeriod(params.time_intervals || [[0, 24]]);

        return `${location.route} ${location.section} 限速${speed}km/h (${time})`;
    }

    /**
     * 生成DHS策略名称
     * 格式："{路线} {路段} 应急车道开放 ({时段})"
     */
    static generateDHSName(params, edges) {
        const location = this.extractLocation(edges);
        const time = this.extractTimePeriod(params.intervals?.map(i => [i.begin/3600, i.end/3600]) || [[0, 24]]);

        return `${location.route} ${location.section} 应急车道开放 (${time})`;
    }

    /**
     * 提取时段描述
     */
    static extractTimePeriod(intervals) {
        if (!intervals || intervals.length === 0) {
            return '定时管控';
        }

        const flattened = intervals[0] instanceof Array ? intervals : [intervals];

        // 检查常见模式
        const isMorningPeak = flattened.some(([start, end]) => start >= 7 && end <= 10);
        const isEveningPeak = flattened.some(([start, end]) => start >= 17 && end <= 20);
        const isFullDay = flattened.some(([start, end]) => start === 0 && end === 24);

        if (isFullDay) return '全天';
        if (isMorningPeak && isEveningPeak) return '早晚高峰';
        if (isMorningPeak) return '早高峰';
        if (isEveningPeak) return '晚高峰';

        return '定时管控';
    }

    /**
     * 确保名称唯一性
     * @param {string} baseName - 生成的基础名称
     * @returns {Promise<string>} 唯一名称
     */
    static async ensureUnique(baseName) {
        // 检查现有策略
        const response = await fetch(`/api/v1/control/strategy-instances?name=${encodeURIComponent(baseName)}`);
        const existing = await response.json();

        if (existing.strategies.length === 0) {
            return baseName;
        }

        // 追加计数器
        let counter = 2;
        while (true) {
            const candidateName = `${baseName} (${counter})`;
            const checkResponse = await fetch(`/api/v1/control/strategy-instances?name=${encodeURIComponent(candidateName)}`);
            const checkExisting = await checkResponse.json();

            if (checkExisting.strategies.length === 0) {
                return candidateName;
            }
            counter++;
        }
    }
}
```

### 4. 描述生成器 (`description_generator.js`)

与名称生成器结构类似，但使用模板元数据和参数值创建多行格式化描述。

**示例输出**：

```
可变限速策略 - 中等控制

管控位置:
- 路线: G4202 (成都绕城高速)
- 路段: K10-K15 (共15个edge,总长8.5km)
- 车道数: 3-4车道

管控参数:
- 限速值: 80 km/h
- 管控时段: 07:00-09:00, 17:00-19:00 (早晚高峰)
- 适用车型: 所有车辆

策略目的: 通过动态调整限速来管理高峰时段交通流,缓解拥堵。

生成元素: 1个 variableSpeedSign (SUMO XML)
```

## 数据库Schema

无需schema更改。使用现有的 `dim.sim_network_edges` 表获取路段信息。

## API端点

### 现有端点（无更改）

- `POST /api/v1/control/strategy-instances` - 创建策略
- `PUT /api/v1/control/strategy-instances/{id}` - 更新策略
- `GET /api/v1/control/strategy-instances` - 列出策略
- `GET /api/v1/control/templates/{id}` - 获取模板schema

### 新端点（可选增强）

```python
# 批量路段信息检索API端点
@router.post("/api/v1/control/edges/batch-info")
async def get_batch_edge_info(request: BatchEdgeInfoRequest):
    """
    获取多个路段的详细信息

    请求:
        {
            "edge_ids": ["-5880", "-5881", "edge_k10_001"]
        }

    响应:
        [
            {
                "edge_id": "-5880",
                "route_code": "G4202",
                "section_code": "K10-K15",
                "start_stake": 10200,
                "end_stake": 10800,
                "length_m": 600,
                "lane_count": 4,
                "direction": "clockwise",
                "node_type": "normal",
                "from_junction_id": "j_123",
                "from_junction_name": "锦江收费站入口",
                "demonstration_segment": "成都示范段"
            },
            ...
        ]
    """
    pass

# Edge ID验证API端点
@router.post("/api/v1/control/edges/validate")
async def validate_edge_ids(request: EdgeValidationRequest):
    """
    验证edge ID是否存在于网络中

    请求:
        {
            "edge_ids": ["-5880", "invalid_edge"]
        }

    响应:
        {
            "valid": ["-5880"],
            "invalid": ["invalid_edge"]
        }
    """
    pass
```

## UI/UX规范

### 第3步布局

```
┌─────────────────────────────────────────────────────────────┐
│  第3步：配置参数                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  已选路段 (15个)  总长度: 8.5km  [导出列表]          │  │
│  │                                                       │  │
│  │  ⚠️ 警告: 所选路段不连续... [查看详情]                │  │
│  │                                                       │  │
│  │  [路段表格 - 10列，可滚动]                            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  📍 管控位置                           [收起 ▲]      │  │
│  │  ────────────────────────────────────────────        │  │
│  │  (位置参数显示在这里)                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  ⏰ 时间配置                           [收起 ▲]      │  │
│  │  ────────────────────────────────────────────        │  │
│  │  (时间参数显示在这里)                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  🚗 管控参数                           [收起 ▲]      │  │
│  │  ────────────────────────────────────────────        │  │
│  │  (控制参数显示在这里)                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  策略名称 *              [建议名称 🔄]               │  │
│  │  [G4202 K10-K15 限速80km/h (早晚高峰)            ]  │  │
│  │                                                       │  │
│  │  策略描述 *              [重新生成 🔄]               │  │
│  │  [                                                 ]  │  │
│  │  [ 自动生成的描述...                               ]  │  │
│  │  [                                                 ]  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  SUMO XML 预览                         [复制XML ▼]   │  │
│  │  ────────────────────────────────────────────        │  │
│  │  <variableSpeedSign id="..." edges="...">            │  │
│  │    <step time="25200" speed="22.22"/>               │  │
│  │  </variableSpeedSign>                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│                        [上一步]  [保存策略]                │
└─────────────────────────────────────────────────────────────┘
```

### 配色方案

- **验证错误**：`#e74c3c`（红色）
- **验证警告**：`#f39c12`（橙色）
- **成功/有效**：`#27ae60`（绿色）
- **信息/提示**：`#3498db`（蓝色）
- **组标题**：`#2c3e50`（深灰色）

## 测试策略

### 单元测试

- ParameterFormBuilder：测试每种输入类型生成
- EdgeDisplayTable：测试连续性检查、验证逻辑
- NameGenerator：测试每种策略类型的名称生成
- DescriptionGenerator：测试描述模板

### 集成测试

- 使用真实模板schema的完整第3步工作流
- 路段表格显示和验证
- 名称/描述自动生成和覆盖
- 参数更改时的XML预览更新

### E2E测试（Playwright）

```javascript
test('创建带自动生成名称和描述的VSS策略', async ({ page }) => {
    await page.goto('/control/templates.html');

    // 选择VSS模板
    await page.click('text=VSS中等控制');

    // 选择路段（第2步）
    await page.click('text=G4202');
    await page.click('text=K10-K15');
    await page.click('.apply-filter-btn');
    await page.click('.select-all-edges');

    // 进入第3步
    await page.click('#step2-next');

    // 验证路段表格已显示
    await expect(page.locator('.edge-table')).toBeVisible();
    await expect(page.locator('.edge-table tbody tr')).toHaveCount(15);

    // 填写参数
    await page.fill('#param-speed_limit', '80');
    await page.fill('#param-time_intervals', '[[7, 9], [17, 19]]');

    // 验证自动生成的名称
    await expect(page.locator('#param-strategy_name')).toHaveValue(/G4202.*限速80km\/h/);

    // 验证自动生成的描述
    await expect(page.locator('#param-strategy_description')).toContainText('可变限速策略');
    await expect(page.locator('#param-strategy_description')).toContainText('G4202');
    await expect(page.locator('#param-strategy_description')).toContainText('80 km/h');

    // 保存策略
    await page.click('.save-strategy-btn');

    // 验证成功
    await expect(page.locator('.success-message')).toContainText('策略创建成功');
});
```

## 迁移路径

1. **阶段1**：部署增强的参数表单构建器（向后兼容）
2. **阶段2**：添加路段展示表格
3. **阶段3**：实现自动生成功能（名称、描述）
4. **阶段4**：移除人员字段（如果存在）
5. **阶段5**：添加XML预览增强

## 性能考虑

- **路段表格渲染**：对>50个路段使用虚拟滚动
- **XML预览更新**：对参数更改进行防抖（500ms延迟）
- **名称生成**：缓存生成的名称以避免重复API调用
- **路段信息加载**：批量API请求而非单个查询

## 安全考虑

- **XSS防护**：在HTML渲染前清理所有用户输入
- **CSRF保护**：所有表单提交使用CSRF令牌
- **输入验证**：除客户端验证外还需服务端验证
- **速率限制**：限制名称唯一性检查API调用以防滥用
