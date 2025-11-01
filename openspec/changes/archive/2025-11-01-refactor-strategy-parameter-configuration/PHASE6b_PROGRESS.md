# Phase 6b 进度 - 车型配置分离

**完成日期**: 2025-11-01
**完成任务**: 6b.1, 6b.2
**状态**: ✅ 进行中

## 已完成的任务

### Task 6b.1: 从 DHS/TEC 表中移除车型列 ✅

**修改文件**: `frontend/control/js/parameter_form.js`

#### 修改内容

1. **renderDHSIntervalControl() 函数**
   - 移除表格头中的 "允许车型" 列（原 1231-1239 行）
   - 列表结构从 4 列改为 3 列：开始时间 | 结束时间 | 状态 | 操作

2. **addDHSIntervalRow() 函数**
   - 移除函数参数中的 `allowedVehicles` 参数
   - 删除了约 40 行的车型多选框创建代码（原 1327-1355 行）
   - 简化后函数从 77 行降至 50 行，符合单一职责原则
   - 更新函数签名文档说明

3. **调用位置更新**
   - 行 1252: `addDHSIntervalRow()` 调用移除 `allowedVehicles` 参数
   - 行 1268: "添加行" 按钮回调移除 `allowedVehicles` 参数

4. **form 提交逻辑**
   - 添加 `dhs_interval_array` 类型的提取逻辑（行 2415-2430）
   - 提取数据结构：`{ begin_hours, end_hours, status }` (无车型)
   - 添加 `tec_interval_array` 类型的提取逻辑（行 2442-2456）
   - 提取数据结构：`{ begin_hours, end_hours }` (无车型)

**验证**: ✅ DHS 表格正确渲染，3 列数据 + 1 操作列

---

### Task 6b.2: 创建全局车型配置区域 ✅

**修改文件**:
- `frontend/control/js/parameter_form.js`
- `frontend/control/css/templates-forms.css`

#### 新增函数

**renderGlobalVehicleTypeControl(vehicleTypeParams, template)**

功能：为策略级别的车型配置生成全局控件

特性：
- 动态标签：根据参数类型显示不同标签
  - `allowed_vehicle_types` → "允许的车型"
  - `disallow_vehicle_types` / `banned_vehicle_types` → "禁止的车型"
  - `applicable_vehicle_types` → "适用车型"

- 动态提示文本：
  - "允许" 模式：仅选中的车型可使用此策略
  - "禁止" 模式：选中的车型禁止使用此策略

- 复选框网格布局：
  - 自适应列数：每列最小宽度 120px
  - 支持 5 种基础车型：小客车、公交车、货车、应急车、执法车
  - 每个复选框有 `enum-checkbox` 类，支持 form 提交逻辑

#### CSS 样式

新增 `.vehicle-type-config-global` 及相关类：

```css
.vehicle-type-config-global {
    background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 15px;
    margin: 20px 0;
}

.vehicle-checkboxes {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
    margin-bottom: 12px;
    padding: 10px;
}

.checkbox-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;
}

.form-hint {
    background-color: #f0f7ff;
    border-left: 3px solid #0066cc;
}
```

特点：
- 浅灰色背景，与其他参数区分
- 高度可视化分离，提升 UX
- 响应式网格布局
- 蓝色提示框提高可读性

#### 函数导出

已在 `window` 对象上导出 `renderGlobalVehicleTypeControl`，供 HTML 模板调用。

---

## 实现细节

### 车型参数识别

系统识别以下参数名称作为车型配置：
- `allowed_vehicle_types` - 允许的车型
- `disallow_vehicle_types` - 禁止的车型
- `banned_vehicle_types` - 被禁止的车型
- `applicable_vehicle_types` - 适用车型

### Form 提交逻辑

已更新 `extractFormParameters()` 函数：
1. 识别 `vehicle-type-config-global` 容器中的 `.enum-checkbox:checked` 元素
2. 提取选中的车型值数组
3. 映射到对应的参数名称

### 架构设计

```
策略参数配置 (Step 3)
├── 策略名称/描述
├── [参数表单]
│   ├── VSS 参数
│   ├── DHS 时间区间表 (无车型)
│   ├── TEC 时间区间表 (无车型)
│   └── ...其他参数
└── [全局车型配置] ← 新增
    └── 车型复选框网格 (允许/禁止)
```

---

## E2E 测试结果

✅ **所有 5 个 E2E 测试通过** (36.1s)

- VSS策略完整工作流 (4.7s)
- DHS策略完整工作流 (4.4s)
- TEC策略完整工作流 (4.8s)
- 参数验证测试 (4.7s)
- UI功能测试 (5.7s)

---

## 下一步计划

### Task 6b.3: 实现动态标签/提示 (已完成)
- ✅ 标签根据参数类型动态显示
- ✅ 提示文本根据 allowed/disallow 模式显示

### Task 6b.4: 更新表单提交逻辑 (已完成)
- ✅ DHS interval array 提取逻辑
- ✅ TEC interval array 提取逻辑
- ✅ 车型复选框提取（已有，无需修改）

### 后续 Phase

- **Phase 7**: 路段来源统一
  - 隐藏 Step 3 中的 `affected_edges` 输入框
  - 显示 Step 2 路段只读列表

- **Phase 8**: 验证和提示改进
  - 时间顺序验证
  - 数值范围验证
  - 删除确认对话框

---

## 代码质量指标

| 指标 | 改进 |
|------|------|
| 函数行数 | `addDHSIntervalRow` 77 → 50 行 (-35%) |
| 代码复用性 | 新增 `renderGlobalVehicleTypeControl()` 支持 4 种车型参数 |
| CSS 分离 | 新增独立的全局车型配置样式 |
| 类名规范 | 统一使用 `enum-checkbox` 类，便于 form 提交 |
| 文档完整性 | 函数注释、参数说明齐全 |

---

## 验证清单

- [x] DHS 表格无车型列
- [x] TEC 表格无车型列
- [x] 全局车型配置区域存在
- [x] 车型标签动态变化
- [x] 车型提示动态变化
- [x] Form 提交逻辑正确
- [x] E2E 测试全部通过
- [x] 代码符合单一职责原则
- [x] CSS 样式符合项目规范
- [x] 函数导出完整

