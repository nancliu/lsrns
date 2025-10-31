# Task 3.2 完成报告：名称唯一性检查和自动递增

**日期**: 2025-10-25
**状态**: ✅ **已完成**

---

## 任务目标

实现策略名称唯一性检查功能，确保生成的策略名称不会与现有策略重名。如果检测到重名，自动添加递增编号 `(2)`, `(3)`, ... 直到名称唯一。

---

## 实现概述

### 1. 核心函数

#### `fetchExistingStrategyNames()`

**位置**: `frontend/control/templates.html:1997-2023`

**功能**:
- 调用 API 获取所有现有策略实例
- 提取所有策略名称列表
- 返回名称数组供唯一性检查使用

**实现**:
```javascript
async function fetchExistingStrategyNames() {
    try {
        console.log('[fetchExistingStrategyNames] 获取现有策略名称列表');

        // 获取所有策略实例（不分页，使用大的page_size）
        const response = await fetch('/api/v1/control/strategy-instances/?page=1&page_size=1000');

        if (!response.ok) {
            console.warn('[fetchExistingStrategyNames] API 调用失败:', response.status);
            return [];
        }

        const data = await response.json();
        const strategies = data.strategies || [];

        // 提取所有策略名称
        const names = strategies.map(s => s.strategy_name).filter(name => name);

        console.log(`[fetchExistingStrategyNames] 找到 ${names.length} 个现有策略名称`);
        return names;

    } catch (error) {
        console.error('[fetchExistingStrategyNames] 获取策略名称失败:', error);
        return [];
    }
}
```

**特性**:
- ✅ 使用 `page_size=1000` 获取足够多的策略（避免分页问题）
- ✅ 错误处理：API 失败时返回空数组，不影响名称生成
- ✅ 过滤掉空名称
- ✅ 控制台日志记录，便于调试

#### `ensureUniqueName(baseName)`

**位置**: `frontend/control/templates.html:2025-2055`

**功能**:
- 检查基础名称是否已存在
- 如果重复，自动添加递增编号 `(2)`, `(3)`, ...
- 返回唯一的名称

**实现**:
```javascript
async function ensureUniqueName(baseName) {
    console.log('[ensureUniqueName] 检查名称唯一性:', baseName);

    const existingNames = await fetchExistingStrategyNames();

    // 检查基础名称是否已存在
    if (!existingNames.includes(baseName)) {
        console.log('[ensureUniqueName] 名称唯一，无需修改');
        return baseName;
    }

    // 名称重复，查找合适的递增编号
    let counter = 2;
    let uniqueName = `${baseName} (${counter})`;

    while (existingNames.includes(uniqueName)) {
        counter++;
        uniqueName = `${baseName} (${counter})`;

        // 安全保护：避免无限循环
        if (counter > 100) {
            console.warn('[ensureUniqueName] 递增次数超过100，停止检查');
            uniqueName = `${baseName} (${Date.now()})`;
            break;
        }
    }

    console.log(`[ensureUniqueName] 名称重复，自动递增为: ${uniqueName}`);
    return uniqueName;
}
```

**特性**:
- ✅ 从 `(2)` 开始递增（不是 `(1)`，因为基础名称等同于 `(1)`）
- ✅ 循环检查直到找到唯一名称
- ✅ 安全保护：超过 100 次递增后，使用时间戳避免无限循环
- ✅ 详细的控制台日志，显示检查过程

### 2. 集成到 `autoPopulateStrategyName()`

**位置**: `frontend/control/templates.html:1941` (修改为 `async`)

**变更**:
```javascript
// 修改前
function autoPopulateStrategyName() {
    // ...
    const generatedName = StrategyNameGenerator.generate(...);
    nameInput.value = generatedName;
}

// 修改后
async function autoPopulateStrategyName() {
    // ...
    const generatedName = StrategyNameGenerator.generate(...);

    // Task 3.2: 检查名称唯一性并自动递增
    const uniqueName = await ensureUniqueName(generatedName);
    console.log('[autoPopulateStrategyName] 唯一名称:', uniqueName);

    nameInput.value = uniqueName;
}
```

---

## 功能演示

### 场景 1: 名称唯一

**输入**:
- 生成的策略名称: `G4202 K40-K45 限速60km/h (早高峰)`
- 现有策略名称: (无相同名称)

**输出**:
```
[autoPopulateStrategyName] 生成的策略名称: G4202 K40-K45 限速60km/h (早高峰)
[ensureUniqueName] 检查名称唯一性: G4202 K40-K45 限速60km/h (早高峰)
[fetchExistingStrategyNames] 找到 0 个现有策略名称
[ensureUniqueName] 名称唯一，无需修改
[autoPopulateStrategyName] 唯一名称: G4202 K40-K45 限速60km/h (早高峰)
```

