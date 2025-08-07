"""
简化版精度分析工具测试脚本
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加精度分析工具路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .analyzer import AccuracyAnalyzer
    from .utils import log_analysis_progress
    
    def simple_test():
        """简单测试精度分析器"""
        
        print("=" * 60)
        print("仿真精度分析工具简单测试")
        print("=" * 60)
        
        # 测试用例：使用现有的run文件夹
        run_folder = r"D:\projects\OD生成脚本\OD生成脚本\sim_scripts\run_20250804_152456"
        
        if not os.path.exists(run_folder):
            print(f"测试文件夹不存在: {run_folder}")
            print("请确保已经运行过仿真并生成了相应的文件夹")
            return False
        
        try:
            # 创建精度分析器
            print(f"初始化精度分析器...")
            analyzer = AccuracyAnalyzer(run_folder)
            
            # 显示分析摘要
            summary = analyzer.get_analysis_summary()
            print(f"\n分析摘要:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
            
            # 执行精度分析
            print(f"\n开始执行精度分析...")
            result = analyzer.analyze_accuracy()
            
            if result['success']:
                print(f"OK 精度分析完成!")
                print(f"结果文件夹: {result['output_folder']}")
                
                # 显示主要指标
                overall_metrics = result.get('accuracy_summary', {}).get('overall_metrics', {})
                print(f"\n主要精度指标:")
                print(f"  MAPE: {overall_metrics.get('mape', 0):.2f}%")
                print(f"  GEH平均值: {overall_metrics.get('geh_mean', 0):.2f}")
                print(f"  GEH合格率: {overall_metrics.get('geh_pass_rate', 0):.1f}%")
                print(f"  样本数量: {overall_metrics.get('sample_size', 0)}")
                
                # 显示生成的文件
                report_files = result.get('report_files', {})
                print(f"\n生成的报告文件:")
                for file_type, file_path in report_files.items():
                    if file_path and os.path.exists(file_path):
                        print(f"  OK {file_type}: {file_path}")
                    else:
                        print(f"  NG {file_type}: 文件未生成")
                
                return True
                
            else:
                print(f"NG 精度分析失败: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"NG 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        success = simple_test()
        if success:
            print("\n测试通过！精度分析工具已准备就绪。")
        else:
            print("\n测试失败，请检查错误信息并修复问题。")
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保精度分析工具的所有模块都已正确安装。")
    sys.exit(1)