# 前端开发快速参考

> 常用代码片段和检查清单

## 案例筛选

### 加载所有案例
```javascript
const response = await fetch(`/api/v1/case/list_cases/?page_size=1000`);
```

### 筛选OD提取案例
```javascript
const odCases = allCases.filter(c => {
    const sourceType = c.source_type || '';
    const caseType = c.case_type || '';
    return !(sourceType.includes('event_scenario') ||
             caseType === 'event_based' ||
             caseType === 'event_scenario_case');
});
```

### 筛选事件场景案例
```javascript
const eventCases = allCases.filter(c => {
    const sourceType = c.source_type || '';
    const caseType = c.case_type || '';
    return sourceType.includes('event_scenario') ||
           caseType === 'event_based' ||
           caseType === 'event_scenario_case';
});
```

## 表单验证

### 创建select选项
```javascript
const option = document.createElement('option');
option.value = caseId;           // ← 必须设置
option.textContent = displayText;
option.disabled = false;
select.appendChild(option);
```

### 创建错误提示选项
```javascript
const option = document.createElement('option');
option.value = '';               // ← 明确设置空字符串
option.disabled = true;
option.textContent = '没有可用的案例';
select.appendChild(option);
```

### 自动选择第一个有效选项
```javascript
let selectedValue = null;
for (let i = 1; i < select.options.length; i++) {
    const option = select.options[i];
    if (!option.disabled &&
        option.value &&
        option.value.startsWith('case_')) {
        selectedValue = option.value;
        break;
    }
}
```

## 参数验证

### 验证case_id
```javascript
function isValidCaseId(caseId) {
    return caseId &&
           typeof caseId === 'string' &&
           caseId.startsWith('case_') &&
           caseId.length > 6;
}
```

### API调用前验证
```javascript
if (!isValidCaseId(caseId)) {
    console.warn('Invalid case_id:', caseId);
    return;
}
const response = await fetch(`/api/cases/${caseId}/...`);
```

## LocalStorage

### 安全存储
```javascript
if (isValidCaseId(caseId)) {
    localStorage.setItem('batchSim.selectedCaseId', caseId);
}
```

### 安全读取
```javascript
const caseId = localStorage.getItem('batchSim.selectedCaseId');
if (!isValidCaseId(caseId)) {
    localStorage.removeItem('batchSim.selectedCaseId');
    return null;
}
```

## 错误处理

### 并行加载
```javascript
const [cases, plans] = await Promise.allSettled([
    loadCases(),
    loadPlans()
]);

if (cases.status === 'fulfilled') {
    populateCaseSelect(cases.value);
} else {
    console.error('Failed to load cases:', cases.reason);
    showWarning('案例加载失败');
}
```

### Try-Catch包装
```javascript
async function loadData(id) {
    if (!isValidId(id)) return null;

    try {
        const response = await fetch(`/api/data/${id}`);
        if (!response.ok) throw new Error(response.statusText);
        return await response.json();
    } catch (error) {
        console.error('Load failed:', error);
        return null;  // 返回默认值
    }
}
```

## 检查清单

### 案例列表加载
- [ ] `page_size=1000`
- [ ] 筛选逻辑使用 `includes('event_scenario')`
- [ ] 同时检查 `source_type` 和 `case_type`

### 创建Select选项
- [ ] 所有option明确设置 `value`
- [ ] 错误/提示选项 `value = ''`
- [ ] 验证自动选择逻辑

### API调用
- [ ] 调用前验证参数
- [ ] Try-Catch错误处理
- [ ] 返回默认值（不抛异常）

### LocalStorage
- [ ] 存储前验证格式
- [ ] 读取后验证格式
- [ ] 无效数据自动清理

---

**参考**: [完整最佳实践文档](./FRONTEND_BEST_PRACTICES.md)
