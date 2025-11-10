# 手动测试控制方案操作指南

## 快速测试步骤

### 1. 准备测试环境

```bash
# 进入case目录
cd cases/case_20251110_130339/simulations

# 创建测试目录
mkdir sim_manual_test_vss
cd sim_manual_test_vss
```

### 2. 复制必要文件

```bash
# 复制基础配置（根据你的实际路径调整）
cp ../../config/sumocfg/simulation.sumocfg ./

# 复制控制文件
cp ../../../../control_data/plans/plan_morning_peak_g4202_vss_g4202k0k20_moderate_v1/control.add.xml ./

# 创建输出目录
mkdir output
```

### 3. 修改SUMO配置文件

打开 `simulation.sumocfg`，在 `<input>` 部分添加控制文件：

```xml
<configuration>
    <input>
        <net-file value="../../../../templates/network_files/sichuan202508v7.net.xml"/>
        <route-files value="../../config/routes/simulation.rou.xml"/>
        <!-- 添加控制文件 -->
        <additional-files value="control.add.xml"/>
    </input>

    <output>
        <summary-output value="output/summary.xml"/>
        <tripinfo-output value="output/tripinfo.xml"/>
    </output>

    <time>
        <begin value="27000"/>  <!-- 7:30 -->
        <end value="30600"/>    <!-- 8:30 -->
        <step-length value="1"/>
    </time>

    <processing>
        <ignore-route-errors value="true"/>
        <time-to-teleport value="300"/>
    </processing>
</configuration>
```

### 4. 运行SUMO仿真

#### 方式A：命令行运行（推荐）
```bash
# 确保SUMO在环境变量中
sumo -c simulation.sumocfg --seed 66

# 或者使用完整路径
%SUMO_HOME%\bin\sumo.exe -c simulation.sumocfg --seed 66
```

#### 方式B：GUI界面运行（可视化）
```bash
# 使用SUMO-GUI查看仿真过程
sumo-gui -c simulation.sumocfg --seed 66
```

### 5. 验证控制是否生效

#### 检查点1：查看仿真启动日志
```
Loading net-file from 'sichuan202508v7.net.xml' ... done
Loading additional-files from 'control.add.xml' ... done  ← 控制文件加载成功
Loading routes from 'simulation.rou.xml' ... done
```

#### 检查点2：验证VSS限速生效
在GUI模式下：
1. 找到edge `-8712`（东段第一个受控路段）
2. 观察车辆速度是否在以下时间点变化：
   - 7:30 (27000s) - 正常速度 120 km/h
   - 7:45 (27900s) - 降至 96 km/h
   - 8:00 (28800s) - 降至 90 km/h

#### 检查点3：查看输出结果
```bash
# 检查summary.xml
cat output/summary.xml | grep meanSpeed

# 应该看到平均速度在不同时间段的变化
```

### 6. 测试其他控制策略

#### TEC流量控制方案
```bash
# 复制TEC方案
cp ../../../../control_data/plans/plan_morning_peak_g4202_tec_k0_mild_v1/control.add.xml ./control_tec.add.xml

# 修改sumocfg使用TEC控制
<additional-files value="control_tec.add.xml"/>
```

#### 复合策略方案
```bash
# 复制VSS+TEC复合方案
cp ../../../../control_data/plans/plan_morning_peak_g4202_vss_tec_g4202k40k60_moderate_v1/control.add.xml ./control_composite.add.xml

# 修改sumocfg使用复合控制
<additional-files value="control_composite.add.xml"/>
```

## 常见问题排查

### 问题1：找不到网络文件
**错误**: `Error: Could not load net-file`
**解决**: 检查net-file路径，使用绝对路径：
```xml
<net-file value="D:/projects/OD_SIM/templates/network_files/sichuan202508v7.net.xml"/>
```

### 问题2：控制文件无效
**错误**: `Error: Invalid additional file`
**解决**: 检查control.add.xml格式，确保edge ID存在

### 问题3：仿真运行缓慢
**解决**:
- 减少仿真时长（如30分钟）
- 减少输出项（去掉tripinfo等）
- 使用命令行模式而非GUI

## 预期结果

成功运行后，您应该看到：
1. ✅ 仿真正常完成，无错误
2. ✅ output目录下生成summary.xml等文件
3. ✅ 控制策略在指定时间点生效
4. ✅ 车辆行为符合控制参数（速度限制/流量控制）

## 批量测试脚本

如果单个测试成功，可以使用脚本批量测试：

```python
import os
import subprocess

# 测试方案列表
test_plans = [
    "plan_morning_peak_g4202_vss_g4202k0k20_moderate_v1",
    "plan_morning_peak_g4202_tec_k0_mild_v1",
    "plan_morning_peak_g4202_vss_tec_g4202k40k60_moderate_v1"
]

for plan in test_plans:
    print(f"Testing {plan}...")
    # 创建目录，复制文件，运行仿真...
    cmd = f"sumo -c simulation.sumocfg --seed 66"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f"  ✓ {plan} passed")
    else:
        print(f"  ✗ {plan} failed")
```

## 测试报告模板

```markdown
## 控制方案测试报告

**方案ID**: plan_morning_peak_g4202_vss_g4202k0k20_moderate_v1
**测试时间**: 2024-11-10 13:30
**测试人员**: [您的名字]

### 测试结果
- [ ] 控制文件加载成功
- [ ] 仿真正常运行
- [ ] VSS限速在指定时间生效
- [ ] 输出文件正常生成
- [ ] 无错误或警告

### 性能指标
- 仿真耗时: XX秒
- 车辆完成率: XX%
- 平均速度变化: 120km/h → 90km/h

### 备注
[任何观察到的问题或建议]
```