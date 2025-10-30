#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
废弃代码清理执行脚本

功能:
  1. 识别废弃代码位置
  2. 添加废弃警告和文档
  3. 记录需要迁移的项目
  4. 生成清理报告

使用:
  python cleanup_deprecated_code.py --analyze    # 仅分析
  python cleanup_deprecated_code.py --fix        # 执行修复 (需确认)
  python cleanup_deprecated_code.py --report     # 生成报告
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
import subprocess
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeprecatedCodeAnalyzer:
    """分析和标记废弃代码"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.findings = {
            "deprecated_dirs": [],
            "deprecated_functions": [],
            "deprecated_imports": [],
            "open_db_connection_uses": [],
            "large_classes": []
        }

    def analyze_all(self) -> Dict:
        """执行完整分析"""
        logger.info("开始分析废弃代码...")

        self.find_deprecated_directories()
        self.find_deprecated_functions()
        self.find_open_db_connection_uses()
        self.find_large_classes()

        logger.info(f"分析完成: 发现 {self.count_issues()} 个问题")
        return self.findings

    def count_issues(self) -> int:
        """统计问题数量"""
        return sum(len(v) if isinstance(v, list) else 0 for v in self.findings.values())

    def find_deprecated_directories(self):
        """查找标记为废弃的目录"""
        deprecated_dirs = ["sim_scripts", "accuracy_analysis"]

        for dir_name in deprecated_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                files = list(dir_path.glob("**/*.py"))
                logger.info(f"发现废弃目录: {dir_name} ({len(files)} 个 Python 文件)")
                self.findings["deprecated_dirs"].append({
                    "path": str(dir_path),
                    "file_count": len(files),
                    "status": "not_marked"  # 需要标记
                })

    def find_deprecated_functions(self):
        """查找标记为废弃的函数"""
        search_patterns = [
            ("generate_sumocfg", "shared/data_processors/simulation_processor.py"),
        ]

        for pattern, file_path in search_patterns:
            filepath = self.project_root / file_path
            if filepath.exists():
                logger.info(f"发现废弃函数: {pattern} 在 {file_path}")
                self.findings["deprecated_functions"].append({
                    "name": pattern,
                    "location": file_path,
                    "status": "handled"  # 已正确处理
                })

    def find_open_db_connection_uses(self):
        """查找 open_db_connection 的使用"""
        try:
            result = subprocess.run(
                ["grep", "-r", "open_db_connection", "api/", "shared/", "--include=*.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.stdout:
                uses = result.stdout.strip().split("\n")
                logger.info(f"发现 open_db_connection 使用: {len(uses)} 处")
                for use in uses[:10]:  # 仅显示前10个
                    self.findings["open_db_connection_uses"].append({
                        "location": use.split(":")[0],
                        "status": "needs_migration"
                    })
        except Exception as e:
            logger.warning(f"grep 搜索失败: {e}")

    def find_large_classes(self):
        """查找超大类定义"""
        import ast

        for py_file in self.project_root.glob("**/*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        continue

                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # 粗略估计: 方法数 * 平均 20 行
                            method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                            if method_count > 10:
                                logger.info(f"发现大类: {node.name} ({method_count} 个方法)")
                                self.findings["large_classes"].append({
                                    "name": node.name,
                                    "file": str(py_file),
                                    "method_count": method_count,
                                    "status": "needs_refactoring"
                                })
            except Exception as e:
                logger.debug(f"解析失败: {py_file} - {e}")

    def generate_report(self) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 60)
        report.append("废弃代码分析报告")
        report.append("=" * 60)
        report.append("")

        # 废弃目录
        if self.findings["deprecated_dirs"]:
            report.append("【废弃目录】")
            for item in self.findings["deprecated_dirs"]:
                report.append(f"  - {item['path']}")
                report.append(f"    文件数: {item['file_count']}")
                report.append(f"    状态: {item['status']} (需要标记)")
            report.append("")

        # 废弃函数
        if self.findings["deprecated_functions"]:
            report.append("【废弃函数】")
            for item in self.findings["deprecated_functions"]:
                report.append(f"  - {item['name']} ({item['location']})")
                report.append(f"    状态: {item['status']}")
            report.append("")

        # open_db_connection 使用
        if self.findings["open_db_connection_uses"]:
            report.append("【待迁移: open_db_connection】")
            report.append(f"  总计: {len(self.findings['open_db_connection_uses'])} 处")
            for i, item in enumerate(self.findings["open_db_connection_uses"][:5]):
                report.append(f"  - {item['location']}")
            if len(self.findings["open_db_connection_uses"]) > 5:
                report.append(f"  ... 还有 {len(self.findings['open_db_connection_uses'])-5} 处")
            report.append("")

        # 大型类
        if self.findings["large_classes"]:
            report.append("【需要重构的大型类】")
            for item in self.findings["large_classes"]:
                report.append(f"  - {item['name']} ({item['file']})")
                report.append(f"    方法数: {item['method_count']}")
            report.append("")

        # 总结
        report.append("=" * 60)
        report.append(f"总问题数: {self.count_issues()}")
        report.append("=" * 60)

        return "\n".join(report)


class DeprecatedCodeFixer:
    """修复和标记废弃代码"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.changes_made = []

    def add_deprecation_marker(self, file_path: Path, deprecation_notice: str) -> bool:
        """为文件添加废弃标记"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # 检查是否已有标记
            if "DEPRECATED" in content or "已废弃" in content:
                logger.info(f"已标记: {file_path}")
                return False

            # 在文件顶部添加标记
            deprecation_header = f'"""\n{deprecation_notice}\n"""\n\n'
            new_content = deprecation_header + content

            file_path.write_text(new_content, encoding='utf-8')
            logger.info(f"已添加标记: {file_path}")
            self.changes_made.append(str(file_path))
            return True

        except Exception as e:
            logger.error(f"添加标记失败: {file_path} - {e}")
            return False

    def mark_deprecated_directories(self):
        """标记废弃目录"""
        dirs_to_mark = {
            "sim_scripts": """
