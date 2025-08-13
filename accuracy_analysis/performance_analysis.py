"""
性能分析模块（performance）

产出：
- 简要的 summary.xml 统计（steps、loaded/inserted/ended总量、running/ waiting 最大值）
- 文件规模与数量统计（simulation 与 analysis 子树）
- HTML 报告 performance_report.html
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

from .utils import log_analysis_progress, create_timestamp_folder


class PerformanceAnalyzer:
    """性能分析器
    - 输入：cases/{case_id}/simulation
    - 核心：解析 summary.xml 的过程计数与峰值，统计 simulation/analysis 目录体量
    - 输出：HTML 报告（无图）
    """
    def __init__(self, simulation_folder: str, output_base_folder: str) -> None:
        self.simulation_folder = simulation_folder
        self.output_base_folder = output_base_folder
        os.makedirs(self.output_base_folder, exist_ok=True)
        self.output_folder = create_timestamp_folder(self.output_base_folder, "accuracy_results")
        self.charts_folder = os.path.join(self.output_folder, 'charts')
        os.makedirs(self.charts_folder, exist_ok=True)

    def _collect_summary_stats(self) -> Dict[str, Any]:
        stats = {
            "steps": 0,
            "loaded_total": 0,
            "inserted_total": 0,
            "running_max": 0,
            "waiting_max": 0,
            "ended_total": 0,
        }
        try:
            summary_path = os.path.join(self.simulation_folder, "summary.xml")
            if not os.path.exists(summary_path):
                return stats
            tree = ET.parse(summary_path)
            root = tree.getroot()
            for step in root.findall('step'):
                stats["steps"] += 1
                try:
                    stats["loaded_total"] += int(float(step.get('loaded', '0')))
                except Exception:
                    pass
                try:
                    stats["inserted_total"] += int(float(step.get('inserted', '0')))
                except Exception:
                    pass
                try:
                    stats["ended_total"] += int(float(step.get('ended', '0')))
                except Exception:
                    pass
                try:
                    r = int(float(step.get('running', '0')))
                    if r > stats["running_max"]:
                        stats["running_max"] = r
                except Exception:
                    pass
                try:
                    w = int(float(step.get('waiting', '0')))
                    if w > stats["waiting_max"]:
                        stats["waiting_max"] = w
                except Exception:
                    pass
        except Exception as e:
            log_analysis_progress(f"解析 summary.xml 失败: {e}", "WARNING")
        return stats

    def _collect_folder_stats(self, path: str) -> Dict[str, Any]:
        try:
            total_files = 0
            total_bytes = 0
            for root, _dirs, files in os.walk(path):
                for name in files:
                    try:
                        fp = os.path.join(root, name)
                        total_files += 1
                        total_bytes += os.path.getsize(fp)
                    except Exception:
                        continue
            return {
                "total_files": total_files,
                "total_bytes": total_bytes,
            }
        except Exception:
            return {"total_files": 0, "total_bytes": 0}

    def _generate_report(self, summary_stats: Dict[str, Any], folders: Dict[str, Any]) -> Optional[str]:
        try:
            html_path = os.path.join(self.output_folder, 'performance_report.html')
            fmt_mb = lambda b: f"{(b/1024/1024):.2f} MB"
            sim = folders.get('simulation', {})
            ana = folders.get('analysis', {})
            total_files = sim.get('total_files', 0) + ana.get('total_files', 0)
            total_bytes = sim.get('total_bytes', 0) + ana.get('total_bytes', 0)
            content = f"""
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>性能分析报告</title>
  <style>
    body{{font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', Arial, sans-serif; padding:16px; color:#222;}}
    h1{{margin:8px 0 12px;}}
    h2{{margin:16px 0 8px;}}
    .card{{border:1px solid #e5e7eb; border-radius:8px; padding:12px; margin:12px 0; background:#fff;}}
    .grid{{display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px;}}
    .ov{{border:1px solid #e5e7eb; border-radius:8px; background:#f9fafb; padding:10px;}}
  </style>
  </head>
<body>
  <h1>性能分析报告</h1>
  <div class=\"card\">
    <h2>概述</h2>
    <p style='opacity:.8;'>本报告展示仿真运行的核心过程指标与产物规模，帮助快速判断仿真规模、拥挤程度与产物大小是否在预期范围。</p>
  </div>

  <div class=\"card\">
    <h2>仿真摘要（summary.xml）</h2>
    <p style='opacity:.8;'>统计自每一步(step)的仿真摘要：steps为总步数；loaded/inserted/ended为车辆加载/注入/结束总量；running_max/ waiting_max 为峰值在跑/等待车辆数。</p>
    <div class='grid'>
      <div class='ov'>steps：{summary_stats.get('steps')}</div>
      <div class='ov'>loaded_total：{summary_stats.get('loaded_total')}</div>
      <div class='ov'>inserted_total：{summary_stats.get('inserted_total')}</div>
      <div class='ov'>ended_total：{summary_stats.get('ended_total')}</div>
      <div class='ov'>running_max：{summary_stats.get('running_max')}</div>
      <div class='ov'>waiting_max：{summary_stats.get('waiting_max')}</div>
    </div>
  </div>
  <div class=\"card\">
    <h2>产物规模</h2>
    <p style='opacity:.8;'>统计 simulation 与 analysis 目录下的文件数量与总体积，便于评估存储与I/O压力。</p>
    <div class='grid'>
      <div class='ov'>simulation 文件数：{sim.get('total_files',0)}</div>
      <div class='ov'>analysis 文件数：{ana.get('total_files',0)}</div>
      <div class='ov'>总文件数：{total_files}</div>
      <div class='ov'>simulation 体积：{fmt_mb(sim.get('total_bytes',0))}</div>
      <div class='ov'>analysis 体积：{fmt_mb(ana.get('total_bytes',0))}</div>
      <div class='ov'>总体积：{fmt_mb(total_bytes)}</div>
    </div>
  </div>

  <div class=\"card\">
    <h2>如何解读与建议</h2>
    <ul>
      <li>running_max/ waiting_max 较高：考虑减小时间切片或启用路径收敛以降低峰值在跑/等待车辆数。</li>
      <li>steps 与 ended_total 明显不匹配：确认仿真时长与OD投放窗口一致性。</li>
      <li>analysis 体积/文件数过大：减少输出类型（如关闭 netstate/fcd），或启用压缩（将输出改为 .xml.gz）。</li>
    </ul>
  </div>
</body>
</html>
"""
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return html_path
        except Exception as e:
            log_analysis_progress(f"性能报告生成失败: {e}", "WARNING")
            return None

    def analyze(self) -> Dict[str, Any]:
        try:
            # 统计 summary.xml
            summary_stats = self._collect_summary_stats()
            # 统计目录规模
            folders = {
                "simulation": self._collect_folder_stats(self.simulation_folder),
                "analysis": self._collect_folder_stats(os.path.join(os.path.dirname(self.simulation_folder), 'analysis')),
            }
            report_file = self._generate_report(summary_stats, folders)
            # 效率对象（前端性能卡片复用）
            efficiency = {
                "duration_sec": None,
                "chart_count": 0,
                "charts_total_bytes": 0,
                "report_bytes": (os.path.getsize(report_file) if report_file and os.path.exists(report_file) else 0)
            }
            return {
                "success": True,
                "output_folder": self.output_folder,
                "summary_stats": summary_stats,
                "efficiency": efficiency,
                "chart_files": [],
                "csv_files": [],
                "report_file": report_file,
            }
        except Exception as e:
            log_analysis_progress(f"性能分析失败: {e}", "ERROR")
            return {"success": False, "error": str(e), "output_folder": self.output_folder}


