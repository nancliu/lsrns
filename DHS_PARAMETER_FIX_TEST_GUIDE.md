# DHS 参数控件修复 - 测试指南

**修复日期**: 2025-10-30
**预计测试时间**: 5-10 分钟

---

## 修复内容快速摘要

✅ **DHS 车型选择**: text input → select multiple (多选下拉框)
✅ **参数提取逻辑**: 更新以支持 select multiple
✅ **时间轴渲染**: 已验证正确调用 TimelineVisualizer
✅ **代码清理**: 验证无旧控件干扰

---

## 启动服务器

**重要**: 必须在 `od_project` 环境下启动服务器

```powershell
# 1. 激活环境
conda activate od_project

# 2. 启动服务器
cd D:\projects\OD_SIM
.\start_api.ps1

# 3. 等待启动完成
# 看到 "Application startup complete" 表示成功
```

---

## 测试步骤

### 步骤 1: 打开策略配置页面

访问: `http://localhost:8000/control/templates.html`

### 步骤 2: 选择 DHS 策略

1. **策略类型**: 选择 **"应急车道开放（DHS）"**
2. **模板**: 选择 **"应急车道开放"** (dhs_peak_hours)
3. 点击 **"下一步"**

### 步骤 3: 选择路段

1. **路线**: 选择 **G4202** (成都绕城高速)
2. **方向**: 选择 **逆时针**
3. **区段**: 选择任意区段（例如 K38.2-K36.9）
4. 点击 **"下一步"** 进入参数配置

### 步骤 4: 检查参数配置页面

#### ✅ 验证点 1: 时间轴显示

**预期**:
- 表格上方显示 **24 小时时间轴**
- 有 **5 个时间槽**（默认配置）
- **绿色槽** = OPEN (开放)
- **红色槽** = CLOSED (关闭)
- 每个槽显示时间范围标签（例如："开启 07:00-09:00"）

**如果没有时间轴**:
- 打开浏览器控制台（F12）
- 查看是否有错误信息
- 检查 `window.TimelineVisualizer` 是否存在

#### ✅ 验证点 2: 车型选择控件

**预期**:
- **"允许车型"** 列显示为 **多选下拉框**（不是 text input）
- 下拉框显示 **5 个选项**:
  - 乘用车
  - 公交车
  - 货车
  - 应急车
  - 执法车
- **默认选中项**（第 1 个区间）:
  - 应急车 ✅
  - 执法车 ✅

**截图对比**:

**修复前** (text input):
```
┌──────────────────────────────────────┐
│ [passenger,bus,truck,emergency     ] │  ← text input
└──────────────────────────────────────┘
```

**修复后** (select multiple):
```
┌──────────────────────────────────────┐
│ ☐ 乘用车                              │
│ ☐ 公交车                              │
│ ☐ 货车                                │
│ ☑ 应急车                              │  ← select multiple
│ ☑ 执法车                              │
└──────────────────────────────────────┘
```

#### ✅ 验证点 3: 交互功能

**测试操作**:
1. **修改时间区间**: 将第 1 个区间的结束时间从 7 改为 8
   - 预期: 时间轴自动更新
2. **修改车型选择**: 点击车型下拉框，多选几个车型
   - 预期: 可以选中多个车型（按住 Ctrl 多选）
3. **添加新区间**: 点击 "+ 添加时间区间" 按钮
   - 预期: 新行显示车型多选下拉框（不是 text input）

### 步骤 5: 创建策略实例

#### 5.1 填写必填参数

| 参数名 | 值 | 说明 |
|-------|-----|------|
| **affected_edges** | (已自动填充) | 选择的路段边列表 |
| **intervals** | (使用默认值或修改) | 时间区间列表 |
| **hard_shoulder_lane_index** | `-1` 或 `0` | 应急车道索引 |
| **allowed_vehicle_types** | (可选) | 顶层车型参数 |

**注意**: DHS 有两个 `allowed_vehicle_types`:
1. **intervals 内部**: 每个时间区间的车型（必须填写）
2. **顶层参数**: 整体策略的车型（可选）

#### 5.2 点击 "生成策略实例"

#### 5.3 检查 Network 请求

打开开发者工具的 **Network** 标签:

**请求 URL**:
```
POST http://localhost:8000/api/v1/control/strategies/instances
```

**请求 Payload** (关键部分):
```json
{
  "template_id": "dhs_peak_hours",
  "strategy_name": "测试策略",
  "configured_params": {
    "affected_edges": ["-8712", "-15452.627", ...],
    "intervals": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]  // ✅ 数组格式
      },
      {
        "begin_hours": 7,
        "end_hours": 9,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]  // ✅ 数组格式
      },
      ...
    ],
    "hard_shoulder_lane_index": -1
  }
}
```