DEPRECATED: 这个目录包含旧的脚本实现，保留用于参考。

所有新开发应该使用:
  - shared/utilities/sumo_utils.generate_sumocfg_for_simulation()
  - api/services/simulation_service.py (API 层)

请勿在新代码中导入此目录中的模块。
更多信息见 BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md
            """.strip(),
            "accuracy_analysis": """
DEPRECATED: 这个目录包含旧的准确性分析实现，保留用于参考。

所有新开发应该使用:
  - shared/analysis_tools/accuracy_analysis.py
  - api/services/accuracy_service.py (API 层)

请勿在新代码中导入此目录中的模块。
更多信息见 BATCH_SIMULATION_CODE_ANALYSIS_AND_CLEANUP.md
            """.strip()
        }

        for dir_name, notice in dirs_to_mark.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                # 创建 __init__.py 文件
                init_file = dir_path / "__init__.py"
                try:
                    init_file.write_text(f'"""\n{notice}\n"""\n', encoding='utf-8')
                    logger.info(f"已创建: {init_file}")
                    self.changes_made.append(str(init_file))
                except Exception as e:
                    logger.error(f"创建失败: {init_file} - {e}")

    def generate_summary(self) -> str:
        """生成修改总结"""
        summary = []
        summary.append("=" * 60)
        summary.append("废弃代码标记完成")
        summary.append("=" * 60)
        summary.append(f"\n已修改文件数: {len(self.changes_made)}")
        summary.append("\n修改的文件:")
        for file_path in self.changes_made:
            summary.append(f"  - {file_path}")
        summary.append("\n" + "=" * 60)

        return "\n".join(summary)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="分析和清理废弃代码"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="仅分析，不做修改"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="执行修复"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="仅生成报告"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="项目根目录"
    )

    args = parser.parse_args()

    # 如果没有指定操作，默认分析
    if not any([args.analyze, args.fix, args.report]):
        args.analyze = True

    # 创建分析器
    analyzer = DeprecatedCodeAnalyzer(args.root)

    if args.analyze or args.report:
        # 执行分析
        findings = analyzer.analyze_all()

        # 生成报告
        report = analyzer.generate_report()
        print(report)

        # 保存报告
        report_file = Path(args.root) / "DEPRECATED_CODE_ANALYSIS.txt"
        report_file.write_text(report, encoding='utf-8')
        logger.info(f"报告已保存: {report_file}")

    if args.fix:
        # 确认
        confirm = input("\n确定要执行修复? (yes/no): ").strip().lower()
        if confirm != "yes":
            logger.info("已取消")
            return

        # 执行修复
        fixer = DeprecatedCodeFixer(args.root)
        fixer.mark_deprecated_directories()

        # 生成总结
        summary = fixer.generate_summary()
        print(summary)

        # 保存总结
        summary_file = Path(args.root) / "DEPRECATED_CODE_FIXES.txt"
        summary_file.write_text(summary, encoding='utf-8')
        logger.info(f"总结已保存: {summary_file}")

    logger.info("完成")


if __name__ == "__main__":
    main()