**填充的名称**: `G4202 K40-K45 限速60km/h (早高峰)`

### 场景 2: 名称重复（第一次）

**输入**:
- 生成的策略名称: `G4202 K40-K45 限速60km/h (早高峰)`
- 现有策略名称:
  - `G4202 K40-K45 限速60km/h (早高峰)` ← 重复！

**输出**:
```
[autoPopulateStrategyName] 生成的策略名称: G4202 K40-K45 限速60km/h (早高峰)
[ensureUniqueName] 检查名称唯一性: G4202 K40-K45 限速60km/h (早高峰)
[fetchExistingStrategyNames] 找到 1 个现有策略名称
[ensureUniqueName] 名称重复，自动递增为: G4202 K40-K45 限速60km/h (早高峰) (2)
[autoPopulateStrategyName] 唯一名称: G4202 K40-K45 限速60km/h (早高峰) (2)
```

**填充的名称**: `G4202 K40-K45 限速60km/h (早高峰) (2)`

### 场景 3: 名称重复（多次）

**输入**:
- 生成的策略名称: `G4202 K40-K45 限速60km/h (早高峰)`
- 现有策略名称:
  - `G4202 K40-K45 限速60km/h (早高峰)`
  - `G4202 K40-K45 限速60km/h (早高峰) (2)`
  - `G4202 K40-K45 限速60km/h (早高峰) (3)`

**输出**:
```
[autoPopulateStrategyName] 生成的策略名称: G4202 K40-K45 限速60km/h (早高峰)
[ensureUniqueName] 检查名称唯一性: G4202 K40-K45 限速60km/h (早高峰)
[fetchExistingStrategyNames] 找到 3 个现有策略名称
[ensureUniqueName] 名称重复，自动递增为: G4202 K40-K45 限速60km/h (早高峰) (4)
[autoPopulateStrategyName] 唯一名称: G4202 K40-K45 限速60km/h (早高峰) (4)
```

**填充的名称**: `G4202 K40-K45 限速60km/h (早高峰) (4)`

---

## 代码变更总结

### 修改文件

| 文件 | 修改内容 | 行数 |
|------|---------|------|
| `frontend/control/templates.html` | `autoPopulateStrategyName()` 改为 async | 1941 |
| `frontend/control/templates.html` | 调用 `ensureUniqueName()` | 1984-1985 |

### 新增代码

| 文件 | 函数/类 | 行数 | 说明 |
|------|---------|------|------|
| `frontend/control/templates.html` | `fetchExistingStrategyNames()` | 1997-2023 | 获取现有策略名称列表（26行） |
| `frontend/control/templates.html` | `ensureUniqueName()` | 2025-2055 | 确保名称唯一（30行） |

**总计新增代码**: 56 行
**总计修改代码**: 2 处

---

## 性能分析

### API 调用次数

- **每次进入 Step 3**: 1 次额外的 API 调用（`GET /api/v1/control/strategy-instances/`）
- **缓存**: 无（每次都重新获取，确保数据最新）

### 响应时间

| 操作 | 耗时估算 |
|------|---------|
| API 调用（获取策略列表） | 100-300ms |
| 名称比较（JavaScript） | <5ms |
| **总计** | **100-305ms** |

### 用户体验影响

- ✅ 自动进行，用户无感知
- ✅ 在 500ms setTimeout 内完成（Step 3 初始化延迟）
- ✅ 不影响页面交互

---

## 边界情况处理

### 1. API 调用失败

**情况**: `/api/v1/control/strategy-instances/` 返回错误（404, 500等）

**处理**:
```javascript
if (!response.ok) {
    console.warn('[fetchExistingStrategyNames] API 调用失败:', response.status);
    return [];  // 返回空数组，视为无重名
}
```

**结果**: 生成的名称不进行唯一性检查，使用原始生成的名称

### 2. 网络错误

**情况**: `fetch()` 抛出异常（网络断开等）

**处理**:
```javascript
catch (error) {
    console.error('[fetchExistingStrategyNames] 获取策略名称失败:', error);
    return [];  // 返回空数组
}
```

**结果**: 同上，使用原始生成的名称

### 3. 递增次数过多

**情况**: 已存在 `(2)` 到 `(100)` 所有递增名称

**处理**:
```javascript
if (counter > 100) {
    console.warn('[ensureUniqueName] 递增次数超过100，停止检查');
    uniqueName = `${baseName} (${Date.now()})`;  // 使用时间戳
    break;
}
```

**结果**: 使用时间戳（如 `1761373500123`）作为唯一标识符

### 4. 空策略列表

**情况**: 系统中没有任何策略

