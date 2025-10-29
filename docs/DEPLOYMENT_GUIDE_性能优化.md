# 性能优化部署指南

**优化目标**: 修复路段代码下拉框加载慢（5-10秒）的问题
**预期效果**: 加载时间降低到 <500ms（10-20倍性能提升）

---

## 📋 前置检查

### ✅ 已完成的修改

1. **前端代码已优化** ✅
   - 文件：`frontend/control/js/edge_selector_embedded.js`
   - 变更：`updateDirectionOptions()` 函数已改为静态路线分类
   - 无需额外操作（代码已在仓库中）

2. **数据库迁移脚本已创建** ✅
   - 文件：`database/migrations/004_add_edge_query_indexes.sql`
   - 内容：6个数据库索引
   - 需要执行：**是**（需要你手动应用）

---

## 🚀 部署步骤

### 步骤1：应用数据库索引（必需）

你有3种方式选择：

#### 方式A：使用数据库管理工具（推荐）

1. **打开你的数据库管理工具**（pgAdmin、DBeaver、Navicat 等）

2. **连接到数据库**：
   - Host: `10.149.235.123`
   - Port: `5432`
   - Database: `sdzg`
   - User/Password: 你的数据库凭据

3. **打开迁移SQL文件**：
   - 路径：`d:\projects\OD_SIM\database\migrations\004_add_edge_query_indexes.sql`
   - 复制全部内容

4. **在SQL查询窗口中粘贴并执行**

5. **验证索引创建成功**（执行以下查询）：
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename = 'sim_network_edges' AND schemaname = 'dim'
   ORDER BY indexname;
   ```

   **预期结果**：应该看到以下4个新索引
   ```
   idx_sim_network_edges_route_code
   idx_sim_network_edges_section_code
   idx_sim_network_edges_route_section    ← 最关键！
   idx_sim_network_edges_demonstration_id
   ```

---

#### 方式B：使用 psql 命令行

如果你已安装 PostgreSQL 客户端工具：

1. **编辑批处理脚本**：
   - 打开 `d:\projects\OD_SIM\apply_migration_simple.bat`
   - 修改数据库凭据（第5-9行）：
     ```batch
     set DB_HOST=10.149.235.123
     set DB_PORT=5432
     set DB_NAME=sdzg
     set DB_USER=你的用户名
     set PGPASSWORD=你的密码
     ```

2. **运行脚本**：
   ```cmd
   cd d:\projects\OD_SIM
   apply_migration_simple.bat
   ```

3. **检查输出**：
   - 成功：`[SUCCESS] Migration applied successfully!`
   - 失败：检查错误信息，可能是凭据错误或 psql 未安装

---

#### 方式C：手动复制SQL逐条执行

如果上述方式都不可行，可以手动复制以下SQL语句到数据库工具执行：

```sql
-- 1. 创建 route_code 索引
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_route_code
ON dim.sim_network_edges(route_code);

-- 2. 创建 section_code 索引
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_section_code
ON dim.sim_network_edges(section_code);

-- 3. 创建复合索引（最重要！）
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_route_section
ON dim.sim_network_edges(route_code, section_code);

-- 4. 创建 demonstration_id 部分索引
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_demonstration_id
ON dim.sim_network_edges(demonstration_id)
WHERE demonstration_id IS NOT NULL;

-- 5. 创建 JOIN 优化索引
CREATE INDEX IF NOT EXISTS idx_multiscale_node_units_junction_id
ON dim.multiscale_node_units(junction_id);

CREATE INDEX IF NOT EXISTS idx_point_gantry_route_stake
ON dim.point_gantry(route_code, gantry_stake);

-- 6. 更新统计信息
ANALYZE dim.sim_network_edges;
ANALYZE dim.multiscale_node_units;
ANALYZE dim.point_gantry;
```

---

### 步骤2：重启API服务器

前端代码更新需要重启服务器才能生效：

```powershell
# 停止当前运行的服务器（如果有）
# 然后启动：
.\start_api.ps1

# 或者
.\start_api.bat

# 或者
python api\main.py
```

---

### 步骤3：清除浏览器缓存

**重要**：浏览器可能缓存了旧的 JavaScript 文件

- **方法1**：强制刷新 `Ctrl + Shift + R`（Windows）
- **方法2**：清空浏览器缓存后刷新
- **方法3**：使用隐私/无痕模式打开

---

### 步骤4：测试性能改进

#### 测试场景1：选择环形高速（SA2 或 G4202）

1. 打开 `http://localhost:8000/control/templates.html`
2. 导航到策略创建向导 → "Step 2: Select Edges"
3. 打开浏览器 DevTools（F12）→ Network 标签
4. 选择路线：**SA2** 或 **G4202**

**预期结果**：
- ✅ 路段下拉框在 <500ms 内填充
- ✅ 方向下拉框只显示 "全部/顺时针/逆时针"（不显示上行/下行）
- ✅ Network 标签只有1个API调用：`/api/v1/control/edges/sections?route_code=SA2`
- ❌ 不应有：`/api/v1/control/edges/query`

---

#### 测试场景2：选择线性高速（如 G5）

1. 选择路线：**G5** 或其他非环形路线

**预期结果**：
- ✅ 路段下拉框在 <500ms 内填充
- ✅ 方向下拉框只显示 "全部/上行/下行"（不显示顺时针/逆时针）
- ✅ 响应时间快速

