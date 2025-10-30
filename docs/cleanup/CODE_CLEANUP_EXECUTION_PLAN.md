# 代码清理执行计划

**生成日期**: 2025-10-30
**基于**: 自动化分析结果
**状态**: 准备执行

---

## 📊 分析摘要

### 发现的问题

**总计**: 22 个问题

| 类别 | 数量 | 优先级 | 状态 |
|------|------|--------|------|
| 待迁移: open_db_connection | 10 处 | P1 | 🔴 需要 |
| 需要重构的大型类 | 11 个 | P2 | 🟠 建议 |
| 已处理的废弃函数 | 1 个 | P0 | ✅ 完成 |

### 按严重程度分类

```
🔴 高优先级 (P0-P1):
  ├─ open_db_connection 使用 (10处)
  │   └─ 影响: 性能，连接池管理
  │   └─ 工作量: 2小时
  │
  └─ 批量仿真服务重构 (19 个方法 → 需拆分)
      └─ 影响: 可维护性，代码复杂度
      └─ 工作量: 4小时

🟠 中优先级 (P2-P3):
  ├─ 其他大型类重构 (10个, 平均12-15个方法)
  │   └─ 影响: 可维护性
  │   └─ 工作量: 15小时
  │
  └─ 文档更新和测试
      └─ 工作量: 3小时
```

---

## 🎯 阶段1: 立即行动 (P0 - 本周)

### 任务1.1: 迁移 open_db_connection (2小时)

**问题分析**:
```
发现10处使用:
  - api/services/base_service.py (2处)
  - api/services/control_strategy_service.py (2处)
  - shared/data_access/connection.py (多处)
  - ... 其他处
```

**工作步骤**:

```bash
# 1. 列出所有使用位置
grep -rn "open_db_connection" api/ shared/ --include="*.py" > /tmp/migration_list.txt

# 2. 逐个检查和修改
# 将所有 open_db_connection() 替换为 get_pooled_connection()

# 3. 验证修改
grep -rn "open_db_connection" api/ shared/ --include="*.py"
# 应该无结果或仅在 connection.py 的定义处
```

**代码示例**:

```python
# 文件: api/services/base_service.py
# 修改前:
from shared.data_access.connection import open_db_connection

def get_data(self):
    conn = open_db_connection()
    try:
        cursor = conn.cursor()
        # ...
    finally:
        conn.close()

# 修改后:
from shared.data_access.connection import get_pooled_connection

def get_data(self):
    conn = get_pooled_connection()
    try:
        cursor = conn.cursor()
        # ...
    finally:
        conn.close()  # 返回到连接池
```

**验证**:

```bash
# 运行测试确保功能正常
conda activate od_project
pytest tests/unit/services/

# 性能对比
# 预期: 数据库操作速度提升 5-10 倍
```

**检查清单**:

- [ ] 列出所有 10 处使用位置
- [ ] 逐一审查并修改
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 性能基准测试
- [ ] 更新文档

---

### 任务1.2: 标记废弃目录 (1小时)

**执行**:

```bash
# 使用清理脚本标记废弃代码
python cleanup_deprecated_code.py --fix

# 确认修改
ls -la sim_scripts/__init__.py
ls -la accuracy_analysis/__init__.py
```

**验证**:

```bash
# 查看是否正确创建了标记文件
cat sim_scripts/__init__.py
cat accuracy_analysis/__init__.py
```

**检查清单**:

- [ ] 为 sim_scripts/ 创建 __init__.py (已标记废弃)
- [ ] 为 accuracy_analysis/ 创建 __init__.py (已标记废弃)
- [ ] 文件内容正确包含废弃说明
- [ ] git 添加新文件

---

### 任务1.3: 文档更新 (1小时)

**更新清单**:

- [ ] 更新 CLAUDE.md
  - 添加"代码清理"部分
  - 更新"Common Pitfalls"
  - 添加迁移指南链接

- [ ] 创建迁移指南文档
  - open_db_connection → get_pooled_connection
  - 性能对比
  - 常见错误和解决方案

- [ ] 创建废弃代码列表
  - sim_scripts/ 的具体作用
  - 替代方案
  - 何时删除

**修改范围**: ~500 行文档

---

## 🏗️ 阶段2: 核心重构 (P1 - 下周)

### 任务2.1: 批量仿真服务重构 (4小时)

**当前状态**:
```
BatchOptimizationService
  - 19 个方法
  - 1193 行代码
  - 职责混杂 (创建、启动、获取进度、获取结果、分析时序)
```