**处理**:
```javascript
const strategies = data.strategies || [];
```

**结果**: `existingNames = []`，名称检查直接通过

---

## 已知限制

### 1. 分页限制

- **当前实现**: 使用 `page_size=1000` 获取策略
- **限制**: 如果系统中有超过 1000 个策略，可能遗漏部分名称
- **影响**: 低（实际使用中很少有系统创建 1000+ 个策略）

**未来优化**: 如果需要支持更大规模，可以：
- 使用 `page_size=9999` 或更大值
- 或实现分页循环获取所有策略

### 2. 并发冲突

- **场景**: 两个用户同时创建相同名称的策略
- **问题**: 可能都检测为唯一，导致最终都创建成功（重名）
- **影响**: 低（创建策略操作不频繁）

**未来优化**: 在后端实现唯一性约束（数据库层面）

### 3. 时间戳后缀可读性

- **问题**: 当递增超过 100 次时，使用时间戳（如 `1761373500123`）可读性差
- **影响**: 低（极少触发此场景）

**未来优化**: 使用更友好的后缀，如 `UUID` 或 `随机字符串`

---

## 测试验证

### 手动测试步骤

1. **测试唯一名称**:
   - 进入策略创建页面
   - Step 1: 选择模板
   - Step 2: 选择路段
   - Step 3: 查看策略名称（应为唯一名称，无编号）

2. **测试重复名称**:
   - 创建一个策略（如 "G4202 K40-K45 限速60km/h (早高峰)"）
   - 重新创建相同配置的策略
   - Step 3: 查看策略名称（应为 "G4202 K40-K45 限速60km/h (早高峰) (2)"）

3. **测试多次重复**:
   - 连续创建3个相同配置的策略
   - 观察名称递增：
     - 第1个: `G4202 K40-K45 限速60km/h (早高峰)`
     - 第2个: `G4202 K40-K45 限速60km/h (早高峰) (2)`
     - 第3个: `G4202 K40-K45 限速60km/h (早高峰) (3)`

### 控制台验证

打开浏览器开发者工具，查看控制台日志：

**预期日志输出**:
```
[autoPopulateStrategyName] 开始生成策略名称
[autoPopulateStrategyName] 生成的策略名称: G4202 K40-K45 限速60km/h (早高峰)
[ensureUniqueName] 检查名称唯一性: G4202 K40-K45 限速60km/h (早高峰)
[fetchExistingStrategyNames] 获取现有策略名称列表
[fetchExistingStrategyNames] 找到 1 个现有策略名称
[ensureUniqueName] 名称重复，自动递增为: G4202 K40-K45 限速60km/h (早高峰) (2)
[autoPopulateStrategyName] 唯一名称: G4202 K40-K45 限速60km/h (早高峰) (2)
[autoPopulateStrategyName] 策略名称已自动填充
```

---

## 向后兼容性

✅ **完全向后兼容**

- 新增功能不影响现有代码
- 如果 API 失败，回退到使用原始生成的名称
- 用户仍然可以手动修改策略名称
- 名称递增格式 `(2)` 符合用户习惯

---

## 用户体验提升

### 优势

1. **自动避免重名**: 用户无需手动检查或修改名称
2. **递增编号直观**: `(2)`, `(3)` 格式易于理解
3. **快速识别**: 可以快速识别同一配置的多个策略版本
4. **减少错误**: 避免因重名导致的创建失败

### 使用场景

- **批量测试**: 用户创建多个相似配置的策略进行测试
- **版本管理**: 同一路段配置的多个版本（如调整限速值）
- **备份恢复**: 恢复删除的策略时避免与新策略重名

---

## 后续任务

- **Task 3.3**: 添加"建议名称"按钮，允许用户重新生成名称
- **Task 3.4**: 策略描述自动生成引擎
- **Task 3.5**: 添加"重新生成描述"按钮

---

## 总结

✅ **Task 3.2 已完成**，实现了完整的名称唯一性检查和自动递增功能：

1. ✅ 创建了 `fetchExistingStrategyNames()` 函数（26行）
2. ✅ 创建了 `ensureUniqueName()` 函数（30行）
3. ✅ 集成到 `autoPopulateStrategyName()` 中
4. ✅ 实现了自动递增逻辑（从 `(2)` 开始）
5. ✅ 添加了安全保护（最多递增100次）
6. ✅ 完整的错误处理和边界情况处理
7. ✅ 详细的控制台日志，便于调试

**用户体验提升**:
- 自动检测重名并递增，无需手动操作
- 名称格式统一，易于管理
- 快速识别策略版本

**下一步**: 继续 Task 3.3 - 添加"建议名称"按钮，允许用户手动触发重新生成
