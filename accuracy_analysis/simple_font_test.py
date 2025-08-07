"""
简单的字体修复验证脚本
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from .report_generator import ReportGenerator

def simple_font_test():
    """简单的字体修复验证"""
    
    print("开始简单的字体修复验证...")
    
    # 创建测试数据
    np.random.seed(42)
    n_samples = 30
    test_data = pd.DataFrame({
        'gantry_id': ['G001', 'G002', 'G003'] * 10,
        'interval_start': list(range(0, n_samples)),
        'sim_flow': np.random.randint(50, 150, n_samples),
        'obs_flow': np.random.randint(45, 140, n_samples)
    })
    
    # 计算MAPE和GEH
    test_data['mape'] = np.abs((test_data['sim_flow'] - test_data['obs_flow']) / test_data['obs_flow']) * 100
    test_data['geh'] = np.sqrt(2 * (test_data['sim_flow'] - test_data['obs_flow'])**2 / (test_data['sim_flow'] + test_data['obs_flow']))
    
    # 创建输出文件夹
    output_folder = f'simple_font_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    os.makedirs(output_folder, exist_ok=True)
    
    # 创建报告生成器
    report_gen = ReportGenerator(output_folder)
    
    print(f"生成测试图表到: {output_folder}")
    
    # 生成MAPE分布图
    mape_chart = report_gen._generate_mape_distribution_chart(test_data)
    if mape_chart:
        print(f"✓ MAPE分布图生成成功: {os.path.basename(mape_chart)}")
    
    # 生成GEH分布图
    geh_chart = report_gen._generate_geh_distribution_chart(test_data)
    if geh_chart:
        print(f"✓ GEH分布图生成成功: {os.path.basename(geh_chart)}")
    
    # 生成散点图
    scatter_chart = report_gen._generate_scatter_plot(test_data)
    if scatter_chart:
        print(f"✓ 散点图生成成功: {os.path.basename(scatter_chart)}")
    
    print(f"\n请检查 {output_folder}/charts/ 文件夹中的PNG文件")
    print("中文字体现在应该正常显示。")
    
    return output_folder

if __name__ == "__main__":
    result_folder = simple_font_test()
    print(f"\n测试完成，结果保存在: {result_folder}")