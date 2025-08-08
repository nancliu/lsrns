"""
数据迁移工具
用于将现有的sim_scripts目录结构迁移到新的案例管理系统
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET

class DataMigrationTool:
    """数据迁移工具类"""
    
    def __init__(self, source_dir: str = "sim_scripts", target_dir: str = "cases"):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.migration_log = []
        
    def scan_existing_data(self) -> Dict[str, Any]:
        """
        扫描现有数据结构
        
        Returns:
            扫描结果
        """
        print("扫描现有数据结构...")
        
        scan_result = {
            "run_folders": [],
            "accuracy_results": [],
            "taz_files": [],
            "network_files": [],
            "config_files": [],
            "e1_data": []
        }
        
        # 扫描run_*文件夹
        for item in self.source_dir.iterdir():
            if item.is_dir() and item.name.startswith("run_"):
                run_info = self._analyze_run_folder(item)
                scan_result["run_folders"].append(run_info)
        
        # 扫描accuracy_analysis文件夹
        accuracy_dir = self.source_dir / "accuracy_analysis"
        if accuracy_dir.exists():
            for item in accuracy_dir.iterdir():
                if item.is_dir() and item.name.startswith("accuracy_results_"):
                    accuracy_info = self._analyze_accuracy_folder(item)
                    scan_result["accuracy_results"].append(accuracy_info)
        
        # 扫描TAZ文件
        for taz_file in self.source_dir.glob("TAZ_*.add.xml"):
            scan_result["taz_files"].append({
                "name": taz_file.name,
                "path": str(taz_file),
                "size": taz_file.stat().st_size
            })
        
        # 扫描网络文件
        for net_file in self.source_dir.glob("sichuan*.net.xml"):
            scan_result["network_files"].append({
                "name": net_file.name,
                "path": str(net_file),
                "size": net_file.stat().st_size
            })
        
        # 扫描配置文件
        for config_file in self.source_dir.glob("*.json"):
            scan_result["config_files"].append({
                "name": config_file.name,
                "path": str(config_file),
                "size": config_file.stat().st_size
            })
        
        # 扫描E1数据
        e1_dir = self.source_dir / "e1"
        if e1_dir.exists():
            for e1_file in e1_dir.rglob("*.xml"):
                scan_result["e1_data"].append({
                    "name": e1_file.name,
                    "path": str(e1_file),
                    "size": e1_file.stat().st_size
                })
        
        return scan_result
    
    def _analyze_run_folder(self, run_folder: Path) -> Dict[str, Any]:
        """分析run文件夹"""
        run_info = {
            "name": run_folder.name,
            "path": str(run_folder),
            "created_at": datetime.fromtimestamp(run_folder.stat().st_ctime).isoformat(),
            "files": [],
            "subfolders": []
        }
        
        # 分析文件
        for file in run_folder.iterdir():
            if file.is_file():
                file_info = {
                    "name": file.name,
                    "path": str(file),
                    "size": file.stat().st_size,
                    "type": self._get_file_type(file.name)
                }
                run_info["files"].append(file_info)
            elif file.is_dir():
                folder_info = {
                    "name": file.name,
                    "path": str(file),
                    "file_count": len(list(file.rglob("*")))
                }
                run_info["subfolders"].append(folder_info)
        
        return run_info
    
    def _analyze_accuracy_folder(self, accuracy_folder: Path) -> Dict[str, Any]:
        """分析精度分析文件夹"""
        accuracy_info = {
            "name": accuracy_folder.name,
            "path": str(accuracy_folder),
            "created_at": datetime.fromtimestamp(accuracy_folder.stat().st_ctime).isoformat(),
            "files": [],
            "subfolders": []
        }
        
        # 分析文件
        for file in accuracy_folder.iterdir():
            if file.is_file():
                file_info = {
                    "name": file.name,
                    "path": str(file),
                    "size": file.stat().st_size,
                    "type": self._get_file_type(file.name)
                }
                accuracy_info["files"].append(file_info)
            elif file.is_dir():
                folder_info = {
                    "name": file.name,
                    "path": str(file),
                    "file_count": len(list(file.rglob("*")))
                }
                accuracy_info["subfolders"].append(folder_info)
        
        return accuracy_info
    
    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        if ext == ".xml":
            return "xml"
        elif ext == ".json":
            return "json"
        elif ext == ".csv":
            return "csv"
        elif ext == ".sumocfg":
            return "sumo_config"
        else:
            return "other"
    
    def migrate_run_folder_to_case(self, run_folder_info: Dict[str, Any]) -> str:
        """
        将run文件夹迁移为案例
        
        Args:
            run_folder_info: run文件夹信息
            
        Returns:
            新案例ID
        """
        run_folder_path = Path(run_folder_info["path"])
        case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        case_dir = self.target_dir / case_id
        
        print(f"迁移 {run_folder_info['name']} 到案例 {case_id}...")
        
        # 创建案例目录结构
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "config").mkdir(exist_ok=True)
        (case_dir / "simulation").mkdir(exist_ok=True)
        (case_dir / "analysis").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "results").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "charts").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "reports").mkdir(exist_ok=True)
        
        # 复制文件
        files_mapped = {}
        for file_info in run_folder_info["files"]:
            source_file = Path(file_info["path"])
            if file_info["type"] in ["xml", "sumo_config"]:
                if "od" in file_info["name"].lower():
                    target_file = case_dir / "config" / "od_data.xml"
                    files_mapped["od_file"] = str(target_file)
                elif "rou" in file_info["name"].lower():
                    target_file = case_dir / "config" / "routes.xml"
                    files_mapped["routes_file"] = str(target_file)
                elif "sumocfg" in file_info["name"].lower():
                    target_file = case_dir / "config" / "simulation.sumocfg"
                    files_mapped["config_file"] = str(target_file)
                elif "static" in file_info["name"].lower():
                    target_file = case_dir / "config" / "static.xml"
                    files_mapped["static_file"] = str(target_file)
                else:
                    target_file = case_dir / "simulation" / file_info["name"]
                    files_mapped[f"simulation_{file_info['name']}"] = str(target_file)
            else:
                target_file = case_dir / "simulation" / file_info["name"]
                files_mapped[f"simulation_{file_info['name']}"] = str(target_file)
            
            shutil.copy2(source_file, target_file)
        
        # 复制子文件夹
        for subfolder_info in run_folder_info["subfolders"]:
            source_subfolder = Path(subfolder_info["path"])
            if "e1" in subfolder_info["name"].lower():
                target_subfolder = case_dir / "simulation" / "e1_detectors"
                files_mapped["e1_detectors"] = str(target_subfolder)
            elif "gantry" in subfolder_info["name"].lower():
                target_subfolder = case_dir / "simulation" / "gantry_data"
                files_mapped["gantry_data"] = str(target_subfolder)
            else:
                target_subfolder = case_dir / "simulation" / subfolder_info["name"]
                files_mapped[f"simulation_{subfolder_info['name']}"] = str(target_subfolder)
            
            if source_subfolder.exists():
                shutil.copytree(source_subfolder, target_subfolder, dirs_exist_ok=True)
        
        # 创建元数据
        metadata = {
            "case_id": case_id,
            "case_name": f"迁移自_{run_folder_info['name']}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "original_folder": run_folder_info["name"],
            "time_range": self._extract_time_range_from_files(files_mapped),
            "config": {
                "taz_file": "TAZ_5_validated.add.xml",
                "net_file": "sichuan202503v6.net.xml",
                "interval_minutes": 5,
                "enable_mesoscopic": False
            },
            "status": "migrated",
            "description": f"从 {run_folder_info['name']} 迁移的案例",
            "statistics": {
                "total_files": len(run_folder_info["files"]),
                "total_subfolders": len(run_folder_info["subfolders"]),
                "original_created_at": run_folder_info["created_at"]
            },
            "files": files_mapped
        }
        
        # 保存元数据
        with open(case_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.migration_log.append({
            "type": "run_folder_migration",
            "source": run_folder_info["name"],
            "target": case_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        return case_id
    
    def _extract_time_range_from_files(self, files_mapped: Dict[str, str]) -> Dict[str, str]:
        """从文件中提取时间范围"""
        # 这里应该实现从OD文件或其他文件中提取时间范围的逻辑
        # 暂时返回默认值
        return {
            "start": "2025/07/21 08:00:00",
            "end": "2025/07/21 09:00:00"
        }
    
    def migrate_accuracy_results(self, accuracy_info: Dict[str, Any]) -> str:
        """
        迁移精度分析结果
        
        Args:
            accuracy_info: 精度分析文件夹信息
            
        Returns:
            迁移结果路径
        """
        accuracy_folder_path = Path(accuracy_info["path"])
        
        # 查找对应的案例
        case_id = self._find_matching_case(accuracy_info)
        if not case_id:
            print(f"警告: 未找到对应的案例，跳过精度分析结果 {accuracy_info['name']}")
            return ""
        
        case_dir = self.target_dir / case_id
        accuracy_target_dir = case_dir / "analysis" / "accuracy" / "results"
        
        # 确保目标目录存在
        accuracy_target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"迁移精度分析结果 {accuracy_info['name']} 到案例 {case_id}...")
        
        # 复制精度分析结果
        if accuracy_folder_path.exists():
            shutil.copytree(accuracy_folder_path, accuracy_target_dir, dirs_exist_ok=True)
        
        # 更新案例元数据
        metadata_file = case_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            metadata["status"] = "analysis_completed"
            metadata["updated_at"] = datetime.now().isoformat()
            metadata["analysis_results"] = {
                "accuracy_folder": str(accuracy_target_dir),
                "migrated_at": datetime.now().isoformat()
            }
            
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.migration_log.append({
            "type": "accuracy_migration",
            "source": accuracy_info["name"],
            "target": case_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        return case_id
    
    def _find_matching_case(self, accuracy_info: Dict[str, Any]) -> Optional[str]:
        """查找匹配的案例"""
        # 从精度分析文件夹名称中提取时间信息
        # 这里应该实现更复杂的匹配逻辑
        # 暂时返回第一个案例
        cases = list(self.target_dir.glob("case_*"))
        if cases:
            return cases[0].name
        return None
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """生成迁移报告"""
        report = {
            "migration_timestamp": datetime.now().isoformat(),
            "total_migrations": len(self.migration_log),
            "successful_migrations": len([log for log in self.migration_log if log["status"] == "success"]),
            "failed_migrations": len([log for log in self.migration_log if log["status"] == "failed"]),
            "migration_details": self.migration_log,
            "source_directory": str(self.source_dir),
            "target_directory": str(self.target_dir)
        }
        
        return report
    
    def save_migration_report(self, report: Dict[str, Any], filename: str = "migration_report.json"):
        """保存迁移报告"""
        report_file = Path(filename)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"迁移报告已保存到: {report_file}")
    
    def run_full_migration(self) -> Dict[str, Any]:
        """
        运行完整的数据迁移
        
        Returns:
            迁移报告
        """
        print("开始数据迁移...")
        print("=" * 50)
        
        # 1. 扫描现有数据
        scan_result = self.scan_existing_data()
        print(f"发现 {len(scan_result['run_folders'])} 个run文件夹")
        print(f"发现 {len(scan_result['accuracy_results'])} 个精度分析结果")
        print(f"发现 {len(scan_result['taz_files'])} 个TAZ文件")
        print(f"发现 {len(scan_result['network_files'])} 个网络文件")
        
        # 2. 迁移run文件夹
        migrated_cases = []
        for run_folder in scan_result["run_folders"]:
            try:
                case_id = self.migrate_run_folder_to_case(run_folder)
                migrated_cases.append(case_id)
                print(f"✓ 成功迁移: {run_folder['name']} -> {case_id}")
            except Exception as e:
                print(f"✗ 迁移失败: {run_folder['name']} - {str(e)}")
                self.migration_log.append({
                    "type": "run_folder_migration",
                    "source": run_folder["name"],
                    "target": "",
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e)
                })
        
        # 3. 迁移精度分析结果
        for accuracy_result in scan_result["accuracy_results"]:
            try:
                case_id = self.migrate_accuracy_results(accuracy_result)
                if case_id:
                    print(f"✓ 成功迁移精度分析: {accuracy_result['name']} -> {case_id}")
                else:
                    print(f"⚠ 跳过精度分析: {accuracy_result['name']} (未找到匹配案例)")
            except Exception as e:
                print(f"✗ 精度分析迁移失败: {accuracy_result['name']} - {str(e)}")
                self.migration_log.append({
                    "type": "accuracy_migration",
                    "source": accuracy_result["name"],
                    "target": "",
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e)
                })
        
        # 4. 生成报告
        report = self.generate_migration_report()
        self.save_migration_report(report)
        
        print("=" * 50)
        print("数据迁移完成!")
        print(f"成功迁移案例: {len(migrated_cases)}")
        print(f"迁移日志条目: {len(self.migration_log)}")
        
        return report

def main():
    """主函数"""
    migration_tool = DataMigrationTool()
    report = migration_tool.run_full_migration()
    
    print("\n迁移报告摘要:")
    print(f"- 总迁移数: {report['total_migrations']}")
    print(f"- 成功迁移: {report['successful_migrations']}")
    print(f"- 失败迁移: {report['failed_migrations']}")

if __name__ == "__main__":
    main() 