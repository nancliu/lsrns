#!/usr/bin/env python3
"""
迁移测试脚本
用于验证数据迁移的正确性
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from shared.utilities.migration_tools import DataMigrationTool

class MigrationTester:
    """迁移测试类"""
    
    def __init__(self):
        self.test_results = []
        self.migration_tool = DataMigrationTool()
    
    def test_data_scanning(self) -> bool:
        """测试数据扫描功能"""
        print("测试数据扫描功能...")
        
        try:
            scan_result = self.migration_tool.scan_existing_data()
            
            # 验证扫描结果
            required_keys = ["run_folders", "accuracy_results", "taz_files", "network_files"]
            for key in required_keys:
                if key not in scan_result:
                    print(f"✗ 扫描结果缺少必要键: {key}")
                    return False
            
            print(f"✓ 发现 {len(scan_result['run_folders'])} 个run文件夹")
            print(f"✓ 发现 {len(scan_result['accuracy_results'])} 个精度分析结果")
            print(f"✓ 发现 {len(scan_result['taz_files'])} 个TAZ文件")
            print(f"✓ 发现 {len(scan_result['network_files'])} 个网络文件")
            
            self.test_results.append({
                "test": "data_scanning",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "details": scan_result
            })
            
            return True
            
        except Exception as e:
            print(f"✗ 数据扫描测试失败: {str(e)}")
            self.test_results.append({
                "test": "data_scanning",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            return False
    
    def test_case_migration(self) -> bool:
        """测试案例迁移功能"""
        print("测试案例迁移功能...")
        
        try:
            # 创建测试run文件夹
            test_run_folder = Path("test_run_folder")
            test_run_folder.mkdir(exist_ok=True)
            
            # 创建测试文件
            test_files = [
                "test_od.xml",
                "test_routes.xml",
                "test_simulation.sumocfg",
                "test_summary.xml"
            ]
            
            for file_name in test_files:
                test_file = test_run_folder / file_name
                test_file.write_text(f"# Test file: {file_name}")
            
            # 创建测试子文件夹
            test_e1_folder = test_run_folder / "e1_test"
            test_e1_folder.mkdir(exist_ok=True)
            (test_e1_folder / "test_e1.xml").write_text("# Test E1 file")
            
            # 创建测试run文件夹信息
            test_run_info = {
                "name": "test_run_folder",
                "path": str(test_run_folder),
                "created_at": datetime.now().isoformat(),
                "files": [
                    {
                        "name": file_name,
                        "path": str(test_run_folder / file_name),
                        "size": (test_run_folder / file_name).stat().st_size,
                        "type": "xml" if file_name.endswith(".xml") else "other"
                    }
                    for file_name in test_files
                ],
                "subfolders": [
                    {
                        "name": "e1_test",
                        "path": str(test_e1_folder),
                        "file_count": 1
                    }
                ]
            }
            
            # 执行迁移
            case_id = self.migration_tool.migrate_run_folder_to_case(test_run_info)
            
            # 验证迁移结果
            case_dir = Path("cases") / case_id
            if not case_dir.exists():
                print("✗ 案例目录未创建")
                return False
            
            metadata_file = case_dir / "metadata.json"
            if not metadata_file.exists():
                print("✗ 元数据文件未创建")
                return False
            
            # 验证目录结构
            required_dirs = ["config", "simulation", "analysis/accuracy"]
            for dir_name in required_dirs:
                if not (case_dir / dir_name).exists():
                    print(f"✗ 缺少必要目录: {dir_name}")
                    return False
            
            # 验证文件复制
            config_files = list((case_dir / "config").iterdir())
            if len(config_files) == 0:
                print("✗ 配置文件未复制")
                return False
            
            print(f"✓ 成功迁移测试案例: {case_id}")
            
            # 清理测试数据
            shutil.rmtree(test_run_folder)
            shutil.rmtree(case_dir)
            
            self.test_results.append({
                "test": "case_migration",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id
            })
            
            return True
            
        except Exception as e:
            print(f"✗ 案例迁移测试失败: {str(e)}")
            self.test_results.append({
                "test": "case_migration",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            return False
    
    def test_accuracy_migration(self) -> bool:
        """测试精度分析迁移功能"""
        print("测试精度分析迁移功能...")
        
        try:
            # 创建测试精度分析文件夹
            test_accuracy_folder = Path("test_accuracy_results")
            test_accuracy_folder.mkdir(exist_ok=True)
            
            # 创建测试文件
            test_files = [
                "accuracy_report.html",
                "accuracy_results.csv",
                "charts/accuracy_chart.png"
            ]
            
            for file_name in test_files:
                test_file = test_accuracy_folder / file_name
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text(f"# Test file: {file_name}")
            
            # 创建测试案例
            test_case_id = f"test_case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_case_dir = Path("cases") / test_case_id
            test_case_dir.mkdir(parents=True, exist_ok=True)
            (test_case_dir / "analysis" / "accuracy").mkdir(parents=True, exist_ok=True)
            
            # 创建测试案例元数据
            test_metadata = {
                "case_id": test_case_id,
                "case_name": "测试案例",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "time_range": {
                    "start": "2025/07/21 08:00:00",
                    "end": "2025/07/21 09:00:00"
                },
                "config": {},
                "status": "created",
                "description": "测试案例",
                "statistics": {},
                "files": {}
            }
            
            with open(test_case_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(test_metadata, f, ensure_ascii=False, indent=2)
            
            # 创建测试精度分析信息
            test_accuracy_info = {
                "name": "test_accuracy_results",
                "path": str(test_accuracy_folder),
                "created_at": datetime.now().isoformat(),
                "files": [
                    {
                        "name": file_name,
                        "path": str(test_accuracy_folder / file_name),
                        "size": (test_accuracy_folder / file_name).stat().st_size,
                        "type": "html" if file_name.endswith(".html") else "csv"
                    }
                    for file_name in test_files
                ],
                "subfolders": []
            }
            
            # 执行迁移
            result_case_id = self.migration_tool.migrate_accuracy_results(test_accuracy_info)
            
            # 验证迁移结果
            if result_case_id:
                accuracy_target_dir = Path("cases") / result_case_id / "analysis" / "accuracy" / "results"
                if accuracy_target_dir.exists():
                    print(f"✓ 成功迁移精度分析结果到案例: {result_case_id}")
                else:
                    print("✗ 精度分析结果未正确迁移")
                    return False
            else:
                print("✗ 精度分析迁移失败")
                return False
            
            # 清理测试数据
            shutil.rmtree(test_accuracy_folder)
            shutil.rmtree(test_case_dir)
            
            self.test_results.append({
                "test": "accuracy_migration",
                "status": "passed",
                "timestamp": datetime.now().isoformat(),
                "case_id": result_case_id
            })
            
            return True
            
        except Exception as e:
            print(f"✗ 精度分析迁移测试失败: {str(e)}")
            self.test_results.append({
                "test": "accuracy_migration",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            return False
    
    def test_report_generation(self) -> bool:
        """测试报告生成功能"""
        print("测试报告生成功能...")
        
        try:
            # 生成迁移报告
            report = self.migration_tool.generate_migration_report()
            
            # 验证报告格式
            required_keys = ["migration_timestamp", "total_migrations", "successful_migrations", "failed_migrations"]
            for key in required_keys:
                if key not in report:
                    print(f"✗ 报告缺少必要键: {key}")
                    return False
            
            # 保存报告
            report_file = "test_migration_report.json"
            self.migration_tool.save_migration_report(report, report_file)
            
            # 验证报告文件
            if Path(report_file).exists():
                print(f"✓ 成功生成迁移报告: {report_file}")
                
                # 清理测试文件
                Path(report_file).unlink()
                
                self.test_results.append({
                    "test": "report_generation",
                    "status": "passed",
                    "timestamp": datetime.now().isoformat(),
                    "report_file": report_file
                })
                
                return True
            else:
                print("✗ 报告文件未创建")
                return False
                
        except Exception as e:
            print(f"✗ 报告生成测试失败: {str(e)}")
            self.test_results.append({
                "test": "report_generation",
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("开始迁移测试...")
        print("=" * 50)
        
        tests = [
            ("数据扫描", self.test_data_scanning),
            ("案例迁移", self.test_case_migration),
            ("精度分析迁移", self.test_accuracy_migration),
            ("报告生成", self.test_report_generation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n测试: {test_name}")
            if test_func():
                passed_tests += 1
            print("-" * 30)
        
        # 生成测试报告
        test_report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": self.test_results
        }
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {test_report['success_rate']:.1f}%")
        
        # 保存测试报告
        with open("migration_test_report.json", "w", encoding="utf-8") as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        
        print(f"测试报告已保存到: migration_test_report.json")
        
        return test_report

def main():
    """主函数"""
    tester = MigrationTester()
    report = tester.run_all_tests()
    
    if report["success_rate"] == 100:
        print("\n🎉 所有测试通过! 迁移工具工作正常。")
    else:
        print(f"\n⚠️  有 {report['failed_tests']} 个测试失败，请检查迁移工具。")

if __name__ == "__main__":
    main() 