**目标结构**:
```
BatchOptimizationService (核心)
  ├─ create_batch()
  ├─ start_batch()
  ├─ get_batch_progress()
  └─ get_batch_results() [改为调用助手类]

BatchResultsExtractor (新类)
  ├─ extract_simulation_metrics()
  ├─ extract_time_series_from_summary()
  └─ _parse_summary_xml()

BatchMetricsAggregator (新类)
  ├─ calculate_aggregated_metrics()
  ├─ aggregate_live_time_series()
  └─ read_or_update_cache()
```

**实施步骤**:

1. **创建新类** (1小时)
   - 创建 BatchResultsExtractor
   - 创建 BatchMetricsAggregator
   - 转移相应方法

2. **重构旧类** (1.5小时)
   - 从 BatchOptimizationService 删除转移的方法
   - 更新方法调用
   - 处理依赖关系

3. **测试验证** (1.5小时)
   - 单元测试各个新类
   - 集成测试完整流程
   - 性能对比

**代码量**:
```
BatchOptimizationService: 1193 → 400 行 (减少 66%)
BatchResultsExtractor: 新增 300 行
BatchMetricsAggregator: 新增 350 行
```

**检查清单**:

- [ ] 创建 BatchResultsExtractor 类
- [ ] 创建 BatchMetricsAggregator 类
- [ ] 转移相应方法
- [ ] 更新导入和调用
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能基准测试

---

### 任务2.2: 其他大型类重构分析 (2小时)

**需要重构的类**:

```
1. AccuracyAnalysis (21个方法) → 分为 3 个类
2. SimulationService (15个方法) → 分为 2 个类
3. StrategyInstanceService (14个方法) → 分为 2 个类
4. MechanismAnalysis (14个方法) → 分为 2 个类
5. PerformanceAnalyzer (15个方法) → 分为 2 个类
6. EdgeDataAnalysis (12个方法) → 可保持 1 个类
7. AccuracyAnalyzer (13个方法) → 分为 2 个类
8. ODProcessor (14个方法, 重复) → 重构
9. DataMigrationTool (12个方法) → 分为 2 个类
```

**预计工作量**:
- 分析: 2 小时
- 实施: 15 小时 (分散到2-3周)
- 测试: 10 小时

**优先次序**:
1. AccuracyAnalysis (最复杂)
2. SimulationService (影响业务)
3. 其他

**检查清单**:

- [ ] 完成需求分析
- [ ] 制定详细重构计划
- [ ] 创建任务卡
- [ ] 分配工期

---

## 📝 阶段3: 长期维护 (P3 - 下月)

### 任务3.1: 代码风格统一

```
目标:
  ├─ 所有类 < 300 行
  ├─ 所有方法 < 30 行
  ├─ 所有参数 < 5 个
  ├─ 所有嵌套 < 3 层
  └─ 类型注解 100%
```

### 任务3.2: 删除废弃代码

```
时间点: v1.0 发布
对象:
  ├─ sim_scripts/ 目录
  └─ accuracy_analysis/ 目录

流程:
  1. 备份旧代码 (git tag)
  2. 删除目录
  3. 更新文档
  4. 发布 v1.0
```

---

## 📊 工作量总结

### 第一阶段 (P0 - 本周)

| 任务 | 预估 | 实际 | 状态 |
|------|------|------|------|
| 迁移 open_db_connection | 2h | - | 🔴 |
| 标记废弃目录 | 1h | - | 🔴 |
| 文档更新 | 1h | - | 🔴 |
| **小计** | **4h** | - | |

### 第二阶段 (P1 - 下周)

| 任务 | 预估 | 实际 | 状态 |
|------|------|------|------|
| 批量仿真服务重构 | 4h | - | 🟠 |
| 其他大型类分析 | 2h | - | 🟠 |
| 单元测试完善 | 3h | - | 🟠 |
| 集成测试 | 2h | - | 🟠 |
| **小计** | **11h** | - | |

### 第三阶段 (P3 - 下月)

| 任务 | 预估 | 实际 | 状态 |
|------|------|------|------|
| 其他大型类重构 | 15h | - | 🟡 |
| 代码风格统一 | 5h | - | 🟡 |
| 文档完善 | 3h | - | 🟡 |
| **小计** | **23h** | - | |

### 总计

```
第一阶段 (P0):  4 小时 - 立即执行
第二阶段 (P1): 11 小时 - 本月完成
第三阶段 (P3): 23 小时 - 后续继续

总计: 38 小时 (~1 周全职开发)
```

