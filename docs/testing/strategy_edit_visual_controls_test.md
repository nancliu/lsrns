# 策略实例编辑表单视觉控件测试指南

## 问题描述
编辑策略实例时，时间选择器（step_array）和车型多选框（enum_array）没有正确显示已保存的数据。

## 根本原因

### 问题1: API请求参数错误 (422错误)
- **现象**: 控制台显示 `GET /api/v1/control/strategy-instances/?page=1&page_size=1000 422`
- **原因**: API限制 `page_size` 最大为100，但前端请求1000
- **修复**: 改用分页循环获取，每次最多100条

### 问题2: 视觉控件未填充数据
- **现象**: 编辑表单中的时间-速度步骤、车型复选框为空
- **原因**:
  1. `populateEditForm()` 只处理简单HTML元素，未处理视觉控件
  2. `generateEditForm()` 使用 `param.allowed_values`，但模板使用 `param.enum_values`

## 修复内容

### 文件1: `frontend/control/templates.html`

#### 修复点1: API分页查询 (Lines 2125-2168)
```javascript
// 修复前
const response = await fetch('/api/v1/control/strategy-instances/?page=1&page_size=1000');

// 修复后
let allNames = [];
let page = 1;
let hasMore = true;

while (hasMore) {
    const response = await fetch(`/api/v1/control/strategy-instances/?page=${page}&page_size=100`);
    // ... 处理响应
    hasMore = pagination.has_next || false;
    page++;
    if (page > 10) break; // 最多10页
}
```

### 文件2: `frontend/control/js/strategy_manager.js`

#### 修复点2: 填充视觉控件 (Lines 1471-1562)
```javascript
// 新增逻辑：检测并填充enum_array、step_array、interval_array控件
const enumControl = form.querySelector(`.enum-array-control[data-field-name="${paramName}"]`);
const stepControl = form.querySelector(`.step-array-control[data-field-name="${paramName}"]`);
const intervalControl = form.querySelector(`.interval-array-control[data-field-name="${paramName}"]`);

if (enumControl) {
    // 勾选对应的复选框
    const checkboxes = enumControl.querySelectorAll('.enum-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = value.includes(checkbox.value);
    });
}
```

#### 修复点3: 模板字段映射 (Line 1449)
```javascript
// 修复前
allowedValues: param.allowed_values  // undefined

// 修复后
allowedValues: param.enum_values || param.allowed_values
```

### 文件3: 缓存版本号
- `templates.html`: `?v=20251028e`
- `strategy_manager.js`: Version 20251028e

## 测试步骤

### 前置条件
1. API服务运行: `http://localhost:8000`
2. 清除浏览器缓存: `Ctrl+Shift+R` 或 `Ctrl+F5`

### 测试用例1: VSS策略（包含speed_steps和vehicle_types）

#### 1.1 打开策略模板页面
```
http://localhost:8000/control/templates.html
```

#### 1.2 定位测试策略
- 策略ID: `strategy_real_vss_g4202_001`
- 策略名称: "G4202绕西双流段早高峰可变限速"
- 策略类型: VSS (可变限速)

#### 1.3 点击"编辑"按钮
弹出编辑模态框

#### 1.4 验证时间-速度步骤 (step_array)
**预期显示**:
```
步骤1: 0时 → 100 km/h
步骤2: 6时 → 80 km/h
步骤3: 7时 → 50 km/h
步骤4: 10时 → 80 km/h
步骤5: 16时 → 100 km/h
步骤6: 23时 → 100 km/h
```

**验证点**:
- ✅ 显示6个时间步骤行
- ✅ 每行有时间输入框和速度输入框
- ✅ 时间值和速度值正确填充
- ✅ 可以点击"+"按钮添加新步骤
- ✅ 可以点击"×"按钮删除步骤（保留至少1个）

#### 1.5 验证车型复选框 (enum_array)
**预期显示**:
```
☑ passenger (乘用车)
☐ bus (公交车)
☑ truck (货车)
☐ emergency (应急车)
```

**验证点**:
- ✅ 显示4个车型复选框（根据模板enum_values）
- ✅ passenger 和 truck 已勾选
- ✅ bus 和 emergency 未勾选
- ✅ 可以手动切换勾选状态

### 测试用例2: DHS策略（包含intervals）

