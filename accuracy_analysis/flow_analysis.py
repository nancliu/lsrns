"""
交通流机理分析模块

功能：
- 观测OD数据 vs 仿真输入（来自 od.xml 与/或 rou.xml 估算）对比
- 仿真输入（rou.xml估算） vs 仿真输出车流（优先 tripinfo.xml，回退 vehroute.xml）对比

输出：
- CSV 对比结果，存放于 accuracy_analysis/accuracy_results_yyyyMMdd_HHmmss 目录
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .utils import (
    log_analysis_progress,
    parse_time_from_filename,
    create_timestamp_folder,
    find_folder_with_prefix,
    DB_CONFIG,
    ANALYSIS_CONFIG,
)

import psycopg2
from .data_loader import DataLoader


@dataclass
class FlowRecord:
    flow_id: str
    from_taz: str
    to_taz: str
    begin: float
    end: float
    vehs_per_hour: float


class TrafficFlowAnalyzer:
    """交通流机理分析器
    - 负责机理相关的两类OD对比与E1速度类图表生成
    - 产出 CSV 与图表，并汇总为 mechanism_report.html
    """

    def __init__(self, run_folder: str, output_base_folder: str = "accuracy_analysis"):
        self.run_folder = run_folder
        self.output_base_folder = output_base_folder

        # 解析时间范围（优先从文件名）
        self.start_time, self.end_time = self._parse_time_range()
        self.output_folder = self._create_output_folder()
        self.charts_folder = os.path.join(self.output_folder, 'charts')
        os.makedirs(self.charts_folder, exist_ok=True)

        log_analysis_progress(f"机理分析初始化完成: {self.run_folder}")

    # ---------------------- 初始化/工具 ----------------------
    def _parse_time_range(self) -> Tuple[datetime, datetime]:
        """与精度分析保持一致的时间解析策略：
        1) 优先读取 cases/{case_id}/metadata.json 的 time_range
        2) 其次从 cases/{case_id}/config/simulation.sumocfg 的注释 real_start/real_end 读取
        3) 再次回退通过 .od.xml 文件名解析（在 config/ 或 传入目录下）
        """
        try:
            # 解析 case_root：若传入的是 simulation 目录，则取上级
            case_root = self.run_folder
            try:
                base = os.path.basename(self.run_folder.rstrip('/\\')).lower()
                if base in ('simulation', 'config'):
                    case_root = os.path.dirname(self.run_folder.rstrip('/\\'))
            except Exception:
                pass

            # 1) metadata.json
            try:
                meta_path = os.path.join(case_root, 'metadata.json')
                if os.path.exists(meta_path):
                    import json as _json
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = _json.load(f)
                    tr = meta.get('time_range') or {}
                    s = tr.get('start'); e = tr.get('end')
                    if s and e:
                        for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
                            try:
                                sd = datetime.strptime(s.replace('T',' ').split('Z')[0], fmt)
                                ed = datetime.strptime(e.replace('T',' ').split('Z')[0], fmt)
                                return sd, ed
                            except Exception:
                                continue
            except Exception:
                pass

            # 2) config/simulation.sumocfg 注释
            try:
                cfg_path = os.path.join(case_root, 'config', 'simulation.sumocfg')
                if os.path.exists(cfg_path):
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    m1 = re.search(r"real_start=([0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", text)
                    m2 = re.search(r"real_end=([0-9]{4}/[0-9]{2}/[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", text)
                    if m1 and m2:
                        sdt = datetime.strptime(m1.group(1), "%Y/%m/%d %H:%M:%S")
                        edt = datetime.strptime(m2.group(1), "%Y/%m/%d %H:%M:%S")
                        return sdt, edt
            except Exception:
                pass

            # 3) 通过 .od.xml 文件名解析（config 或 run_folder）
            try:
                search_dirs = [self.run_folder, os.path.join(case_root, 'config')]
                for d in search_dirs:
                    if not d or not os.path.isdir(d):
                        continue
                    for fn in os.listdir(d):
                        if fn.endswith('.od.xml'):
                            return parse_time_from_filename(fn)
            except Exception:
                pass
        except Exception:
            pass
        raise ValueError(f"无法解析时间范围: {self.run_folder}")

    def _create_output_folder(self) -> str:
        os.makedirs(self.output_base_folder, exist_ok=True)
        folder = create_timestamp_folder(self.output_base_folder, "accuracy_results")
        return folder

    # ---------------------- 解析输入 ----------------------
    def _find_file(self, suffix: str) -> Optional[str]:
        """在 run_folder 与 cases/{case_id}/config 下查找目标文件"""
        try:
            search_dirs: List[str] = []
            # 优先 run_folder
            if os.path.isdir(self.run_folder):
                search_dirs.append(self.run_folder)
            # case_root/config
            case_root = self.run_folder
            try:
                base = os.path.basename(self.run_folder.rstrip('/\\')).lower()
                if base in ('simulation', 'config'):
                    case_root = os.path.dirname(self.run_folder.rstrip('/\\'))
            except Exception:
                pass
            cfg_dir = os.path.join(case_root, 'config')
            if os.path.isdir(cfg_dir):
                search_dirs.append(cfg_dir)
            for d in search_dirs:
                try:
                    for fn in os.listdir(d):
                        if fn.endswith(suffix):
                            return os.path.join(d, fn)
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def parse_od_xml(self) -> pd.DataFrame:
        """解析 od.xml 得到 (fromTaz, toTaz) 聚合的输入OD数量。

        说明：
        - 仅用于机理“观测OD vs 仿真输入flow”的辅助回退口径。
        - 若 `.rou.xml` 可用，则优先使用 `.rou.xml` 的 flow 时间窗 + 车速/小时换算得到更贴近投放的输入量。

        Returns: DataFrame[fromTaz, toTaz, input_od_amount]
        """
        od_path = self._find_file('.od.xml')
        if not od_path or not os.path.exists(od_path):
            log_analysis_progress("未找到 od.xml，跳过od输入解析", "WARNING")
            return pd.DataFrame()

        try:
            tree = ET.parse(od_path)
            root = tree.getroot()
            rows: List[Tuple[str, str, float]] = []
            for ts in root.findall('.//timeSlice'):
                for odp in ts.findall('odPair'):
                    origin = odp.get('origin') or odp.get('fromTaz') or ''
                    dest = odp.get('destination') or odp.get('toTaz') or ''
                    amount = float(odp.get('amount', '0'))
                    if origin and dest:
                        rows.append((origin, dest, amount))
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows, columns=['fromTaz', 'toTaz', 'amount'])
            df = df.groupby(['fromTaz', 'toTaz'], as_index=False)['amount'].sum()
            df = df.rename(columns={'amount': 'input_od_amount'})
            return df
        except Exception as e:
            log_analysis_progress(f"解析 od.xml 失败: {e}", "ERROR")
            return pd.DataFrame()

    def parse_rou_flows(self) -> pd.DataFrame:
        """解析 rou.xml 得到每个flow的参数以及按OD聚合的预计输入车辆数。

        说明：
        - 作为机理“输入口径”的首选来源，兼容 fromTaz/toTaz 或 from/to 字段。
        - 采用 `vehsPerHour * (end-begin)/3600` 估算该 flow 在窗口内的车辆数。

        Returns: DataFrame[fromTaz, toTaz, input_flow_count]
        """
        rou_path = self._find_file('.rou.xml')
        if not rou_path or not os.path.exists(rou_path):
            log_analysis_progress("未找到 rou.xml，跳过flow输入解析", "WARNING")
            return pd.DataFrame()

        try:
            tree = ET.parse(rou_path)
            root = tree.getroot()
            flow_rows: List[FlowRecord] = []
            for f in root.findall('flow'):
                flow_id = f.get('id') or ''
                begin = float(f.get('begin', '0'))
                end = float(f.get('end', '0'))
                vph = float(f.get('vehsPerHour', '0'))
                from_taz = f.get('fromTaz') or f.get('from') or ''
                to_taz = f.get('toTaz') or f.get('to') or ''
                if flow_id and from_taz and to_taz:
                    flow_rows.append(FlowRecord(flow_id, from_taz, to_taz, begin, end, vph))

            if not flow_rows:
                return pd.DataFrame()

            df = pd.DataFrame([r.__dict__ for r in flow_rows])
            duration = (df['end'] - df['begin']).clip(lower=0)
            df['expected_count'] = df['vehs_per_hour'] * (duration / 3600.0)
            df_od = (
                df.groupby(['from_taz', 'to_taz'], as_index=False)['expected_count'].sum()
                .rename(columns={'from_taz': 'fromTaz', 'to_taz': 'toTaz', 'expected_count': 'input_flow_count'})
            )
            return df_od
        except Exception as e:
            log_analysis_progress(f"解析 rou.xml 失败: {e}", "ERROR")
            return pd.DataFrame()

    def _read_tripinfo_or_vehroute(self) -> pd.DataFrame:
        """读取 tripinfo.xml（优先）或 vehroute.xml，返回车辆→flowId 映射及出发时间。

        说明：
        - SUMO 默认会用 `<flow id>` 作为车辆 `id` 的前缀，常见格式为 `f_12.0`, `f_12#1` 等。
        - 这里仅提取前缀作为 `flow_id` 用于与 `.rou.xml` 的 `<flow id>` 对齐，不做车辆粒度的路径对照。

        Returns: DataFrame[vehicle_id, flow_id, depart]
        """
        def parse_tripinfo(path: str) -> pd.DataFrame:
            rows = []
            tree = ET.parse(path)
            root = tree.getroot()
            for ti in root.findall('tripinfo'):
                vid = ti.get('id') or ''
                depart = float(ti.get('depart', '0'))
                # 流生成的车辆默认 id 形如: f_12.0, 也可能用其他分隔符
                try:
                    flow_id = re.split(r"[.#]", vid)[0]
                except Exception:
                    flow_id = vid.split('.')[0] if '.' in vid else ''
                rows.append((vid, flow_id, depart))
            return pd.DataFrame(rows, columns=['vehicle_id', 'flow_id', 'depart'])

        def parse_vehroute(path: str) -> pd.DataFrame:
            rows = []
            tree = ET.parse(path)
            root = tree.getroot()
            for veh in root.findall('vehicle'):
                vid = veh.get('id') or ''
                depart = float(veh.get('depart', '0'))
                try:
                    flow_id = re.split(r"[.#]", vid)[0]
                except Exception:
                    flow_id = vid.split('.')[0] if '.' in vid else ''
                rows.append((vid, flow_id, depart))
            return pd.DataFrame(rows, columns=['vehicle_id', 'flow_id', 'depart'])

        tripinfo = os.path.join(self.run_folder, 'tripinfo.xml')
        if os.path.exists(tripinfo):
            try:
                return parse_tripinfo(tripinfo)
            except Exception as e:
                log_analysis_progress(f"解析 tripinfo.xml 失败: {e}", "WARNING")

        vehroute = os.path.join(self.run_folder, 'vehroute.xml')
        if os.path.exists(vehroute):
            try:
                return parse_vehroute(vehroute)
            except Exception as e:
                log_analysis_progress(f"解析 vehroute.xml 失败: {e}", "WARNING")

        log_analysis_progress("未找到 tripinfo.xml 或 vehroute.xml", "WARNING")
        return pd.DataFrame()

    # ---------------------- 观测OD ----------------------
    def load_observed_od(self, schemas_name: str = 'dwd', table_name: Optional[str] = None) -> pd.DataFrame:
        """从数据库加载观测OD，聚合到 (fromTaz,toTaz) 总量。

        优先字段：start_square_code/end_square_code；为空回退 station_code。
        用途：与 `.rou.xml` 或 `.od.xml` 的输入口径做 OD 级别总量对比。
        """
        # 推断表名
        if not table_name:
            # 按年份推断
            if self.start_time.year == 2024:
                table_name = 'dwd_od_g4202'
            else:
                table_name = 'dwd_od_weekly'

        sql = f"""
        WITH params AS (
          SELECT 
            TO_TIMESTAMP(%s, 'YYYY/MM/DD HH24:MI:SS') AS start_ts,
            TO_TIMESTAMP(%s, 'YYYY/MM/DD HH24:MI:SS') AS end_ts
        )
        SELECT
          COALESCE(NULLIF(t."start_square_code", ''), t."start_station_code") AS "fromTaz",
          COALESCE(NULLIF(t."end_square_code",   ''), t."end_station_code")   AS "toTaz",
          COUNT(*)::bigint AS cnt
        FROM "{schemas_name}"."{table_name}" t
        CROSS JOIN params p
        WHERE t."start_time" >= p.start_ts AND t."start_time" < p.end_ts
        GROUP BY 1,2
        HAVING COALESCE(NULLIF(t."start_square_code", ''), t."start_station_code") IS NOT NULL
           AND COALESCE(NULLIF(t."end_square_code",   ''), t."end_station_code") IS NOT NULL
        ;
        """

        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            df = pd.read_sql_query(
                sql,
                conn,
                params=[self.start_time.strftime('%Y/%m/%d %H:%M:%S'), self.end_time.strftime('%Y/%m/%d %H:%M:%S')]
            )
            if df.empty:
                return pd.DataFrame()
            df = df.rename(columns={'cnt': 'observed_count'})
            return df
        except Exception as e:
            log_analysis_progress(f"查询观测OD失败: {e}", "ERROR")
            return pd.DataFrame()
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    # ---------------------- 对比逻辑 ----------------------
    def compare_observed_vs_input(self) -> Optional[str]:
        """观测OD vs 仿真输入（优先 rou.xml 估算，其次 od.xml）对比，输出CSV路径。

        设计要点：
        - 以 OD 粒度对齐，避免门架/路径分配差异干扰。
        - 输出 diff/ratio/mape，支持快速定位总量/结构偏差。
        """
        df_obs = self.load_observed_od()
        df_flow = self.parse_rou_flows()
        df_odxml = self.parse_od_xml()

        # 选择输入口径：优先 rou.xml 计算出的 input_flow_count
        if not df_flow.empty:
            df_input = df_flow.rename(columns={'input_flow_count': 'input_count'})
        elif not df_odxml.empty:
            df_input = df_odxml.rename(columns={'input_od_amount': 'input_count'})
        else:
            log_analysis_progress("无可用仿真输入（rou或od）", "WARNING")
            return None

        if df_obs.empty:
            log_analysis_progress("观测OD为空，跳过该对比", "WARNING")
            return None

        df_merged = pd.merge(df_obs, df_input, on=['fromTaz', 'toTaz'], how='inner')
        if df_merged.empty:
            log_analysis_progress("观测OD与仿真输入无交集", "WARNING")
            return None

        # 指标
        df_merged['diff'] = df_merged['input_count'] - df_merged['observed_count']
        df_merged['ratio'] = (df_merged['input_count'] / df_merged['observed_count']).replace([np.inf, -np.inf], np.nan)
        df_merged['mape'] = (np.abs(df_merged['diff']) / df_merged['observed_count']) * 100.0

        out_path = os.path.join(self.output_folder, 'od_observed_vs_input.csv')
        df_merged.to_csv(out_path, index=False, encoding='utf-8-sig')
        return out_path

    def compare_input_vs_simoutput(self) -> Optional[str]:
        """仿真输入（rou.xml估算） vs 仿真输出（tripinfo/vehroute统计）对比，输出CSV路径。

        设计要点：
        - 通过车辆 `id` 前缀还原到 flow，再基于 `.rou.xml` 的 `<flow id fromTaz/toTaz>` 建立 OD 映射。
        - 若车辆命名或 `.rou.xml` 无 fromTaz/toTaz，将无法映射到 OD（此时输出提示）。
        - 统计的是“实际输出车辆”在 OD 粒度上的聚合计数。
        """
        df_flow = self.parse_rou_flows()
        if df_flow.empty:
            log_analysis_progress("无 rou.xml 输入，无法进行输入vs输出对比", "WARNING")
            return None

        df_out = self._read_tripinfo_or_vehroute()
        if df_out.empty:
            log_analysis_progress("未找到可用的仿真输出（tripinfo/vehroute）", "WARNING")
            return None

        # 读取 rou.xml 以构建 flow_id -> (fromTaz,toTaz)
        rou_path = self._find_file('.rou.xml')
        try:
            tree = ET.parse(rou_path)
            root = tree.getroot()
            mapping: Dict[str, Tuple[str, str]] = {}
            id_map: Dict[str, Tuple[str, str]] = {}
            # 1) 解析 flow 元素
            for f in root.findall('flow'):
                fid = f.get('id') or ''
                ft = f.get('fromTaz') or f.get('from') or ''
                tt = f.get('toTaz') or f.get('to') or ''
                if fid and ft and tt:
                    mapping[fid] = (ft, tt)
            # 2) 解析 route 元素（如存在，记录 id 映射）
            for r in root.findall('route'):
                rid = r.get('id') or ''
                if rid:
                    id_map[rid] = ('', '')
            # 3) 解析 vehicle 基于 routeRef（若存在）
            # 这里不聚合vehicle级别，只尝试补充映射备用
            for veh in root.findall('vehicle'):
                vid = veh.get('id') or ''
                route_ref = veh.get('route') or veh.get('routeRef') or ''
                if route_ref and route_ref in id_map:
                    id_map[vid] = id_map.get(route_ref, ('', ''))
            # 合并两个映射，优先 flow 映射
            if id_map:
                mapping.update(id_map)
        except Exception as e:
            log_analysis_progress(f"解析 rou.xml 以获取flow映射失败: {e}", "ERROR")
            return None

        # 将输出车辆映射到 OD
        df_out['flow_id'] = df_out['flow_id'].astype(str)
        def map_to_od(fid: str) -> Tuple[Optional[str], Optional[str]]:
            # 直接用 flow_id；若不存在，尝试去掉前缀 f_ / v_ 等
            if fid in mapping:
                return mapping[fid]
            fid2 = re.sub(r"^(f_|v_|flow_)", "", fid)
            return mapping.get(fid2, (None, None))
        df_out[['fromTaz','toTaz']] = df_out['flow_id'].apply(lambda x: pd.Series(map_to_od(x)))
        df_out = df_out.dropna(subset=['fromTaz', 'toTaz'])

        # 仅保留映射成功的记录
        df_out = df_out.dropna(subset=['fromTaz', 'toTaz'])
        if df_out.empty:
            log_analysis_progress("tripinfo/vehroute 无法映射到任何 fromTaz/toTaz，请检查 flow id 命名或 rou.xml 中 flow 的 id 与 fromTaz/toTaz", "WARNING")
            return None
        df_out_od = df_out.groupby(['fromTaz', 'toTaz'], as_index=False).agg(sim_output_count=('vehicle_id','count'))

        df_input = df_flow.rename(columns={'input_flow_count': 'input_count'})
        df_merged = pd.merge(df_input, df_out_od, on=['fromTaz', 'toTaz'], how='inner')
        if df_merged.empty:
            log_analysis_progress("输入OD与仿真输出OD无交集", "WARNING")
            return None

        df_merged['diff'] = df_merged['sim_output_count'] - df_merged['input_count']
        df_merged['ratio'] = (df_merged['sim_output_count'] / df_merged['input_count']).replace([np.inf, -np.inf], np.nan)
        df_merged['mape'] = (np.abs(df_merged['diff']) / df_merged['input_count']) * 100.0

        out_path = os.path.join(self.output_folder, 'od_input_vs_simoutput.csv')
        df_merged.to_csv(out_path, index=False, encoding='utf-8-sig')
        return out_path

    def analyze(self) -> Dict[str, Any]:
        """执行完整机理分析，返回产物路径"""
        log_analysis_progress("开始交通流机理分析...")
        od_vs_input = self.compare_observed_vs_input()
        input_vs_out = self.compare_input_vs_simoutput()
        # 生成CSV的可视化图
        csv_charts = self._generate_csv_visualizations(od_vs_input, input_vs_out)
        # 生成基于E1与观测的机理图（散点/速度序列/滞后）
        mech_charts = self._generate_mechanism_charts()
        # 生成机理报告HTML
        extra_csvs: List[str] = []
        lag_csv = os.path.join(self.output_folder, 'lag_by_gantry.csv')
        if os.path.exists(lag_csv):
            extra_csvs.append(lag_csv)
        report_file = self._generate_mechanism_report(
            chart_files=(csv_charts + mech_charts),
            csv_files=[p for p in [od_vs_input, input_vs_out] if p] + extra_csvs
        )
        log_analysis_progress("交通流机理分析完成")

        return {
            'success': True,
            'output_folder': self.output_folder,
            'csv_files': {
                'observed_vs_input': od_vs_input,
                'input_vs_output': input_vs_out,
            },
            'chart_files': csv_charts + mech_charts,
            'report_file': report_file,
        }

    # ---------------------- CSV 可视化 ----------------------
    def _generate_csv_visualizations(self, od_vs_input_path: Optional[str], input_vs_out_path: Optional[str]) -> List[str]:
        charts: List[str] = []
        try:
            if od_vs_input_path and os.path.exists(od_vs_input_path):
                df = pd.read_csv(od_vs_input_path)
                # 比例直方图（仿真输入/观测）
                try:
                    ratio = df['input_count'] / df['observed_count'] if 'input_count' in df.columns else df.get('ratio')
                    ratio = pd.to_numeric(ratio, errors='coerce')
                    ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()
                    plt.figure(figsize=(8,5))
                    plt.hist(ratio, bins=40, alpha=0.8, color='steelblue', edgecolor='black')
                    plt.axvline(1.0, color='red', linestyle='--', label='理想比例1.0')
                    plt.legend()
                    plt.title('观测OD vs 仿真输入flow 比例分布 (input/observed)')
                    f1 = os.path.join(self.charts_folder, 'observed_vs_input_ratio_hist.png')
                    plt.savefig(f1, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f1)
                except Exception:
                    pass
                # 散点图
                if {'observed_count','input_count'}.issubset(df.columns):
                    try:
                        plt.figure(figsize=(6,6))
                        plt.scatter(df['observed_count'], df['input_count'], s=10, alpha=0.5)
                        mn = min(df['observed_count'].min(), df['input_count'].min())
                        mx = max(df['observed_count'].max(), df['input_count'].max())
                        plt.plot([mn,mx],[mn,mx],'r--',alpha=0.7)
                        plt.xlabel('observed_count'); plt.ylabel('input_count')
                        plt.title('观测OD vs 仿真输入flow 散点')
                        f2 = os.path.join(self.charts_folder, 'observed_vs_input_scatter.png')
                        plt.savefig(f2, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f2)
                    except Exception:
                        pass
            if input_vs_out_path and os.path.exists(input_vs_out_path):
                df = pd.read_csv(input_vs_out_path)
                # 比例直方图（仿真输出/输入）
                try:
                    ratio = df['sim_output_count'] / df['input_count'] if {'sim_output_count','input_count'}.issubset(df.columns) else df.get('ratio')
                    ratio = pd.to_numeric(ratio, errors='coerce')
                    ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()
                    plt.figure(figsize=(8,5))
                    plt.hist(ratio, bins=40, alpha=0.8, color='seagreen', edgecolor='black')
                    plt.axvline(1.0, color='red', linestyle='--', label='理想比例1.0')
                    plt.legend()
                    plt.title('仿真输入flow vs 仿真输出车流 比例分布 (output/input)')
                    f3 = os.path.join(self.charts_folder, 'input_vs_output_ratio_hist.png')
                    plt.savefig(f3, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f3)
                except Exception:
                    pass
                # 散点图
                if {'sim_output_count','input_count'}.issubset(df.columns):
                    try:
                        plt.figure(figsize=(6,6))
                        plt.scatter(df['input_count'], df['sim_output_count'], s=10, alpha=0.5)
                        mn = min(df['input_count'].min(), df['sim_output_count'].min())
                        mx = max(df['input_count'].max(), df['sim_output_count'].max())
                        plt.plot([mn,mx],[mn,mx],'r--',alpha=0.7)
                        plt.xlabel('input_count'); plt.ylabel('sim_output_count')
                        plt.title('仿真输入flow vs 仿真输出车流 散点')
                        f4 = os.path.join(self.charts_folder, 'input_vs_output_scatter.png')
                        plt.savefig(f4, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f4)
                    except Exception:
                        pass
        except Exception as e:
            log_analysis_progress(f"CSV可视化生成失败: {e}", "WARNING")
        return charts

    # ---------------------- 机理图（E1与观测） ----------------------
    def _generate_mechanism_charts(self) -> List[str]:
        charts: List[str] = []
        try:
            time_step = int(ANALYSIS_CONFIG.get('time_interval', 5))
            dl = DataLoader()
            # E1 仿真聚合（包含 sim_flow 与 sim_speed）
            # 需要找到 cases/{case_id}/simulation 下的 e1 目录
            e1_dir = None
            try:
                base = self.run_folder
                if os.path.basename(self.run_folder.rstrip('/\\')).lower() != 'simulation':
                    base = os.path.join(self.run_folder, 'simulation')
                # 常见 e1 位置
                for cand in [os.path.join(base,'e1'), base]:
                    if os.path.isdir(cand):
                        if any(fn.lower().endswith('.xml') for fn in os.listdir(cand)):
                            e1_dir = cand; break
                if not e1_dir:
                    # 递归找 e1*
                    for root, dirs, files in os.walk(base):
                        for d in dirs:
                            if d.lower().startswith('e1'):
                                e1_dir = os.path.join(root,d); break
                        if e1_dir:
                            break
            except Exception:
                e1_dir = None
            if not e1_dir:
                log_analysis_progress("未找到E1目录，跳过机理图生成", "WARNING")
                return charts

            sim_df = dl.load_detector_data(e1_dir, time_interval=time_step, sim_start_time=self.start_time)
            if sim_df.empty or 'sim_speed' not in sim_df.columns:
                log_analysis_progress("E1未包含速度字段或数据为空，跳过机理图生成", "WARNING")
                return charts

            # 观测门架数据
            obs_df = dl.load_gantry_data(self.start_time, self.end_time, time_interval=time_step)
            if obs_df.empty:
                log_analysis_progress("观测门架数据为空，滞后图将跳过", "WARNING")

            # flow-speed 散点
            try:
                sdf = sim_df.dropna(subset=['sim_speed']).copy()
                if not sdf.empty:
                    plt.figure(figsize=(7,6))
                    plt.scatter(sdf['sim_flow'], sdf['sim_speed'], s=8, alpha=0.35)
                    plt.xlabel('sim_flow'); plt.ylabel('sim_speed (km/h)'); plt.title('流-速散点（仿真）')
                    f5 = os.path.join(self.charts_folder, 'flow_speed_scatter.png')
                    plt.savefig(f5, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f5)
            except Exception:
                pass

            # 速度时间序列（总流量TOP5门架）
            try:
                sums = sim_df.groupby('gantry_id')['sim_flow'].sum().sort_values(ascending=False)
                top_ids = list(sums.head(5).index)
                if top_ids:
                    n = len(top_ids)
                    cols = 1; rows = n
                    plt.figure(figsize=(12, 2.5*n))
                    for i, gid in enumerate(top_ids, start=1):
                        sub = sim_df[sim_df['gantry_id']==gid].sort_values('interval_start')
                        ax = plt.subplot(rows, cols, i)
                        ax.plot(sub['interval_start'], sub['sim_speed'], label=f'{gid}', color='tab:blue')
                        ax.set_title(f'门架 {gid} 速度时间序列'); ax.set_xlabel('minute-of-day'); ax.set_ylabel('speed (km/h)')
                        ax.grid(alpha=0.3)
                    plt.tight_layout()
                    f6 = os.path.join(self.charts_folder, 'speed_timeseries_top5.png')
                    plt.savefig(f6, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f6)
            except Exception:
                pass

            # 滞后分布（在观测数据可用时）
            try:
                if obs_df is not None and not obs_df.empty:
                    # 对齐时间轴
                    def best_lag(sim_s: pd.Series, obs_s: pd.Series, max_lag_bins: int = 6) -> int:
                        # 简单互相关：找使均方误差最小的滞后（以桶为单位）
                        lags = range(-max_lag_bins, max_lag_bins+1)
                        best, best_score = 0, float('inf')
                        for lag in lags:
                            if lag >= 0:
                                s = sim_s.shift(lag)
                                o = obs_s
                            else:
                                s = sim_s
                                o = obs_s.shift(-lag)
                            df = pd.DataFrame({'s':s, 'o':o}).dropna()
                            if df.empty:
                                continue
                            mse = ((df['s']-df['o'])**2).mean()
                            if mse < best_score:
                                best_score = mse; best = lag
                        return best

                    merged = pd.merge(sim_df, obs_df.rename(columns={'total_flow':'obs_flow'}), on=['gantry_id','interval_start'], how='inner')
                    if not merged.empty:
                        lag_rows = []
                        for gid, grp in merged.groupby('gantry_id'):
                            sim_s = grp.sort_values('interval_start')['sim_flow']
                            obs_s = grp.sort_values('interval_start')['obs_flow']
                            lag_bins = best_lag(sim_s.reset_index(drop=True), obs_s.reset_index(drop=True), max_lag_bins=6)
                            lag_min = lag_bins * time_step
                            lag_rows.append({'gantry_id': gid, 'lag_bins': lag_bins, 'lag_minutes': lag_min})
                        if lag_rows:
                            lag_df = pd.DataFrame(lag_rows)
                            lag_csv = os.path.join(self.output_folder, 'lag_by_gantry.csv')
                            lag_df.to_csv(lag_csv, index=False, encoding='utf-8-sig')
                            # 直方图
                            plt.figure(figsize=(8,5))
                            plt.hist(lag_df['lag_minutes'], bins=np.arange(-30, 31, time_step), color='orchid', edgecolor='black', alpha=0.8)
                            plt.title('滞后分布（分钟，正值=仿真滞后）'); plt.xlabel('lag (minutes)'); plt.ylabel('count')
                            f7 = os.path.join(self.charts_folder, 'lag_histogram.png')
                            plt.savefig(f7, dpi=200, bbox_inches='tight'); plt.close(); charts.append(f7)
            except Exception:
                pass

        except Exception as e:
            log_analysis_progress(f"机理图生成失败: {e}", "WARNING")
        return charts

    # ---------------------- 机理报告HTML ----------------------
    def _generate_mechanism_report(self, chart_files: List[str], csv_files: List[str]) -> Optional[str]:
        try:
            title = "机理分析报告"
            html_path = os.path.join(self.output_folder, 'mechanism_report.html')

            # 相对引用
            def rel(p: str) -> str:
                try:
                    if os.path.dirname(p) == self.output_folder:
                        return os.path.basename(p)
                    if os.path.dirname(p) == self.charts_folder:
                        return f"charts/{os.path.basename(p)}"
                    return os.path.basename(p)
                except Exception:
                    return os.path.basename(p)

            # 概述统计（从CSV中读取）
            overview_rows: List[str] = []
            try:
                # 观测 vs 输入
                ov_path = next((p for p in csv_files if p and p.endswith('od_observed_vs_input.csv')), None)
                if ov_path and os.path.exists(ov_path):
                    df = pd.read_csv(ov_path)
                    n = len(df)
                    ratio = None
                    if {'observed_count','input_count'}.issubset(df.columns):
                        ratio = (df['input_count'] / df['observed_count']).replace([np.inf,-np.inf], np.nan)
                    elif 'ratio' in df.columns:
                        ratio = pd.to_numeric(df['ratio'], errors='coerce')
                    mape = pd.to_numeric(df.get('mape'), errors='coerce') if 'mape' in df.columns else None
                    ratio_mean = f"{ratio.dropna().mean():.3f}" if ratio is not None and ratio.dropna().size>0 else '—'
                    ratio_med = f"{ratio.dropna().median():.3f}" if ratio is not None and ratio.dropna().size>0 else '—'
                    pass_rate = None
                    if ratio is not None and ratio.dropna().size>0:
                        pass_rate = f"{(ratio.dropna().between(0.8,1.2).mean()*100):.1f}%"
                    mape_mean = f"{mape.dropna().mean():.2f}%" if mape is not None and mape.dropna().size>0 else '—'
                    overview_rows.append(f"<div class='ov-card'><div class='ov-title'>观测OD vs 仿真输入</div><div>OD对数：{n}</div><div>比例均值：{ratio_mean}</div><div>比例中位数：{ratio_med}</div><div>±20%合格率：{pass_rate or '—'}</div><div>MAPE均值：{mape_mean}</div></div>")
            except Exception:
                pass
            try:
                # 输入 vs 输出
                io_path = next((p for p in csv_files if p and p.endswith('od_input_vs_simoutput.csv')), None)
                if io_path and os.path.exists(io_path):
                    df = pd.read_csv(io_path)
                    n = len(df)
                    ratio = None
                    if {'sim_output_count','input_count'}.issubset(df.columns):
                        ratio = (df['sim_output_count'] / df['input_count']).replace([np.inf,-np.inf], np.nan)
                    elif 'ratio' in df.columns:
                        ratio = pd.to_numeric(df['ratio'], errors='coerce')
                    ratio_mean = f"{ratio.dropna().mean():.3f}" if ratio is not None and ratio.dropna().size>0 else '—'
                    ratio_med = f"{ratio.dropna().median():.3f}" if ratio is not None and ratio.dropna().size>0 else '—'
                    pass_rate = None
                    if ratio is not None and ratio.dropna().size>0:
                        pass_rate = f"{(ratio.dropna().between(0.8,1.2).mean()*100):.1f}%"
                    overview_rows.append(f"<div class='ov-card'><div class='ov-title'>仿真输入 vs 仿真输出</div><div>OD对数：{n}</div><div>比例均值：{ratio_mean}</div><div>比例中位数：{ratio_med}</div><div>±20%合格率：{pass_rate or '—'}</div></div>")
            except Exception:
                pass
            try:
                # 滞后
                lag_path = next((p for p in csv_files if p and p.endswith('lag_by_gantry.csv')), None)
                if lag_path and os.path.exists(lag_path):
                    df = pd.read_csv(lag_path)
                    if 'lag_minutes' in df.columns:
                        lag = pd.to_numeric(df['lag_minutes'], errors='coerce').dropna()
                        mean_lag = f"{lag.mean():.1f}min" if lag.size>0 else '—'
                        med_lag = f"{lag.median():.1f}min" if lag.size>0 else '—'
                        within10 = f"{(lag.abs()<=10).mean()*100:.1f}%" if lag.size>0 else '—'
                        overview_rows.append(f"<div class='ov-card'><div class='ov-title'>滞后统计</div><div>平均滞后：{mean_lag}</div><div>中位滞后：{med_lag}</div><div>|滞后|≤10min：{within10}</div></div>")
            except Exception:
                pass

            overview_html = ''.join(overview_rows) if overview_rows else "<div style='opacity:.7;'>暂无概述数据</div>"

            # 图表分组展示（CSV相关与E1相关）
            def caption_of(name: str) -> str:
                m = {
                    'observed_vs_input_ratio_hist.png': '观测OD vs 仿真输入 比例分布',
                    'observed_vs_input_scatter.png': '观测OD vs 仿真输入 散点',
                    'input_vs_output_ratio_hist.png': '仿真输入 vs 仿真输出 比例分布',
                    'input_vs_output_scatter.png': '仿真输入 vs 仿真输出 散点',
                    'flow_speed_scatter.png': '流-速散点（仿真）',
                    'speed_timeseries_top5.png': '速度时间序列（TOP5门架）',
                    'lag_histogram.png': '滞后分布直方图',
                }
                return m.get(name, name)

            csv_chart_imgs = []
            mech_chart_imgs = []
            for p in chart_files:
                if not p or not os.path.exists(p):
                    continue
                name = os.path.basename(p)
                img_tag = f"<figure class='fig'><img src='{rel(p)}' alt='{name}'/><figcaption>{caption_of(name)}</figcaption></figure>"
                if name.startswith('observed_') or name.startswith('input_'):
                    csv_chart_imgs.append(img_tag)
                else:
                    mech_chart_imgs.append(img_tag)
            csv_chart_html = ''.join(csv_chart_imgs)
            mech_chart_html = ''.join(mech_chart_imgs)

            # CSV链接列表
            csv_links = ''.join([
                f"<li><a href='{rel(p)}' target='_blank'>{os.path.basename(p)}</a></li>"
                for p in csv_files if p and os.path.exists(p)
            ])

            time_info = f"<p>时间范围：{self.start_time} ~ {self.end_time}</p>"
            content = f"""
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>{title}</title>
  <style>
    body{{font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', Arial, sans-serif; padding:16px; color:#222;}}
    h1{{margin:8px 0 12px;}}
    h2{{margin:16px 0 8px;}}
    .card{{border:1px solid #e5e7eb; border-radius:8px; padding:12px; margin:12px 0; background:#fff;}}
    .ov-grid{{display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px;}}
    .ov-card{{border:1px solid #e5e7eb; border-radius:8px; padding:10px; background:#f9fafb;}}
    .ov-title{{font-weight:600; margin-bottom:6px;}}
    .grid{{display:grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap:12px;}}
    .fig{{background:#fafafa; border:1px solid #eee; border-radius:8px; padding:8px;}}
    .fig img{{width:100%; height:auto; display:block; border-radius:4px;}}
    .figcaption{{font-size:12px; color:#555; margin-top:4px;}}
  </style>
  </head>
<body>
  <h1>{title}</h1>
  {time_info}
  <div class=\"card\">
    <h2>概述</h2>
    <div class='ov-grid'>
      {overview_html}
    </div>
  </div>
  <div class=\"card\">
    <h2>CSV 产物</h2>
    <ul>
      {csv_links}
    </ul>
  </div>
  <div class=\"card\">
    <h2>OD 对比图</h2>
    <div class='grid'>
      {csv_chart_html or "<div style='opacity:.7;'>暂无图表</div>"}
    </div>
  </div>
  <div class=\"card\">
    <h2>机理图</h2>
    <div class='grid'>
      {mech_chart_html or "<div style='opacity:.7;'>暂无图表</div>"}
    </div>
  </div>
</body>
</html>
"""
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return html_path
        except Exception as e:
            log_analysis_progress(f"机理报告生成失败: {e}", "WARNING")
            return None


