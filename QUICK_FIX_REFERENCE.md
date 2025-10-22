# 快速修复参考卡片

## 问题：路段代码下拉框慢（5-10秒）

### ⚡ 快速部署（3步）

```powershell
# 1. 应用数据库索引
.\database\apply_migration.ps1 -MigrationFile "004_add_edge_query_indexes.sql"

# 2. 重启API服务器
.\start_api.ps1

# 3. 测试（浏览器访问）
# http://localhost:8000/control/templates.html
# 选择路线 → 应在<500ms内填充路段
```

### ✅ 验证成功

**浏览器DevTools → Network标签**：
- ✅ 只有1个API调用：`/api/v1/control/edges/sections?route_code=XXX`
- ❌ 没有：`/api/v1/control/edges/query`
- ✅ 响应时间 < 500ms

**方向下拉框**：
- 选择 SA2 或 G4202 → 只显示"顺时针/逆时针"
- 选择其他路线 → 只显示"上行/下行"

### 📊 性能对比

| 操作 | 优化前 | 优化后 |
|------|--------|--------|
| 选择路线 | 5-10秒 | <500ms |
| 提升倍数 | - | **10-20x** |

### 🔧 故障排查

**如果还是慢**：

1. **检查索引是否创建**：
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename = 'sim_network_edges';
   ```
   应该看到 `idx_sim_network_edges_route_section`

2. **检查浏览器缓存**：
   - 按 Ctrl+Shift+R 强制刷新
   - 清空缓存后再试

3. **检查API是否调用了两次**：
   - 打开Network标签
   - 如果看到 `/api/v1/control/edges/query` 说明前端代码没更新
   - 重启API服务器

### 🔙 紧急回滚

```powershell
# 回滚前端
git checkout HEAD~1 -- frontend/control/js/edge_selector_embedded.js

# 回滚数据库（如需要）
psql -h 10.149.235.123 -U username -d sdzg -c "
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_section;
"
```

### 📖 完整文档

- 详细分析：`docs/performance/PERFORMANCE_FIX_SUMMARY.md`
- 测试指南：`docs/performance/edge_selector_performance_test.md`
- 路网特征：`docs/data_in_db/road_network_topology.md`
- 完整总结：`IMPLEMENTATION_SUMMARY.md`

---

**修复日期**: 2025-10-22
**性能提升**: 10-20倍
**用户体验**: 从"令人沮丧"到"近乎瞬时"
