"""
OD数据处理器
迁移自原有的OD数据处理逻辑
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import xml.etree.ElementTree as ET
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ODProcessor:
    """OD数据处理器类"""
    
    def __init__(self):
        self.vehicle_mapping = {
            "k1": "passenger_small",
            "k2": "passenger_small", 
            "k3": "passenger_large",
            "k4": "passenger_large",
            "h1": "truck_small",
            "h2": "truck_small",
            "h3": "truck_large",
            "h4": "truck_large",
            "h5": "truck_large",
            "h6": "truck_large",
            "t1": "bus_small",
            "t2": "bus_large",
            "t3": "bus_large",
            "t4": "bus_large"
        }
    
    def calculate_duration(self, start_time: str, end_time: str) -> int:
        """
        计算两个时间点之间的时长（秒）
        
        Args:
            start_time: 开始时间字符串 "YYYY/MM/DD HH:MM:SS"
            end_time: 结束时间字符串 "YYYY/MM/DD HH:MM:SS"
            
        Returns:
            时长（秒）
        """
        start_dt = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")
        return int((end_dt - start_dt).total_seconds())
    
    def split_time_range(self, start_time: str, end_time: str, interval_minutes: int) -> List[Tuple[str, str]]:
        """
        将时间范围分割为多个小段
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            interval_minutes: 时间间隔（分钟）
            
        Returns:
            时间段列表
        """
        start_dt = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")
        
        time_segments = []
        current_dt = start_dt
        
        while current_dt < end_dt:
            next_dt = min(current_dt + timedelta(minutes=interval_minutes), end_dt)
            time_segments.append((
                current_dt.strftime("%Y/%m/%d %H:%M:%S"),
                next_dt.strftime("%Y/%m/%d %H:%M:%S")
            ))
            current_dt = next_dt
        
        return time_segments
    
    def load_taz_ids(self, taz_file: str) -> List[str]:
        """
        从TAZ文件中加载TAZ ID列表
        
        Args:
            taz_file: TAZ文件路径
            
        Returns:
            TAZ ID列表
        """
        try:
            tree = ET.parse(taz_file)
            root = tree.getroot()
            
            taz_ids = []
            for taz in root.findall('.//taz'):
                taz_id = taz.get('id')
                if taz_id:
                    taz_ids.append(taz_id)
            
            logger.info(f"从TAZ文件加载了 {len(taz_ids)} 个TAZ ID")
            return taz_ids
            
        except Exception as e:
            logger.error(f"加载TAZ文件失败: {e}")
            return []
    
    def load_single_direction_tazs(self, taz_file: str) -> Dict[str, str]:
        """
        从TAZ文件中加载单向TAZ信息
        
        Args:
            taz_file: TAZ文件路径
            
        Returns:
            单向TAZ字典 {taz_id: 'source'|'sink'}
        """
        try:
            tree = ET.parse(taz_file)
            root = tree.getroot()
            
            single_direction_tazs = {}
            for taz in root.findall('.//taz'):
                taz_id = taz.get('id')
                if taz_id:
                    # 检查是否有source或sink属性
                    if taz.get('source') == 'true':
                        single_direction_tazs[taz_id] = 'source'
                    elif taz.get('sink') == 'true':
                        single_direction_tazs[taz_id] = 'sink'
            
            logger.info(f"从TAZ文件加载了 {len(single_direction_tazs)} 个单向TAZ")
            return single_direction_tazs
            
        except Exception as e:
            logger.error(f"加载单向TAZ信息失败: {e}")
            return {}
    
    def filter_od_by_taz(self, od_data: pd.DataFrame, taz_ids: List[str]) -> pd.DataFrame:
        """
        筛选OD数据，删除起点或终点不在TAZ ID列表中的数据
        
        Args:
            od_data: OD数据DataFrame
            taz_ids: TAZ ID列表
            
        Returns:
            筛选后的OD数据
        """
        logger.info("开始按TAZ ID筛选OD数据")
        
        # 创建筛选掩码
        mask = od_data['start_square_code'].isin(taz_ids) & od_data['end_square_code'].isin(taz_ids)
        filtered_data = od_data[mask]
        
        filtered_count = len(od_data) - len(filtered_data)
        logger.info(f"筛选掉不在TAZ ID列表中的OD对数量: {filtered_count}")
        
        return filtered_data
    
    def filter_invalid_od_data(self, od_data: pd.DataFrame, single_direction_tazs: Dict[str, str]) -> pd.DataFrame:
        """
        筛选无效的OD数据（考虑单向TAZ约束）
        
        Args:
            od_data: OD数据DataFrame
            single_direction_tazs: 单向TAZ字典
            
        Returns:
            筛选后的OD数据
        """
        logger.info("开始按单向TAZ约束筛选OD数据")
        
        # 统计单向TAZ的数量
        source_only_tazs = [k for k, v in single_direction_tazs.items() if v == 'source']
        sink_only_tazs = [k for k, v in single_direction_tazs.items() if v == 'sink']
        
        logger.info(f"单向TAZ统计: 仅起点TAZ: {len(source_only_tazs)}, 仅终点TAZ: {len(sink_only_tazs)}")
        
        # 创建筛选掩码
        # 起点不能是sink_only的TAZ
        valid_source = ~od_data['start_square_code'].isin(sink_only_tazs)
        # 终点不能是source_only的TAZ
        valid_dest = ~od_data['end_square_code'].isin(source_only_tazs)
        
        # 组合筛选条件
        valid_mask = valid_source & valid_dest
        filtered_data = od_data[valid_mask]
        
        invalid_count = len(od_data) - len(filtered_data)
        if len(od_data) > 0:
            invalid_percentage = invalid_count / len(od_data) * 100
            logger.info(f"因单向TAZ约束筛选掉的OD对数量: {invalid_count}, 占比: {invalid_percentage:.2f}%")
            
            if invalid_percentage > 20:
                logger.warning(f"警告: 单向TAZ约束筛选掉了大量OD对 ({invalid_percentage:.2f}%)，请检查TAZ文件是否正确!")
        
        return filtered_data
    
    def process_vehicle_types(self, od_data: pd.DataFrame) -> pd.DataFrame:
        """
        处理车辆类型映射
        
        Args:
            od_data: OD数据DataFrame
            
        Returns:
            处理后的OD数据
        """
        logger.info("开始处理车辆类型映射")
        
        # 添加车辆分类字段
        od_data = od_data.copy()
        od_data['vehicle_category'] = od_data['vehicle_type'].map(self.vehicle_mapping)
        
        # 统计车辆类型分布
        vehicle_counts = od_data['vehicle_category'].value_counts()
        logger.info(f"车辆类型分布: {vehicle_counts.to_dict()}")
        
        return od_data
    
    def aggregate_od_data(self, od_data: pd.DataFrame) -> pd.DataFrame:
        """
        聚合OD数据
        
        Args:
            od_data: OD数据DataFrame
            
        Returns:
            聚合后的OD数据
        """
        logger.info("开始聚合OD数据")
        
        # 按OD对和车辆类型聚合
        aggregated = od_data.groupby(
            ['start_square_code', 'end_square_code', 'vehicle_category'], 
            as_index=False
        ).size().rename(columns={'size': 'count'})
        
        logger.info(f"聚合后得到 {len(aggregated)} 个OD对")
        
        return aggregated
    
    def generate_flow_data(self, aggregated_od: pd.DataFrame, segment_start_sec: int, 
                          segment_end_sec: int) -> pd.DataFrame:
        """
        生成流量数据
        
        Args:
            aggregated_od: 聚合后的OD数据
            segment_start_sec: 时间段开始时间（秒）
            segment_end_sec: 时间段结束时间（秒）
            
        Returns:
            流量数据DataFrame
        """
        logger.info("开始生成流量数据")
        
        # 计算时间段时长（小时）
        segment_duration_hours = (segment_end_sec - segment_start_sec) / 3600
        
        # 计算每小时车辆数
        flow_data = aggregated_od.copy()
        flow_data['vehsPerHour'] = flow_data['count'] / segment_duration_hours
        
        # 添加时间信息
        flow_data['begin'] = segment_start_sec
        flow_data['end'] = segment_end_sec
        
        # 重命名列以符合SUMO格式
        flow_data = flow_data.rename(columns={
            'start_square_code': 'fromTaz',
            'end_square_code': 'toTaz',
            'vehicle_category': 'vtype'
        })
        
        logger.info(f"生成了 {len(flow_data)} 条流量数据")
        
        return flow_data
    
    def generate_od_xml(self, od_matrix: pd.DataFrame, start_time: str, end_time: str, 
                         output_file: str) -> None:
         """
         生成OD XML文件
         
         Args:
             od_matrix: OD矩阵DataFrame（可为长表包含fromTaz/toTaz/vehsPerHour，或为以fromTaz为index、toTaz为columns的透视矩阵，值为车辆总数或速率）
             start_time: 开始时间
             end_time: 结束时间
             output_file: 输出文件路径
         """
         logger.info(f"开始生成OD XML文件: {output_file}")
         
         # 创建XML根元素
         root = ET.Element("od-matrix")
         root.set("id", "od_matrix")
         root.set("begin", "0")
         root.set("end", str(self.calculate_duration(start_time, end_time)))
         
         # 根据输入数据结构写入
         try:
             if {'fromTaz', 'toTaz', 'vehsPerHour'}.issubset(set(od_matrix.columns)):
                 # 长表，直接写
                 for _, row in od_matrix.iterrows():
                     od_pair = ET.SubElement(root, "od")
                     od_pair.set("from", str(row['fromTaz']))
                     od_pair.set("to", str(row['toTaz']))
                     od_pair.set("vehsPerHour", str(float(row['vehsPerHour'])))
             else:
                 # 透视矩阵：index为fromTaz，columns为toTaz，值为车辆总数或速率
                 total_hours = max(1e-6, self.calculate_duration(start_time, end_time) / 3600)
                 for from_taz, row in od_matrix.iterrows():
                     for to_taz, value in row.items():
                         vehs_per_hour = float(value)
                         # 如果值看起来像总车辆数（非速率），则转为速率
                         if vehs_per_hour > 1e6 or vehs_per_hour == int(vehs_per_hour):
                             vehs_per_hour = vehs_per_hour / total_hours
                         od_pair = ET.SubElement(root, "od")
                         od_pair.set("from", str(from_taz))
                         od_pair.set("to", str(to_taz))
                         od_pair.set("vehsPerHour", str(vehs_per_hour))
         except Exception as e:
             logger.error(f"写入OD矩阵失败: {e}")
             raise
         
         # 写入文件
         tree = ET.ElementTree(root)
         tree.write(output_file, encoding='utf-8', xml_declaration=True)
         
         logger.info(f"OD XML文件生成完成: {output_file}")
    
    def generate_rou_xml(self, flow_df: pd.DataFrame, output_file: str) -> None:
        """
        生成SUMO路由文件（基于TAZ流）
        需要列：fromTaz, toTaz, vtype, begin, end, vehsPerHour
        """
        logger.info(f"开始生成ROU XML文件: {output_file}")
        root = ET.Element("routes")
        # 车辆类型定义
        for vt in sorted(set(flow_df.get('vtype', []))):
            v = ET.SubElement(root, "vType")
            v.set("id", str(vt))
            # 基础占位属性，可根据需要微调
            v.set("accel", "1.0"); v.set("decel", "4.5"); v.set("sigma", "0.5")
            v.set("length", "5"); v.set("maxSpeed", "27.78")
        # flows
        for i, row in flow_df.iterrows():
            f = ET.SubElement(root, "flow")
            f.set("id", f"f{i}")
            f.set("begin", str(int(row['begin'])))
            f.set("end", str(int(row['end'])))
            f.set("fromTaz", str(row['fromTaz']))
            f.set("toTaz", str(row['toTaz']))
            if 'vtype' in row and pd.notnull(row['vtype']):
                f.set("type", str(row['vtype']))
            f.set("vehsPerHour", str(float(row['vehsPerHour'])))
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        logger.info(f"ROU XML文件生成完成: {output_file}")
    
    def process_od_data(self, db_connection, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理OD数据的主函数
        
        Args:
            db_connection: 数据库连接
            request: 请求参数
            
        Returns:
            处理结果
        """
        try:
            start_time = request['start_time']
            end_time = request['end_time']
            interval_minutes = request.get('interval_minutes', 5)
            taz_file = request['taz_file']
            net_file = request['net_file']
            schemas_name = request.get('schemas_name', 'dwd')
            table_name = request.get('table_name')
            output_dir = request.get('output_dir')
            
            logger.info(f"开始处理OD数据(单SQL): {start_time} 到 {end_time}，间隔 {interval_minutes} 分钟")
            
            # 计算总时长
            total_duration = self.calculate_duration(start_time, end_time)
            
            # 加载TAZ信息
            taz_ids = self.load_taz_ids(taz_file)
            single_direction_tazs = self.load_single_direction_tazs(taz_file)
            source_only_tazs = [k for k, v in single_direction_tazs.items() if v == 'source']
            sink_only_tazs = [k for k, v in single_direction_tazs.items() if v == 'sink']
            
            if not taz_ids:
                raise Exception(f"无法加载TAZ文件: {taz_file}")
            
            # 输出目录
            if output_dir:
                run_folder = output_dir
            else:
                current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                run_folder = f"run_{current_time}"
            os.makedirs(run_folder, exist_ok=True)
            
            # 生成文件名
            def gen_file(ext):
                filename = f"{table_name}_{start_time.replace('/', '').replace(' ', '').replace(':', '')}_{end_time.replace('/', '').replace(' ', '').replace(':', '')}{ext}"
                return os.path.join(run_folder, filename)
            
            od_file = gen_file(".od.xml")
            route_file = gen_file(".rou.xml")
            sumocfg_file = os.path.join(run_folder, "simulation.sumocfg")
 
            # 单SQL：在数据库内完成5分钟分桶与聚合以及车辆类型映射
            base_sql = f"""
            WITH params AS (
              SELECT 
                TO_TIMESTAMP(%s, 'YYYY/MM/DD HH24:MI:SS') AS start_ts,
                TO_TIMESTAMP(%s, 'YYYY/MM/DD HH24:MI:SS') AS end_ts,
                %s::int AS interval_min
            )
            SELECT
              s."fromTaz", s."toTaz", s."vtype",
              EXTRACT(EPOCH FROM s.ts_begin - p.start_ts)::int AS begin,
              EXTRACT(EPOCH FROM s.ts_end   - p.start_ts)::int AS end,
              (s.cnt::double precision) * (3600.0 / EXTRACT(EPOCH FROM (s.ts_end - s.ts_begin))) AS "vehsPerHour"
            FROM (
              SELECT
                date_bin((p.interval_min||' minutes')::interval, t."start_time", p.start_ts)                                               AS ts_begin,
                date_bin((p.interval_min||' minutes')::interval, t."start_time", p.start_ts) + (p.interval_min||' minutes')::interval     AS ts_end,
                COALESCE(NULLIF(t."start_square_code", ''), t."start_station_code")                                                        AS "fromTaz",
                COALESCE(NULLIF(t."end_square_code", ''),   t."end_station_code")                                                          AS "toTaz",
                CASE
                  WHEN t."vehicle_type" IN ('k1','k2')              THEN 'passenger_small'
                  WHEN t."vehicle_type" IN ('k3','k4')              THEN 'passenger_large'
                  WHEN t."vehicle_type" IN ('h1','h2')              THEN 'truck_small'
                  WHEN t."vehicle_type" IN ('h3','h4','h5','h6')    THEN 'truck_large'
                  WHEN t."vehicle_type" IN ('t1')                   THEN 'bus_small'
                  WHEN t."vehicle_type" IN ('t2','t3','t4')         THEN 'bus_large'
                  ELSE 'passenger_small'
                END AS "vtype",
                COUNT(*)::bigint AS cnt
              FROM "{schemas_name}"."{table_name}" t
              CROSS JOIN params p
              WHERE t."start_time" >= p.start_ts AND t."start_time" < p.end_ts
            {{TAZ_FILTERS}}
              GROUP BY 1,2,3,4,5
            ) s
            CROSS JOIN params p
            """
             
            # 构建可选TAZ过滤片段
            filters = []
            params: List[Any] = [start_time, end_time, interval_minutes]
            # 限定在TAZ列表内
            if taz_ids:
                filters.append("AND COALESCE(NULLIF(t.\"start_square_code\", ''), t.\"start_station_code\") = ANY(%s)")
                params.append(taz_ids)
                filters.append("AND COALESCE(NULLIF(t.\"end_square_code\", ''),   t.\"end_station_code\")   = ANY(%s)")
                params.append(taz_ids)
            # 单向TAZ约束（起点不能是sink-only；终点不能是source-only）
            if sink_only_tazs:
                filters.append("AND NOT (COALESCE(NULLIF(t.\"start_square_code\", ''), t.\"start_station_code\") = ANY(%s))")
                params.append(sink_only_tazs)
            if source_only_tazs:
                filters.append("AND NOT (COALESCE(NULLIF(t.\"end_square_code\", ''),   t.\"end_station_code\")   = ANY(%s))")
                params.append(source_only_tazs)
             
            sql = base_sql.replace("{TAZ_FILTERS}", ("\n" + "\n".join(filters)) if filters else "")
            logger.info("执行单SQL聚合查询...")
             
            cur = db_connection.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            cur.close()
             
            if not rows:
                raise Exception("指定时间窗内无数据")
             
            flow_df = pd.DataFrame(rows, columns=colnames)
            logger.info(f"聚合查询返回 {len(flow_df)} 行")
 
            # 计算车辆数：vehsPerHour * (每bucket时长小时)
            bucket_hours = interval_minutes / 60.0
            flow_df['vehicle_count'] = flow_df['vehsPerHour'].astype(float) * bucket_hours
             
            # 按OD对聚合得到整窗OD矩阵
            od_matrix_df = flow_df.groupby(['fromTaz', 'toTaz'], as_index=False)['vehicle_count'].sum()
            od_matrix = od_matrix_df.pivot(index='fromTaz', columns='toTaz', values='vehicle_count').fillna(0)
 
            # 生成文件
            self.generate_od_xml(od_matrix, start_time, end_time, od_file)
            self.generate_rou_xml(flow_df, route_file)
             
            logger.info("OD数据处理完成(单SQL)")
             
            return {
                "success": True,
                "run_folder": run_folder,
                "od_file": os.path.abspath(od_file),
                "route_file": os.path.abspath(route_file),
                "sumocfg_file": os.path.abspath(sumocfg_file),
                "total_records": int(len(flow_df)),
                "od_pairs": int(len(od_matrix_df))
            }
        except Exception as e:
            logger.error(f"OD数据处理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            } 