**关键验证**:
- ✅ `allowed_vehicle_types` 是 **数组** (不是字符串 "passenger,bus,...")
- ✅ 每个时间区间都有 `allowed_vehicle_types` 字段
- ✅ 车型值是英文小写（passenger, bus, truck, emergency, authority）

#### 5.4 检查响应

**成功响应** (200 OK):
```json
{
  "strategy_id": "strategy_dhs_peak_hours_20251030_030123",
  "message": "Strategy instance created successfully",
  "file_path": "control_data/strategies/strategy_dhs_peak_hours_20251030_030123.json"
}
```

**如果失败** (400 或 500):
- 查看响应的 `detail` 字段
- 检查是否有参数验证错误
- 查看服务器日志

---

## 常见问题排查

### Q1: 时间轴不显示

**原因**: TimelineVisualizer 未加载

**解决方案**:
1. 检查 `timeline_visualizer.js` 是否已加载
2. 在控制台运行: `console.log(window.TimelineVisualizer)`
3. 应该看到对象，不是 undefined

### Q2: 车型列显示为 text input（修复未生效）

**原因**: 浏览器缓存

**解决方案**:
1. **强制刷新**: `Ctrl + F5` (Windows) 或 `Cmd + Shift + R` (Mac)
2. **清除缓存**: 开发者工具 → Network → Disable cache
3. **重启浏览器**: 关闭所有浏览器窗口后重新打开

### Q3: 策略创建失败 - "intervals not provided"

**原因**: 模板继承未解析（之前的 bug）

**验证修复**:
```bash
# 检查 API 返回的模板是否包含 intervals 参数
curl http://localhost:8000/api/v1/control/templates/dhs_peak_hours | grep intervals
```

**如果没有 intervals**:
- 服务器未重启或 uvicorn 自动重载失败
- 需要手动重启服务器

### Q4: 车型数组提取失败

**错误**: `Cannot read property 'selectedOptions' of null`

**原因**: 代码未正确部署

**解决方案**:
1. 确认 `templates.html` 的修改已保存
2. 强制刷新浏览器 (`Ctrl + F5`)
3. 检查代码修改是否正确（Lines 2983-2993）

### Q5: 策略创建请求中断 - "[Request interrupted by user]"

**可能原因**:
1. **前端错误**: 检查浏览器控制台是否有 JavaScript 错误
2. **网络问题**: 检查 Network 标签是否有请求失败
3. **后端错误**: 查看服务器日志是否有异常

**解决方案**:
- 打开浏览器控制台查看完整错误信息
- 检查 Network 请求的 Response 标签
- 查看服务器终端的错误日志

---

## 成功标志

所有以下验证点通过，说明修复成功：

- [x] **时间轴显示**: 表格上方显示 24 小时时间轴
- [x] **车型控件**: "允许车型" 列为 select multiple (不是 text input)
- [x] **默认选中**: 车型下拉框有默认选中项
- [x] **交互更新**: 修改参数时时间轴实时更新
- [x] **添加区间**: 新区间的车型列也是 select multiple
- [x] **参数格式**: Network Payload 中 allowed_vehicle_types 是数组
- [x] **策略创建**: 成功创建策略（200 响应）
- [x] **文件生成**: control_data/strategies/ 目录下有新策略文件

---

## 验证完成后

### 1. 查看生成的策略文件

```powershell
# 查看最新创建的策略
ls control_data/strategies/ | sort LastWriteTime -Descending | select -First 1

# 查看文件内容
cat control_data/strategies/strategy_dhs_*.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 2. 验证车型格式

检查策略文件中的 `intervals` 数组：

```json
{
  "configured_params": {
    "intervals": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]  // ✅ 数组格式，不是字符串
      }
    ]
  }
}
```

### 3. 记录测试结果

如果测试通过，请反馈：
- ✅ 车型控件显示正常（select multiple）
- ✅ 策略创建成功
- ✅ 生成的策略文件格式正确

如果测试失败，请提供：
- ❌ 浏览器控制台截图
- ❌ Network 请求/响应截图
- ❌ 服务器日志

---

## 额外测试（可选）

### 测试 TEC 策略（预防性验证）

虽然 TEC 策略没有车型参数问题，建议测试确保没有意外影响：

1. 选择 **"收费站流量控制（TEC）"** 策略类型
2. 选择 TEC 模板
3. 选择路段
4. 检查参数配置页面
5. 测试策略创建

**预期**: TEC 策略创建正常，无错误

---

**测试文档创建时间**: 2025-10-30
**预计测试时间**: 5-10 分钟
**风险级别**: 低
