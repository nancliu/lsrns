# Phase 1 Day 4-5 实施指南

**日期**：2025-10-30 (周四-周五)
**目标**：重构 createStrategy() 函数
**预计耗时**：8 小时

---

## 🎯 Day 4-5 目标

### 主要任务

重构 `createStrategy()` 函数 (229 行 → 9 个单一职责函数)：

1. **参数收集函数**（3 个）- 2 小时
   - 收集不同参数类型
   - 处理表格数据
   - 支持可选参数跳过

2. **参数验证函数**（2 个）- 1.5 小时
   - 验证必填参数
   - 验证参数值类型
   - 生成验证报告

3. **API 提交函数**（2 个）- 1.5 小时
   - 构建 API 请求
   - 调用提交接口
   - 处理响应结果

4. **流程协调函数**（2 个）- 1 小时
   - 管理创建流程
   - 处理错误和回滚
   - 刷新界面状态

5. **单元测试**（20+ 个）- 2 小时
   - 每个函数 2-3 个测试
   - 集成测试 5+ 个
   - 覆盖率 >90%

### 成功标志

- ✅ createStrategy() 重构为 9 个函数
- ✅ 单个函数 <50 行
- ✅ 100% JSDoc 覆盖
- ✅ 20+ 个单元测试通过
- ✅ 完整的参数处理流程

---

## 📋 当前分析

### 原函数问题（229 行）

1. **职责过多**
   - 参数收集 (85 行)
   - 参数验证 (20 行)
   - API 调用 (40 行)
   - UI 更新 (30 行)
   - 错误处理 (54 行)

2. **嵌套过深**
   - 3-4 层条件判断
   - 多个参数类型处理混在一起
   - 难以维护和测试

3. **不易扩展**
   - 新增参数类型需要修改主函数
   - 新增验证规则难以添加
   - 难以独立测试各部分

---

## 🛠️ 重构方案

### 新架构设计

```
createStrategy() 流程图：

用户点击创建
   ↓
validateStrategyCreationInput()  ← 基础验证
   ↓
collectAllStrategyParameters()   ← 收集参数
   ↓
validateStrategyParameters()     ← 参数验证
   ↓
buildStrategyPayload()           ← 构建请求
   ↓
submitStrategyToAPI()            ← 提交 API
   ↓
handleStrategyCreationResponse() ← 处理响应
   ↓
refreshStrategyUI()              ← 刷新界面
   ↓
显示成功信息
```

### 9 个重构函数

#### 参数收集 (3 个函数)

**1. collectBasicStrategyInfo()**
```javascript
/**
 * 收集基础策略信息
 * @returns {Object} { templateId, templateObj, strategyName, edgeIds }
 * @throws {Error} 缺少必要信息时抛出
 */
function collectBasicStrategyInfo() {
    // 验证模板选择
    // 验证策略名称
    // 验证路段选择
    // 返回基础信息对象
}
```

**行数**: ~25 行

**2. collectParameterValues(template)**
```javascript
/**
 * 收集参数值（处理所有参数类型）
 * @param {Object} template - 策略模板
 * @returns {Object} 参数名-值映射
 */
function collectParameterValues(template) {
    // 遍历参数 schema
    // 为每个参数调用对应的收集函数
    // 跳过空的可选参数
    // 返回参数对象
}
```

**行数**: ~30 行

**3. extractTableParameters(paramName, paramType)**
```javascript
/**
 * 从表格提取数组参数
 * @param {string} paramName - 参数名
 * @param {string} paramType - 参数类型
 * @returns {Array} 提取的数据数组
 */
function extractTableParameters(paramName, paramType) {
    // 定位表格元素
    // 按类型提取数据（step_array, dhs_interval, flow_interval）
    // 转换数据格式
    // 返回数组数据
}
```

**行数**: ~40 行

#### 参数验证 (2 个函数)

**4. validateStrategyInput(input)**
```javascript
/**
 * 验证策略创建输入
 * @param {Object} input - 输入对象 { templateId, strategyName, edgeIds }
 * @returns {Object} { valid: boolean, errors: Array }
 */
function validateStrategyInput(input) {
    // 验证模板存在
    // 验证策略名称非空
    // 验证路段非空
    // 返回验证结果
}
```

**行数**: ~20 行

**5. validateStrategyParameters(parameters, schema)**
```javascript
/**
 * 验证所有参数
 * @param {Object} parameters - 参数对象
 * @param {Array} schema - 参数定义
 * @returns {Object} { valid: boolean, errors: Object }
 */
function validateStrategyParameters(parameters, schema) {
    // 遍历 schema
    // 验证必填参数
    // 验证参数类型
    // 验证参数值范围（如需要）
    // 返回完整验证结果
}
```

**行数**: ~30 行

#### API 提交 (2 个函数)

**6. buildStrategyPayload(template, parameters, edgeIds, strategyName)**
```javascript
/**
 * 构建策略提交负载
 * @returns {Object} API 请求体
 */
function buildStrategyPayload(template, parameters, edgeIds, strategyName) {
    // 构建标准请求格式
    // 设置模板 ID
    // 设置参数
    // 设置受影响路段
    // 返回完整的负载对象
}
```

**行数**: ~15 行

