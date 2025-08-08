# TAZ文件修复工具

## 问题描述

在TAZ_5.add.xml文件中存在重复的TAZ ID定义，导致SUMO在加载文件时报错：

```
Error: Another edge with the id 'G000551044001410010-sink' exists.
Error: Another edge with the id 'G000551044001420010-sink' exists.
...
```

## 解决方案

本工具集提供了一系列脚本，用于分析和修复TAZ_5.add.xml文件中的重复TAZ定义问题。

### 工具列表

1. `analyze_duplicate_taz.py` - 分析TAZ文件中的重复ID，并输出详细信息
2. `fix_duplicate_taz.py` - 修复TAZ文件中的重复定义，生成新的TAZ文件，并更新DLLtest2025_6_3.py中的引用
3. `fix_taz.bat` - Windows批处理脚本，自动运行上述所有Python脚本

### 修复逻辑

修复过程如下：

1. 分析TAZ_5.add.xml文件，找出所有重复的TAZ ID
2. 对于每个重复的TAZ ID，根据taz_validation_results.csv中的数据选择保留哪个定义：
   - 优先选择source和sink状态与验证结果匹配的TAZ定义
   - 如果没有匹配的，则选择第一个定义
3. 确保处理后的TAZ ID是唯一的，即使存在完全相同的TAZ数据也只保留一个
4. 生成新的TAZ文件，命名为TAZ_5_fixed.add.xml
5. 更新DLLtest2025_6_3.py中的TAZ文件引用，将TAZ_5.add.xml替换为TAZ_5_fixed.add.xml

## 使用方法

### Windows系统

1. 打开命令提示符或PowerShell
2. 切换到taz_analysis目录
3. 运行fix_taz.bat批处理脚本

```
cd taz_analysis
fix_taz.bat
```

### 手动运行Python脚本

如果需要单独运行某个脚本，可以使用以下命令：

```
python analyze_duplicate_taz.py  # 分析重复TAZ ID
python fix_duplicate_taz.py      # 修复TAZ文件并更新DLLtest2025_6_3.py
```

## 输出文件

- `TAZ_5_fixed.add.xml` - 修复后的TAZ文件，保存在sim_scripts目录下
- DLLtest2025_6_3.py中的TAZ文件引用已更新为TAZ_5_fixed.add.xml

## 注意事项

- 运行脚本前，请确保已安装Python 3.6或更高版本
- 修复过程不会修改原始的TAZ_5.add.xml文件
- 修复后的TAZ文件中，每个TAZ ID都是唯一的，不存在重复定义
- 如果需要恢复原始设置，只需将DLLtest2025_6_3.py中的TAZ_5_fixed.add.xml改回TAZ_5.add.xml即可 