---

## 🔄 执行流程

### 周一-周三 (第一阶段)

```
09:00 - 启动会议 (30分钟)
  ├─ 讨论清理计划
  ├─ 确认优先级
  └─ 分配任务

09:30 - 迁移 open_db_connection (2小时)
  ├─ 列出所有使用点
  ├─ 逐一修改
  └─ 验证测试

11:30 - 标记废弃目录 (1小时)
  ├─ 运行清理脚本
  ├─ 验证创建
  └─ git 提交

12:30 - 午休 (1小时)

13:30 - 文档更新 (1小时)
  ├─ 更新 CLAUDE.md
  ├─ 创建迁移指南
  └─ 创建废弃列表

14:30 - 代码审查 (1小时)
  ├─ peer review
  ├─ 修复问题
  └─ 最终确认

15:30 - 测试执行 (2小时)
  ├─ 单元测试运行
  ├─ 集成测试运行
  └─ 性能基准测试

17:30 - 总结会议 (30分钟)
  ├─ 进度回顾
  ├─ 问题讨论
  └─ 下周计划
```

### 周四-周五 (第二阶段开启)

```
开始批量仿真服务重构
  ├─ 创建新类
  ├─ 转移方法
  └─ 测试验证
```

---

## ✅ 成功标准

### 第一阶段

- [ ] 所有 10 处 open_db_connection 已迁移
- [ ] 废弃目录已正确标记
- [ ] 文档已更新
- [ ] 所有测试通过
- [ ] 代码通过审查

### 第二阶段

- [ ] BatchOptimizationService 已拆分
- [ ] 所有新类已创建
- [ ] 所有方法已转移
- [ ] 单元测试覆盖 > 90%
- [ ] 集成测试通过
- [ ] 性能无退化

### 第三阶段

- [ ] 所有大型类已重构
- [ ] 代码风格统一
- [ ] 类型注解 100%
- [ ] 文档完整准确

---

## 📞 沟通计划

### 日报

每天 17:30 发送进度报告:
```
【日期】2025-10-31
【完成】
  ✓ 迁移 6 处 open_db_connection
  ✓ 测试验证通过

【进行中】
  → 迁移剩余 4 处
  → 标记废弃目录

【阻碍】
  ❌ 无

【明天计划】
  - 完成迁移
  - 文档更新
  - 代码审查
```

### 周报

每周五 16:00 发送周报:
```
【周期】2025-10-27 ~ 2025-10-31
【本周目标】
  - P0 阶段全部完成

【完成情况】
  ✓ 迁移 open_db_connection
  ✓ 标记废弃目录
  ✓ 更新文档

【下周计划】
  - 批量仿真服务重构
  - 新类创建和测试
```

---

## 🚨 风险与缓解

### 风险1: 迁移后数据库性能下降

**风险**: 虽然预期性能提升，但可能因连接池配置不当导致性能下降

**缓解**:
- [ ] 对比迁移前后的性能指标
- [ ] 监控连接池使用情况
- [ ] 设置告警阈值
- [ ] 如有问题立即回滚

### 风险2: 遗漏的 open_db_connection 使用

**风险**: 某些地方使用了 open_db_connection 但没有被 grep 找到

**缓解**:
- [ ] 运行 pylint 检查
- [ ] 手动代码审查
- [ ] 完整的测试覆盖

### 风险3: 重构过程中引入 bug

**风险**: 拆分大型类时可能破坏现有功能

**缓解**:
- [ ] 编写详细的单元测试
- [ ] 保留旧代码进行对比测试
- [ ] 逐步重构 (不要一次性全部)
- [ ] 充分的代码审查

---

## 📅 时间表

```
2025-10-31 (周四)
  08:00 - 启动会议
  09:00 - 开始第一阶段

2025-11-03 (周一)
  09:00 - 第一阶段总结
  09:30 - 开始第二阶段

2025-11-06 (周四)
  09:00 - 第二阶段总结

2025-11-10 (周一)
  开始第三阶段

2025-11-30 (前)
  完成所有清理工作
```

---

## 📚 相关文档

- `BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md` - 详细分析
- `DEPRECATED_CODE_ANALYSIS.txt` - 自动化分析结果
- `cleanup_deprecated_code.py` - 清理脚本
- `CLAUDE.md` - 项目规范

---

**计划完成**: 2025-10-30
**执行负责人**: 待分配
**状态**: 🔴 准备执行
