"""
生成研究绩效评价图表
自动生成所有需要的数据可视化图表
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
output_dir = Path("docs/research_performance_evaluation/charts")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("开始生成研究绩效评价图表")
print("=" * 60)


# 图表1: 事件类型分布饼图
def generate_event_type_distribution():
    print("\n[1/8] 生成事件类型分布饼图...")

    labels = ['交通事故', '交通管制', '交通阻塞', '地质灾害', '车辆故障', '恶劣天气', '其他']
    sizes = [150, 80, 80, 30, 30, 30, 49]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BDC3C7']
    explode = (0.05, 0, 0, 0, 0, 0, 0)  # 突出交通事故

    plt.figure(figsize=(12, 9))
    wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors,
                                         autopct='%1.1f%%', startangle=90,
                                         explode=explode,
                                         textprops={'fontsize': 14, 'fontweight': 'bold'})

    # 美化百分比文字
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(13)
        autotext.set_weight('bold')

    plt.title('场景库事件类型分布 (总计:449场景)',
              fontsize=20, fontweight='bold', pad=20)
    plt.axis('equal')

    # 添加图例
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=12)

    plt.savefig(output_dir / '01_event_type_distribution.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 01_event_type_distribution.png")


# 图表2: 控制策略分布柱状图
def generate_strategy_distribution():
    print("\n[2/8] 生成控制策略分布柱状图...")

    strategies = ['NO_CONTROL\n(基线)', 'VSS\n(可变限速)',
                  'TEC\n(收费站控制)', 'DHS\n(动态硬路肩)']
    counts = [113, 112, 112, 112]
    colors = ['#95A5A6', '#3498DB', '#E74C3C', '#2ECC71']

    plt.figure(figsize=(14, 8))
    bars = plt.bar(strategies, counts, color=colors, edgecolor='black',
                    linewidth=2, width=0.6)

    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                 f'{int(height)}',
                 ha='center', va='bottom', fontsize=18, fontweight='bold')

    plt.title('场景库控制策略分布', fontsize=22, fontweight='bold', pad=20)
    plt.ylabel('场景数量', fontsize=16, fontweight='bold')
    plt.ylim(0, 130)
    plt.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)
    plt.xticks(fontsize=14, fontweight='bold')
    plt.yticks(fontsize=13)

    # 添加平均线
    avg = np.mean(counts)
    plt.axhline(y=avg, color='#E67E22', linestyle='--', linewidth=2,
                label=f'平均值: {avg:.1f}')
    plt.legend(fontsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / '02_strategy_distribution.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 02_strategy_distribution.png")


# 图表3: 效率提升对比图
def generate_efficiency_comparison():
    print("\n[3/8] 生成效率提升对比图...")

    categories = ['单场景生成\n(分钟)', '18场景批量\n(分钟)', '错误率\n(%)']
    traditional = [150, 2700, 15]
    our_method = [0.4, 9, 1]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))
    bars1 = ax.bar(x - width/2, traditional, width, label='传统方法',
                    color='#E74C3C', edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, our_method, width, label='本项目方法',
                    color='#2ECC71', edgecolor='black', linewidth=1.5)

    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height >= 100:
                label = f'{int(height)}'
            else:
                label = f'{height:.1f}'
            ax.text(bar.get_x() + bar.get_width()/2., height * 1.05,
                    label, ha='center', va='bottom',
                    fontsize=13, fontweight='bold')

    ax.set_title('效率提升对比', fontsize=22, fontweight='bold', pad=20)
    ax.set_ylabel('数值', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=14, fontweight='bold')
    ax.legend(fontsize=14, loc='upper left')
    ax.set_yscale('log')  # 对数刻度
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # 添加提升幅度标注
    improvements = ['↓99.7%', '↓99.7%', '↓93%']
    for i, imp in enumerate(improvements):
        ax.text(i, max(traditional[i], our_method[i]) * 2, imp,
                ha='center', va='bottom', fontsize=14, fontweight='bold',
                color='#27AE60', bbox=dict(boxstyle='round',
                facecolor='#E8F8F5', edgecolor='#27AE60', linewidth=2))

    plt.tight_layout()
    plt.savefig(output_dir / '03_efficiency_comparison.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 03_efficiency_comparison.png")


# 图表4: 多策略对比雷达图
def generate_strategy_radar():
    print("\n[4/8] 生成多策略对比雷达图...")

    categories = ['平均速度\n提升(%)', '拥堵时间\n减少(%)',
                  '车辆完成率\n提升(%)', '排放减少(%)',
                  '部署成本\n(低=好)']
    N = len(categories)

    # 数据(归一化到0-100)
    vss_values = [12.5, 15, 3, 8, 80]  # 成本反向:100-20=80
    tec_values = [16.2, 20, 5, 10, 50]
    dhs_values = [8.7, 10, 2, 6, 70]

    # 创建角度
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    vss_values += vss_values[:1]
    tec_values += tec_values[:1]
    dhs_values += dhs_values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(polar=True))

    # 绘制3个策略
    ax.plot(angles, vss_values, 'o-', linewidth=3, label='VSS',
            color='#3498DB', markersize=8)
    ax.fill(angles, vss_values, alpha=0.25, color='#3498DB')

    ax.plot(angles, tec_values, 'o-', linewidth=3, label='TEC',
            color='#E74C3C', markersize=8)
    ax.fill(angles, tec_values, alpha=0.25, color='#E74C3C')

    ax.plot(angles, dhs_values, 'o-', linewidth=3, label='DHS',
            color='#2ECC71', markersize=8)
    ax.fill(angles, dhs_values, alpha=0.25, color='#2ECC71')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=13, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.set_title('scenario_12547 多策略效果对比\n(交通事故场景)',
                 fontsize=20, fontweight='bold', pad=30)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15),
              fontsize=14, frameon=True, shadow=True)
    ax.grid(True, linewidth=1.5, alpha=0.3)

    # 添加刻度线
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=11)

    plt.tight_layout()
    plt.savefig(output_dir / '04_strategy_radar.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 04_strategy_radar.png")


# 图表5: 场景时长分布直方图
def generate_duration_distribution():
    print("\n[5/8] 生成场景时长分布直方图...")

    duration_ranges = ['0.5-1小时', '1-1.5小时', '1.5-2小时',
                       '2-2.5小时', '2.5-3小时']
    percentages = [35, 25, 17, 13, 10]
    colors = ['#3498DB', '#2ECC71', '#F39C12', '#E74C3C', '#9B59B6']

    plt.figure(figsize=(14, 8))
    bars = plt.bar(duration_ranges, percentages, color=colors,
                    edgecolor='black', linewidth=2, width=0.6)

    # 添加百分比标签
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                 f'{pct}%',
                 ha='center', va='bottom', fontsize=16, fontweight='bold')

    plt.title('场景事件时长分布', fontsize=22, fontweight='bold', pad=20)
    plt.xlabel('事件时长', fontsize=16, fontweight='bold')
    plt.ylabel('占比 (%)', fontsize=16, fontweight='bold')
    plt.ylim(0, 42)
    plt.xticks(fontsize=13, fontweight='bold')
    plt.yticks(fontsize=13)
    plt.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)

    # 添加最优区域标注
    plt.axvspan(0.5, 2.5, alpha=0.1, color='green')
    plt.text(1.5, 38, '最优时长区域\n(1-2小时: 42%)',
             ha='center', fontsize=13, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='#E8F8F5',
                      edgecolor='#27AE60', linewidth=2))

    plt.tight_layout()
    plt.savefig(output_dir / '05_duration_distribution.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 05_duration_distribution.png")


# 图表6: 成效雷达图(多维度)
def generate_achievement_radar():
    print("\n[6/8] 生成成效雷达图...")

    categories = ['规模化', '效率提升', '成本节约',
                  '质量保证', '覆盖率', '可追溯性']
    values = [95, 99, 96, 93, 90, 100]

    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(polar=True))
    ax.plot(angles, values, 'o-', linewidth=4, color='#2ECC71', markersize=10)
    ax.fill(angles, values, alpha=0.35, color='#2ECC71')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=15, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.set_title('项目成效多维度评估', fontsize=22, fontweight='bold', pad=40)
    ax.grid(True, linewidth=1.5, alpha=0.3)

    # 设置刻度
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=12)

    # 添加数值标签
    for angle, value, category in zip(angles[:-1], values[:-1], categories):
        ax.text(angle, value + 7, f'{value}', ha='center', va='center',
                fontsize=14, fontweight='bold', color='#2C3E50',
                bbox=dict(boxstyle='circle', facecolor='white',
                         edgecolor='#2ECC71', linewidth=2))

    plt.tight_layout()
    plt.savefig(output_dir / '06_achievement_radar.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 06_achievement_radar.png")


# 图表7: 覆盖率对比柱状图
def generate_coverage_comparison():
    print("\n[7/8] 生成覆盖率对比图...")

    event_types = ['交通事故', '交通管制', '交通阻塞',
                   '地质灾害', '车辆故障', '恶劣天气']
    traditional_coverage = [1.1, 2.2, 7.1, 12.5, 14.3, 16.7]
    our_coverage = [57.5, 89.9, 100, 100, 100, 100]

    x = np.arange(len(event_types))
    width = 0.35

    fig, ax = plt.subplots(figsize=(15, 8))
    bars1 = ax.bar(x - width/2, traditional_coverage, width,
                    label='传统方法', color='#E74C3C',
                    edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, our_coverage, width,
                    label='本项目方法', color='#2ECC71',
                    edgecolor='black', linewidth=1.5)

    # 添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.set_title('事件类型覆盖率对比', fontsize=22, fontweight='bold', pad=20)
    ax.set_ylabel('覆盖率 (%)', fontsize=16, fontweight='bold')
    ax.set_xlabel('事件类型', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(event_types, fontsize=13, fontweight='bold', rotation=15)
    ax.legend(fontsize=14, loc='upper left')
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)

    # 添加100%参考线
    ax.axhline(y=100, color='#95A5A6', linestyle='--',
               linewidth=2, label='完全覆盖')

    plt.tight_layout()
    plt.savefig(output_dir / '07_coverage_comparison.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 07_coverage_comparison.png")


# 图表8: 综合成效对比表(可视化表格)
def generate_summary_table():
    print("\n[8/8] 生成综合成效对比表...")

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')

    # 表格数据
    table_data = [
        ['成效维度', '核心指标', '传统方法', '本项目方法', '提升幅度'],
        ['规模化', '场景库规模', '<10个', '449个', '+4390%'],
        ['效率', '生成效率', '2-3h/场景', '0.4min/场景', '+99.7%'],
        ['成本', '成本节约', '--', '96%节约', '7.4万/100场景'],
        ['质量', '错误率', '~15%', '<1%', '-93%'],
        ['覆盖率', '事件覆盖', '<20%', '>90%', '+4.5×'],
        ['知识管理', '可追溯性', '无', '三级元数据', '新增能力']
    ]

    # 创建表格
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.15, 0.18, 0.22, 0.22, 0.23])

    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 3)

    # 设置表头样式
    for i in range(5):
        cell = table[(0, i)]
        cell.set_facecolor('#2C3E50')
        cell.set_text_props(weight='bold', color='white', fontsize=15)

    # 设置数据行样式
    for i in range(1, 7):
        for j in range(5):
            cell = table[(i, j)]
            if i % 2 == 0:
                cell.set_facecolor('#ECF0F1')
            else:
                cell.set_facecolor('#FFFFFF')
            cell.set_text_props(fontsize=13, weight='bold')

            # 高亮提升幅度列
            if j == 4:
                cell.set_facecolor('#E8F8F5')
                cell.set_text_props(color='#27AE60', weight='bold', fontsize=14)

    # 添加边框
    for key, cell in table.get_celld().items():
        cell.set_linewidth(2)
        cell.set_edgecolor('#34495E')

    plt.title('项目成效综合对比表', fontsize=24, fontweight='bold', pad=20)

    plt.savefig(output_dir / '08_summary_table.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ 保存: 08_summary_table.png")


# 主函数
def main():
    """生成所有图表"""
    try:
        generate_event_type_distribution()
        generate_strategy_distribution()
        generate_efficiency_comparison()
        generate_strategy_radar()
        generate_duration_distribution()
        generate_achievement_radar()
        generate_coverage_comparison()
        generate_summary_table()

        print("\n" + "=" * 60)
        print("✓ 所有图表生成完成!")
        print(f"✓ 输出目录: {output_dir.absolute()}")
        print("=" * 60)

        # 列出生成的文件
        print("\n生成的文件清单:")
        for i, filename in enumerate(sorted(output_dir.glob("*.png")), 1):
            print(f"  {i}. {filename.name}")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
