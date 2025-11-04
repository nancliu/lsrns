# Batch Creation Logging - Quick Reference

**When**: Click "Create Batch" button
**Where**: Console output (terminal/IDE console)
**What**: Complete batch information summary

---

## Information Logged

### Basic Info
```
批次ID:       batch_20251104_123456_abc
案例ID:       case_20251025_001
状态:         pending
创建时间:      2025-11-04T12:34:56.789012
```

### Plans
```
方案数量:      3
方案列表:
  [1] baseline_plan - 基准方案（无管控）
  [2] plan_001 - 可变限速方案A
  [3] plan_002 - 流量计费方案B
```

### Seed Configuration (Phase 5)
```
num_seeds:     5              # Seeds per plan
base_seed:     66             # Starting seed
Seed sequence: [66,67,68,69,70]
Total Tasks:   15             # 3 plans × 5 seeds
```

### Output Configuration (Phase 3)
```
tripinfo_xml:  True/False     # Vehicle trip information
vehroute:      True/False     # Vehicle routes
netstate:      True/False     # Network state
fcd:           True/False     # Floating car data
emission:      True/False     # Emissions data
edgedata_xml:  True/False     # Road segment stats
edges_attr:    True/False     # Preserve edges in EdgeData
```

### Simulation Duration (Phase 1) - Optional
```
Hours:         4
Minutes:       0
Total Minutes: 240
```

### Directory Path
```
D:\projects\OD_SIM\cases\case_20251025_001\simulations\plan_opti\batch_20251104_123456_abc
```

---

## Why This Matters

✅ **Verify Batch Creation** - Confirm batch was created with correct parameters
✅ **Debug Issues** - Check if wrong values were submitted
✅ **Track Batches** - Identify batch ID for result retrieval
✅ **Monitor Execution** - See total tasks to monitor progress
✅ **Validate Configuration** - Ensure output options are correct

---

## Key Fields to Check

| Field | Why Important | Normal Range |
|-------|--------------|--------------|
| batch_id | Unique identifier | Timestamp-based |
| plan_ids | Which plans testing | Min 2 (baseline + control) |
| num_seeds | Monte Carlo iterations | 1-100 |
| base_seed | Seed starting value | Any positive integer |
| total_tasks | Expected execution count | plans × seeds |
| output_tripinfo | Detailed vehicle data | Usually True |
| edgedata_xml | Road segment stats | Usually False (slower) |

---

## Example Output

```
================================================================================
✓ 批次创建成功 (Batch Created Successfully)
================================================================================

【批次基础信息 (Batch Basic Info)】
  批次ID (Batch ID):           batch_20251104_143052_f8d2c
  案例ID (Case ID):            case_20251025_001
  批次状态 (Status):            pending
  创建时间 (Created At):        2025-11-04T14:30:52.123456

【方案配置 (Plans Configuration)】
  方案数量 (Number of Plans):   2
  方案ID列表 (Plan IDs):
    [1] baseline_plan - 基准方案（无管控）
    [2] plan_001 - VSS可变限速方案

【种子配置 (Seed Configuration - Phase 5)】
  每方案种子数 (num_seeds):    3
  基础种子值 (base_seed):       66
  种子序列 (seed_sequence):     [66, 67, 68]
  总任务数 (Total Tasks):       6 (2 plans × 3 seeds)

【输出配置 (Output Configuration - Phase 3)】
  输出级别 (Output Level):      standard
  tripinfo输出 (tripinfo_xml):  True
  vehroute输出 (vehroute):      False
  netstate输出 (netstate):      False
  FCD输出 (fcd):                False
  排放数据输出 (emission):      False
  edgedata输出 (edgedata_xml):  False
  edgedata保留edges属性:        False

【批次目录 (Batch Directory)】
  D:\projects\OD_SIM\cases\case_20251025_001\simulations\plan_opti\batch_20251104_143052_f8d2c
================================================================================
```

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| No logging output | Is API server running? Check console logs enabled? |
| Wrong batch_id | Verify batch directory created at shown path |
| Missing plans | Confirm baseline_plan auto-added to list |
| Wrong seed values | Check form submission in browser DevTools |
| No output config | Verify output_config defaults applied correctly |

---

**For detailed information**: See `BATCH_CREATION_CONSOLE_LOGGING.md`