#### 2.1 定位测试策略
- 策略ID: `strategy_real_dhs_g4202_001`
- 策略名称: "G4202成雅段早高峰应急车道开放"
- 策略类型: DHS (动态硬路肩)

#### 2.2 点击"编辑"按钮

#### 2.3 验证时间段配置 (dhs_interval_array)
**预期显示**:
```
时间段1: 0时 → 7时 (CLOSED, emergency)
时间段2: 7时 → 10时 (OPEN, all vehicles)
时间段3: 10时 → 17时 (CLOSED, emergency)
时间段4: 17时 → 19时 (OPEN, all vehicles)
时间段5: 19时 → 24时 (CLOSED, emergency)
```

**验证点**:
- ✅ 显示5个时间段行
- ✅ 每行有开始时间和结束时间输入框
- ✅ 时间值正确填充
- ✅ 可以添加/删除时间段

#### 2.4 验证车型复选框
**预期显示**:
```
☑ passenger
☑ bus
☑ truck
☑ emergency
```

**验证点**:
- ✅ 所有4个车型都已勾选

### 测试用例3: 控制台日志检查

#### 3.1 打开浏览器开发者工具 (F12)

#### 3.2 观察控制台输出
**成功加载的日志**:
```
[StrategyManager] Version 20251028e loaded - enum_values mapping fixed
[fetchExistingStrategyNames] 获取现有策略名称列表
[fetchExistingStrategyNames] 找到 XX 个现有策略名称
[StrategyManager] Loading strategy for editing: strategy_real_vss_g4202_001
[StrategyManager] Strategy loaded: {...}
[StrategyManager] Template loaded for editing
[StrategyManager] Generated edit form
[StrategyManager] Populating enum_array 'applicable_vehicle_types': ["passenger", "truck"]
[StrategyManager] Populating step_array 'speed_steps': [...]
[StrategyManager] Form populated with existing values (including visual controls)
```

**不应该出现的错误**:
- ❌ `422 (Unprocessable Entity)` - page_size错误
- ❌ `Cannot read property 'includes' of undefined` - allowedValues未定义
- ❌ `querySelector returned null` - 控件未找到

### 测试用例4: 编辑并保存

#### 4.1 修改时间步骤
- 修改第3个步骤的速度: 50 → 60 km/h

#### 4.2 修改车型选择
- 勾选 bus 复选框

#### 4.3 点击"保存更改"

#### 4.4 验证保存成功
- ✅ 显示成功提示消息
- ✅ 模态框关闭
- ✅ 策略列表刷新

#### 4.5 重新打开编辑
- ✅ 修改后的值被正确保存和显示

## 性能测试

### API响应时间
```bash
# 测试分页API
time curl -s "http://localhost:8000/api/v1/control/strategy-instances/?page=1&page_size=100" > /dev/null

# 预期: < 500ms
```

### 表单加载时间
- 打开编辑模态框到表单完全显示: **< 1秒**
- 控件数据填充完成: **< 200ms**

## 回归测试

### 创建新策略实例
1. 进入Step 1，选择模板: `vss_moderate`
2. 进入Step 2，选择路段（任意10个）
3. 进入Step 3，配置参数
4. 验证视觉控件正常工作:
   - ✅ 时间-速度步骤默认显示3个步骤
   - ✅ 车型复选框显示4个选项
   - ✅ 所有控件可交互

### 其他策略类型
- TEC策略（收费入口管控）
- 不同模板的参数组合

## 已知限制

1. **编辑时不支持修改路段**: 当前版本只允许编辑参数，不允许修改affected_edges
2. **分页限制**: 策略名称查询最多获取1000条（10页×100）
3. **车型类型固定**: enum_array控件中的车型列表来自模板定义，不可自定义

## 相关文件

- `frontend/control/js/strategy_manager.js` - 策略管理核心逻辑
- `frontend/control/templates.html` - 策略模板页面
- `templates/control_strategies/variable_speed_sign/vss_moderate.json` - VSS模板定义
- `api/routes/control_strategy_instance_routes.py` - 策略实例API路由

## 版本历史

- **20251028e**: 修复enum_values映射和API分页问题
- **20251028d**: 修复编辑表单视觉控件填充
- **20251028c**: 新增视觉控件（enum_array、step_array、interval_array）
