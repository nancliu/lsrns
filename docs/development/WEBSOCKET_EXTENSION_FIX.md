# WebSocket 连接错误 - 浏览器扩展问题解决方案

## ✅ 问题已解决

**问题根源**：hyperCRX 浏览器扩展

**扩展 ID**：`lbbajaehiibofpconjgdjonmkidpcome`

**解决方案**：已删除 hyperCRX 扩展，错误已消除。

**错误调用链**：
```
chrome-extension://lbbajaehiibofpconjgdjonmkidpcome/sandbox.html
chrome-extension://lbbajaehiibofpconjgdjonmkidpcome/sandbox.bundle.js
→ WebSocketClient.js:13
→ socket.js:27
→ ws://localhost:3000/ws (连接失败)
```

## 快速解决方案

如果遇到相同的 WebSocket 连接错误，请检查是否安装了 hyperCRX 或其他可能注入 WebSocket 连接的扩展。

## 详细解决方案（供参考）

### 方案 1：识别并禁用该扩展（推荐）

#### 步骤 1：查找扩展 ID 对应的扩展

**Chrome/Edge 浏览器**：
1. 打开扩展管理页面：
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
2. 启用"开发者模式"（右上角开关）
3. 在地址栏输入扩展 ID：`chrome-extension://lbbajaehiibofpconjgdjonmkidpcome/`
4. 查看页面标题或内容，识别是哪个扩展

**或者使用浏览器控制台**：
```javascript
// 在扩展管理页面打开控制台执行
chrome.management.getAll((extensions) => {
    const ext = extensions.find(e => e.id === 'lbbajaehiibofpconjgdjonmkidpcome');
    if (ext) {
        console.log('扩展名称:', ext.name);
        console.log('扩展描述:', ext.description);
        console.log('扩展详情:', ext);
    } else {
        console.log('未找到该扩展，可能已卸载');
    }
});
```

#### 步骤 2：禁用或卸载扩展

1. 在扩展管理页面找到该扩展
2. **选项 A**：禁用扩展（临时解决）
   - 点击扩展卡片上的"禁用"开关
   - 刷新页面，错误应该消失

3. **选项 B**：卸载扩展（永久解决）
   - 点击扩展卡片上的"删除"按钮
   - 确认删除

#### 步骤 3：验证修复

1. 刷新使用服务的页面
2. 打开浏览器控制台（F12）
3. 检查是否还有 WebSocket 连接错误
4. 确认功能正常

### 方案 2：配置扩展（如果扩展必须保留）

如果该扩展是必需的，可以尝试：

1. **检查扩展设置**：
   - 打开扩展详情页面
   - 查看是否有"在此网站上禁用"选项
   - 将服务地址添加到禁用列表

2. **修改扩展权限**：
   - 在扩展管理页面，点击扩展的"详细信息"
   - 查看权限设置
   - 尝试禁用"访问所有网站的数据"权限

3. **联系扩展开发者**：
   - 报告问题：扩展在不需要时尝试连接 WebSocket
   - 请求修复或提供配置选项

### 方案 3：使用无痕模式（临时方案）

如果无法禁用扩展，可以使用无痕模式：

1. 按 `Ctrl+Shift+N` 打开无痕窗口
2. 访问服务地址
3. 无痕模式下扩展默认被禁用，错误应该消失

**注意**：无痕模式下需要重新登录和配置。

### 方案 4：创建浏览器配置文件（推荐用于生产环境）

为工作环境创建独立的浏览器配置文件：

1. **Chrome**：
   - 点击右上角头像 → "添加" → 创建新配置文件
   - 命名为"工作环境"或类似名称
   - 在新配置文件中只安装工作必需的扩展

2. **Edge**：
   - 点击右上角头像 → "添加配置文件"
   - 创建独立的工作配置文件

**好处**：
- 隔离工作和个人扩展
- 避免扩展冲突
- 更好的安全性

## 已知问题扩展

**hyperCRX**：
- 扩展 ID: `lbbajaehiibofpconjgdjonmkidpcome`
- 问题：该扩展会注入脚本尝试连接 `ws://localhost:3000/ws`
- 影响：从其他电脑访问服务时，会在控制台显示 WebSocket 连接错误
- 解决：禁用或卸载该扩展

**注意**：此错误不影响项目功能，项目使用轮询而非 WebSocket。

## 验证步骤

修复后，验证以下内容：

1. ✅ **错误消失**：
   ```javascript
   // 在浏览器控制台检查
   // 应该没有 WebSocket 连接错误
   ```

2. ✅ **功能正常**：
   - 批量仿真监控功能正常
   - 进度更新正常
   - 图表显示正常

3. ✅ **Network 面板**：
   - 打开开发者工具 → Network
   - 筛选 WS (WebSocket)
   - 应该没有失败的连接

## 预防措施

为避免类似问题：

1. **定期审查扩展**：
   - 只安装必需的扩展
   - 定期检查扩展权限
   - 卸载不使用的扩展

2. **使用独立配置文件**：
   - 为不同用途创建不同的浏览器配置文件
   - 工作和个人环境分离

3. **监控扩展行为**：
   - 使用浏览器控制台监控网络请求
   - 注意扩展注入的脚本

## 总结

✅ **问题根源**：浏览器扩展 `lbbajaehiibofpconjgdjonmkidpcome` 注入的脚本

✅ **解决方案**：
1. 识别并禁用/卸载该扩展（推荐）
2. 配置扩展在特定网站上禁用
3. 使用无痕模式或独立配置文件

✅ **重要**：这个错误不影响项目功能，但禁用扩展可以消除控制台错误，提升用户体验。