**7. submitStrategyToAPI(payload)**
```javascript
/**
 * 提交策略到 API
 * @param {Object} payload - 提交数据
 * @returns {Promise<Object>} API 响应结果
 * @throws {Error} API 错误
 */
async function submitStrategyToAPI(payload) {
    // 调用 API 端点
    // 处理 HTTP 响应
    // 解析 JSON 响应
    // 抛出错误或返回结果
}
```

**行数**: ~25 行

#### 流程协调 (2 个函数)

**8. handleStrategyCreationResponse(result)**
```javascript
/**
 * 处理策略创建响应
 * @param {Object} result - API 响应结果
 * @returns {void}
 */
function handleStrategyCreationResponse(result) {
    // 显示成功信息
    // 提取策略 ID
    // 刷新策略列表
    // 重置表单
}
```

**行数**: ~15 行

**9. createStrategy()**
```javascript
/**
 * 创建策略 - 主协调函数
 * 职责：协调整个创建流程
 */
async function createStrategy() {
    try {
        // Step 1: 收集基础信息
        const basicInfo = collectBasicStrategyInfo();

        // Step 2: 收集参数值
        const parameters = collectParameterValues(basicInfo.templateObj);

        // Step 3: 验证输入
        const inputValidation = validateStrategyInput(basicInfo);
        if (!inputValidation.valid) throw new Error(...);

        // Step 4: 验证参数
        const paramValidation = validateStrategyParameters(
            parameters,
            basicInfo.templateObj.parameters_schema
        );
        if (!paramValidation.valid) throw new Error(...);

        // Step 5: 构建请求
        const payload = buildStrategyPayload(
            basicInfo.templateObj,
            parameters,
            basicInfo.edgeIds,
            basicInfo.strategyName
        );

        // Step 6: 提交 API
        const result = await submitStrategyToAPI(payload);

        // Step 7: 处理响应
        handleStrategyCreationResponse(result);

    } catch (error) {
        console.error('[createStrategy] Error:', error);
        alert(`创建失败: ${error.message}`);
    }
}
```

**行数**: ~35 行

---

## 📊 函数对比

### 重构前后对比

| 指标 | 重构前 | 重构后 |
|------|-------|-------|
| 函数数量 | 1 | 9 |
| 主函数行数 | 229 | 35 |
| 平均函数行数 | 229 | 25 |
| 最大函数行数 | 229 | 40 |
| 职责数（主函数） | 5+ | 1 |
| 可测试性 | 低 | 高 |
| JSDoc 覆盖 | 无 | 100% |
| 代码复用性 | 低 | 高 |

---

## 🧪 测试策略

### Unit Tests (15-20 个)

**collectBasicStrategyInfo()** (3 个)
- ✅ 正常情况：收集完整信息
- ✅ 缺少模板：抛出错误
- ✅ 缺少策略名：抛出错误

**collectParameterValues()** (3 个)
- ✅ 单个参数收集
- ✅ 混合参数收集
- ✅ 可选参数跳过

**extractTableParameters()** (3 个)
- ✅ step_array 提取
- ✅ dhs_interval_array 提取
- ✅ flow_interval_array 提取

**validateStrategyInput()** (2 个)
- ✅ 有效输入通过
- ✅ 无效输入失败

**validateStrategyParameters()** (2 个)
- ✅ 所有有效参数通过
- ✅ 缺少必填参数失败

**buildStrategyPayload()** (1 个)
- ✅ 构建正确的请求格式

**submitStrategyToAPI()** (2 个)
- ✅ 成功的 API 调用
- ✅ 失败的 API 调用

### Integration Tests (5+ 个)

1. **完整创建流程** - 从输入到响应
2. **验证失败场景** - 各种验证失败情况
3. **错误处理** - API 错误、网络错误
4. **边界情况** - 空值、大数据等

---

## ⏱️ 时间预算

| 任务 | 预计 |
|------|------|
| 分析和规划 | 1h |
| 实现 9 个函数 | 3.5h |
| 单元测试编写 | 2h |
| 集成测试编写 | 1h |
| 调试和优化 | 0.5h |
| **总计** | **8h** |

---

## 📌 实施步骤

### Step 1: 实现参数收集函数（Day 4 前半）

```bash
# 实现顺序
1. collectBasicStrategyInfo()
2. extractTableParameters()
3. collectParameterValues()
```

### Step 2: 实现验证函数（Day 4 后半）

```bash
# 实现顺序
4. validateStrategyInput()
5. validateStrategyParameters()
```

### Step 3: 实现 API 函数（Day 5 前半）

```bash
# 实现顺序
6. buildStrategyPayload()
7. submitStrategyToAPI()
```

### Step 4: 实现协调函数（Day 5 后半）

```bash
# 实现顺序
8. handleStrategyCreationResponse()
9. createStrategy() (主函数)
```

### Step 5: 创建测试套件

```bash
# 测试覆盖
- 单元测试：createStrategyTests.test.js (20+ 个)
- 集成测试：createStrategyIntegration.test.js (5+ 个)
```

---

## ✅ 完成检查清单

- [ ] 9 个函数实现
- [ ] 单个函数 <50 行
- [ ] 100% JSDoc 覆盖
- [ ] 20+ 单元测试
- [ ] 5+ 集成测试
- [ ] 所有测试通过
- [ ] 代码审查就绪

---

**版本**：1.0
**状态**：准备就绪
**预计完成**：2025-10-31

🚀 **准备开始 Day 4-5 重构！**