---

#### 测试场景3：混合选择

1. 同时选择 **SA2** 和 **G5**

**预期结果**：
- ✅ 方向下拉框显示全部4个方向选项
- ✅ 响应时间快速

---

### 步骤5：验证数据库查询性能

在数据库工具中执行以下查询，测试索引效果：

```sql
EXPLAIN ANALYZE
SELECT
    section_code,
    route_code,
    COUNT(*) as edge_count,
    MIN(start_stake) as min_stake,
    MAX(end_stake) as max_stake
FROM dim.sim_network_edges
WHERE section_code IS NOT NULL
  AND route_code = 'G4202'
GROUP BY section_code, route_code
ORDER BY route_code, section_code;
```

**预期结果**：
- ✅ 执行计划显示 `Index Scan using idx_sim_network_edges_route_section`
- ✅ 执行时间 < 400ms（之前是 3-6秒）
- ❌ 不应显示 `Seq Scan`（全表扫描）

---

## ✅ 成功标准

所有以下检查都通过：

- [x] 数据库索引创建成功（验证查询返回4+个索引）
- [x] API服务器已重启
- [x] 浏览器缓存已清除
- [ ] 选择路线后，路段下拉框 <500ms 填充 ← **核心指标**
- [ ] Network 标签只有1个 `/sections` API调用
- [ ] 方向选项根据路线类型正确显示
- [ ] 数据库查询使用索引扫描（不是全表扫描）

---

## 🔧 故障排查

### 问题1：还是很慢（>2秒）

**可能原因1**：索引未创建或未生效

**解决方法**：
```sql
-- 检查索引是否存在
SELECT indexname FROM pg_indexes WHERE tablename = 'sim_network_edges';

-- 如果缺少，手动创建最关键的索引
CREATE INDEX idx_sim_network_edges_route_section
ON dim.sim_network_edges(route_code, section_code);

-- 强制更新统计信息
ANALYZE dim.sim_network_edges;
```

**可能原因2**：浏览器缓存未清除

**解决方法**：
- 按 `Ctrl + Shift + R` 强制刷新
- 或使用隐私模式重新打开

**可能原因3**：API服务器未重启

**解决方法**：
- 确认重启了 `start_api.ps1`
- 检查终端是否有错误信息

---

### 问题2：Network 标签还是显示2个API调用

**原因**：前端代码未更新

**解决方法**：
1. 检查文件 `frontend/control/js/edge_selector_embedded.js`
2. 在 `updateDirectionOptions()` 函数中（约145行）
3. 确认**没有** `fetch()` 调用
4. 确认**有** `const ringRoutes = new Set(['SA2', 'G4202']);`

如果代码不对，说明文件未保存或API服务器未重启。

---

### 问题3：方向选项显示不正确

**示例**：选择SA2却显示"上行/下行"

**原因**：前端代码未更新

**解决方法**：
- 检查浏览器Console（F12 → Console标签）是否有JavaScript错误
- 确认 `edge_selector_embedded.js` 文件已正确修改
- 清除浏览器缓存后再试

---

### 问题4：数据库查询还是全表扫描

**原因**：PostgreSQL查询规划器未使用索引

**解决方法**：
```sql
-- 强制更新统计信息
ANALYZE dim.sim_network_edges;

-- 检查索引是否有效
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'sim_network_edges';
```

如果 `idx_scan = 0`，说明索引从未被使用。可能需要重建索引：
```sql
REINDEX INDEX dim.idx_sim_network_edges_route_section;
```

---

## 🔙 回滚方案

如果优化导致问题，可以快速回滚：

### 回滚数据库索引

```sql
-- 删除所有新建索引
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_code;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_section_code;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_section;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_demonstration_id;
DROP INDEX IF EXISTS dim.idx_multiscale_node_units_junction_id;
DROP INDEX IF EXISTS dim.idx_point_gantry_route_stake;
```

### 回滚前端代码

```bash
# 使用 Git 回退到之前的版本
git checkout HEAD~1 -- frontend/control/js/edge_selector_embedded.js

# 重启API服务器
.\start_api.ps1
```

---

## 📊 性能基准测试

部署后记录以下指标，用于监控：

| 路线代码 | 优化前 | 优化后 | 目标 |
|---------|--------|--------|------|
| SA2 | 5-10秒 | ? | <500ms |
| G4202 | 5-10秒 | ? | <500ms |
| G5 | 5-10秒 | ? | <500ms |

填写"优化后"列，确认达到目标。

---

## 📞 需要帮助？

如果遇到问题：

1. **检查日志**：
   - API服务器终端输出
   - 浏览器Console（F12 → Console）
   - 浏览器Network（F12 → Network）

2. **查看详细文档**：
   - `IMPLEMENTATION_SUMMARY.md` - 完整实施总结
   - `docs/performance/PERFORMANCE_FIX_SUMMARY.md` - 技术细节
   - `docs/performance/edge_selector_performance_test.md` - 测试指南

3. **联系支持**：
   - 提供错误信息截图
   - 提供 Network 标签截图
   - 提供数据库查询执行计划

---

**部署完成后，你应该能感受到显著的性能提升！**

从"等待5-10秒"变为"几乎瞬时响应" 🎉
