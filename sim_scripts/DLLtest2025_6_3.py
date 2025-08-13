from fastapi import FastAPI, Depends
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import subprocess
import os
from datetime import datetime, timedelta
import json
import uvicorn
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Tuple

# 导入精度分析工具
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from accuracy_analysis import AccuracyAnalyzer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建连接池
connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname="sdzg",
    user="lsrns",
    password="Abcd@1234",
    host="10.149.235.123",
    port="5432"
)


def get_db_connection():
    try:
        conn = connection_pool.getconn()
        if conn:
            print("Successfully retrieved a database connection from the pool.")
            return conn
    except Exception as e:
        print(f"Failed to retrieve a database connection: {e}")
        return None


# Pydantic 模型用于接收 API 请求参数
class TimeRangeRequest(BaseModel):
    start_time: str
    end_time: str
    """数据库模式名称"""
    schemas_name: Optional[str] = "dwd"
    table_name: Optional[str] = "dwd_od_g4202"
    taz_file: Optional[str] = "TAZ_5_validated.add.xml"
    net_file: Optional[str] = "sichuan202503v6.net.xml"
    interval_minutes: Optional[int] = 5  # 默认5分钟间隔
    # 中观仿真选项
    enable_mesoscopic: Optional[bool] = False  # 是否启用中观仿真
    # SUMO输出选项
    output_summary: Optional[bool] = True
    output_tripinfo: Optional[bool] = False
    output_vehroute: Optional[bool] = False
    output_fcd: Optional[bool] = False
    output_netstate: Optional[bool] = False
    output_emission: Optional[bool] = False


class ProcessResult(BaseModel):
    run_folder: str
    od_file: str
    route_file: str
    sumocfg_file: str


"""-------------工具函数-------------"""


# 计算时间区间的时长（秒）
def calculate_duration(start_time, end_time):
    start = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
    end = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")
    duration = (end - start).total_seconds()
    return int(duration)


# 将时间区间分割成多个小时间段
def split_time_range(start_time: str, end_time: str, interval_minutes: int) -> List[Tuple[str, str]]:
    """
    将时间区间分割成多个指定长度的小时间段
    """
    start_dt = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")

    time_segments = []
    current_start = start_dt

    while current_start < end_dt:
        current_end = current_start + timedelta(minutes=interval_minutes)
        # 确保不超出结束时间
        if current_end > end_dt:
            current_end = end_dt

        time_segments.append((
            current_start.strftime("%Y/%m/%d %H:%M:%S"),
            current_end.strftime("%Y/%m/%d %H:%M:%S")
        ))

        current_start = current_end

    return time_segments


# 解析 TAZ.add.xml 文件，返回只作起点或终点的 TAZ ID
def load_single_direction_tazs(taz_file):
    # 确保使用绝对路径
    if not os.path.isabs(taz_file):
        taz_file = os.path.abspath(taz_file)

    try:
        print(f"Loading TAZ file from: {taz_file}")
        tree = ET.parse(taz_file)
        root = tree.getroot()

        single_direction_tazs = {}

        # 遍历每个 taz 元素
        for taz in root.findall("taz"):
            taz_id = taz.get("id")
            sources = [source.get("id") for source in taz.findall("tazSource")]
            sinks = [sink.get("id") for sink in taz.findall("tazSink")]

            # 判断该 TAZ 是否只有一条路
            if len(sources) == 1 and len(sinks) == 0:
                single_direction_tazs[taz_id] = 'source'  # 只能作为起点
            elif len(sinks) == 1 and len(sources) == 0:
                single_direction_tazs[taz_id] = 'sink'  # 只能作为终点

        print(f"Loaded {len(single_direction_tazs)} single-direction TAZs")
        return single_direction_tazs
    except Exception as e:
        print(f"Error loading TAZ file: {e}")
        return {}


# 筛选无效的 OD 数据
def filter_invalid_od_data(od_data, single_direction_tazs):
    valid_od_data = []

    for _, row in od_data.iterrows():
        origin = row['start_square_code']
        destination = row['end_square_code']

        # 如果 origin 或 destination 是只有一条路的 TAZ，检查是否正确
        if origin in single_direction_tazs:
            if single_direction_tazs[origin] == 'sink':  # 不能作为起点
                continue

        if destination in single_direction_tazs:
            if single_direction_tazs[destination] == 'source':  # 不能作为终点
                continue

        valid_od_data.append(row)

    return pd.DataFrame(valid_od_data)


def load_taz_ids(taz_file):
    # 确保使用绝对路径
    if not os.path.isabs(taz_file):
        taz_file = os.path.abspath(taz_file)

    """从 TAZ 文件中提取所有 TAZ ID"""
    print(f"Loading TAZ IDs from: {taz_file}")
    try:
        tree = ET.parse(taz_file)
        root = tree.getroot()

        taz_ids = set()
        for taz in root.findall("taz"):
            taz_id = taz.get("id")
            if taz_id:
                taz_ids.add(taz_id)

        print(f"Loaded {len(taz_ids)} TAZ IDs")
        return taz_ids
    except Exception as e:
        print(f"Error loading TAZ IDs: {e}")
        return set()


def filter_od_by_taz(od_data, taz_ids):
    """筛选 OD 数据，删除起点或终点不在 TAZ ID 列表中的数据"""
    print("Filtering OD data by TAZ IDs")
    valid_od_data = []

    for _, row in od_data.iterrows():
        origin = row['start_square_code']
        destination = row['end_square_code']

        # 如果起点或终点不在 TAZ ID 中，跳过这条数据
        if origin not in taz_ids or destination not in taz_ids:
            continue

        valid_od_data.append(row)

    print(f"Filtered {len(valid_od_data)} valid OD pairs")
    return pd.DataFrame(valid_od_data)


# 加入对缺失 start_square_code 和 end_square_code 的处理
def handle_missing_codes(row):
    # 如果 start_square_code 为空，用 start_station_code 替代
    if not row['start_square_code']:
        row['start_square_code'] = row['start_station_code']

    # 如果 end_square_code 为空，用 end_station_code 替代
    if not row['end_square_code']:
        row['end_square_code'] = row['end_station_code']

    return row


# 加载车辆类型配置和创建映射
def load_vehicle_config(config_path="vehicle_types.json"):
    # 确保使用绝对路径
    if not os.path.isabs(config_path):
        config_path = os.path.abspath(config_path)

    """加载车辆类型配置并建立映射关系"""
    print("Loading vehicle configuration")
    try:
        with open(config_path) as f:
            config = json.load(f)

        # 建立具体车辆ID到分类的映射（如 "k1" -> "passenger_small"）
        vehicle_mapping = {}
        for category, params in config["vehicle_types"].items():
            for vid in params["valid_ids"]:
                vehicle_mapping[vid] = category

        # 提取分类参数（去除不需要的字段）
        vehicle_params = {
            category: {k: str(v) for k, v in params.items() if k not in ["id_prefix", "valid_ids"]}
            for category, params in config["vehicle_types"].items()
        }

        print(f"Loaded vehicle mapping for {len(vehicle_mapping)} vehicle types")
        return vehicle_params, vehicle_mapping
    except Exception as e:
        print(f"Error loading vehicle config: {e}")
        return {}, {}


# 生成 OD XML 文件
def generate_od_xml(od_matrix, start_time, end_time, od_file):
    print(f"Generating OD XML file: {od_file}")
    root = ET.Element("demand")
    actor_config = ET.SubElement(root, "actorConfig", id="DEFAULT_VEHTYPE")
    time_slice = ET.SubElement(actor_config, "timeSlice", duration=str(calculate_duration(start_time, end_time) * 1000),
                               startTime="0")

    for origin, row in od_matrix.iterrows():
        for destination, value in row.items():
            if value > 0:
                ET.SubElement(time_slice, "odPair", amount=str(value), origin=origin, destination=destination)

    tree = ET.ElementTree(root)
    tree_str = ET.tostring(root, encoding="UTF-8", method="xml").decode()
    xml_str = minidom.parseString(tree_str).toprettyxml(indent="  ")

    with open(od_file, "w", encoding="UTF-8") as f:
        f.write(xml_str)
    print(f"OD XML file has been generated and saved as {od_file}")


def generate_rou_file(routes_root, flow_data):
    """
    生成路由文件，包含所有时间段的flow
    :param routes_root: 路由文件的根元素
    :param flow_data: 包含所有时间段flow数据的列表
    """
    # 先添加车辆类型定义
    vehicle_config, _ = load_vehicle_config()
    for category, params in vehicle_config.items():
        vtype = ET.SubElement(routes_root, "vType", id=category, **params)

    # 然后添加所有flow元素
    for flow in flow_data:
        ET.SubElement(routes_root, "flow", **flow)


# 生成 SUMO 配置文件
def generate_sumocfg(route_file, net_file, start_time, end_time, additional_file="TAZ_4.add.xml",
                     output_file="simulation.sumocfg", output_options=None, enable_mesoscopic=False):
    """
    仅旧版脚本使用的 sumocfg 生成函数。
    API 主流程已统一使用 api.utils.generate_sumocfg，请勿在后端代码中混用此实现。
    """
    print(f"Generating SUMO config file: {output_file}")
    # 计算仿真时长
    simulation_duration = calculate_duration(start_time, end_time)
    route_file_basename = os.path.basename(route_file)
    
    # 默认输出选项
    if output_options is None:
        output_options = {
            "summary": True,
            "tripinfo": False,
            "vehroute": False,
            "fcd": False,
            "netstate": False,
            "emission": False
        }

    root = ET.Element("configuration", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/sumoConfiguration.xsd"
    })

    # Input section
    input_elem = ET.SubElement(root, "input")
    ET.SubElement(input_elem, "net-file", value=str("../" + net_file))
    ET.SubElement(input_elem, "route-files", value=route_file_basename)
    
    # 支持多个附加文件
    additional_files = []
    # 添加TAZ文件
    additional_files.append(str("../" + additional_file))
    # 注意：E1检测器文件已在TAZ文件中包含，不需要单独添加
    
    ET.SubElement(input_elem, "additional-files", value=",".join(additional_files))

    # Time section
    time_elem = ET.SubElement(root, "time")
    ET.SubElement(time_elem, "begin", value="0")
    ET.SubElement(time_elem, "end", value=str(int(simulation_duration)))

    # Processing section (中观仿真配置)
    if enable_mesoscopic:
        processing_elem = ET.SubElement(root, "mesoscopic")
        ET.SubElement(processing_elem, "mesosim", value="true")
        print("Enabled mesoscopic simulation")

    # Output section
    output_elem = ET.SubElement(root, "output")
    
    # 基础统计输出（保持原有的）
    ET.SubElement(output_elem, "statistic-output", value="static.xml")
    ET.SubElement(output_elem, "duration-log.statistics", value="true")
    
    # 可选的输出文件
    if output_options.get("summary", False):
        ET.SubElement(output_elem, "summary-output", value="summary.xml")
        print("Added summary output")
    
    if output_options.get("tripinfo", False):
        ET.SubElement(output_elem, "tripinfo-output", value="tripinfo.xml")
        print("Added tripinfo output")
    
    if output_options.get("vehroute", False):
        ET.SubElement(output_elem, "vehroute-output", value="vehroute.xml")
        print("Added vehroute output")
    
    if output_options.get("fcd", False):
        ET.SubElement(output_elem, "fcd-output", value="fcd.xml")
        print("Added fcd output")
    
    if output_options.get("netstate", False):
        ET.SubElement(output_elem, "netstate-dump", value="netstate.xml")
        print("Added netstate output")
    
    if output_options.get("emission", False):
        ET.SubElement(output_elem, "emission-output", value="emission.xml")
        print("Added emission output")

    # GUI-only section
    gui_only_elem = ET.SubElement(root, "gui_only")
    ET.SubElement(gui_only_elem, "start", value="true")
    ET.SubElement(gui_only_elem, "quit-on-end", value="false")

    # Pretty print and save the sumocfg file
    tree = ET.ElementTree(root)
    tree_str = ET.tostring(root, encoding="UTF-8", method="xml").decode()
    xml_str = minidom.parseString(tree_str).toprettyxml(indent="  ")

    with open(output_file, "w", encoding="UTF-8") as f:
        f.write(xml_str)
    print(f"SUMO configuration file has been generated and saved as {output_file}")
    return output_file


# 启动 SUMO 仿真
def run_sumo(sumocfg_file, gui=True):
    print(f"Starting SUMO simulation with config: {sumocfg_file}")
    print(f"GUI mode: {'enabled' if gui else 'disabled'}")
    
    sumo_command = "sumo-gui" if gui else "sumo"
    command = f"{sumo_command} -c {sumocfg_file}"
    
    try:
        # 使用Popen而不是run，这样SUMO GUI可以独立运行
        if gui:
            print(f"Launching SUMO GUI with command: {command}")
            # 对于GUI模式，使用Popen让它在后台运行
            process = subprocess.Popen(command, shell=True)
            print(f"SUMO GUI launched with PID: {process.pid}")
            return process.pid
        else:
            # 对于非GUI模式，使用run等待完成
            print(f"Running SUMO command: {command}")
            result = subprocess.run(command, shell=True, check=True)
            print(f"SUMO simulation completed with return code: {result.returncode}")
            return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running SUMO simulation: {e}")
        print(f"Command: {command}")
        raise e


#从时间选择对应的表：
def get_year_from_date(date_str: str) -> int:
        """从日期字符串中提取年份"""
        from datetime import datetime
        return datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S').year

def is_2024_data(start_date: str) -> bool:
    """判断是否为2024年数据"""
    return get_year_from_date(start_date) == 2024
def get_table_names(start_date: str) -> dict:
    """根据年份获取对应的表名"""
    if is_2024_data(start_date):
        return {
            'od_table': 'dwd_od_g4202',
            'gantry_table': 'dwd_flow_gantry', 
            'onramp_table': 'dwd_flow_onramp',
            'offramp_table': 'dwd_flow_offramp'
        }
    else:
        return {
            'od_table': 'dwd_od_weekly',
            'gantry_table': 'dwd_flow_gantry_weekly',
            'onramp_table': 'dwd_flow_onramp_weekly', 
            'offramp_table': 'dwd_flow_offramp_weekly'
        }


@app.post("/process_od_data/", response_model=ProcessResult)
async def process_od_data(request: TimeRangeRequest, db_conn=Depends(get_db_connection)):
    start_time = request.start_time
    end_time = request.end_time
    schemas_name = request.schemas_name
    table_name = request.table_name
    taz_file = request.taz_file
    net_file = request.net_file
    interval_minutes = request.interval_minutes

    table_name= get_table_names(start_time)['od_table']

    # print(f"Processing OD data for table: {table_name}")
    # print(f"Start time: {start_time}, End time: {end_time}")
    # print(f"TAZ file: {taz_file}, Net file: {net_file}")
    # print(f"Using time interval: {interval_minutes} minutes")

    # 计算整个仿真时长
    total_duration = calculate_duration(start_time, end_time)

    # 将时间区间分割为多个小段
    time_segments = split_time_range(start_time, end_time, interval_minutes)
    # print(f"Split time range into {len(time_segments)} segments")

    # 加载TAZ ID和单向限制
    taz_ids = load_taz_ids(taz_file)
    single_direction_tazs = load_single_direction_tazs(taz_file)
    
    # 检查TAZ文件是否成功加载
    if not taz_ids:
        error_msg = f"无法加载TAZ文件: {taz_file}。请检查文件是否存在且格式正确。"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

    # 加载车辆类型配置
    vehicle_config, vehicle_mapping = load_vehicle_config()

    # 创建一个空的flow数据列表，用于收集所有时间段的flow
    all_flow_data = []

    # 获取当前时间，生成文件夹名称
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_folder = f"run_{current_time}"
    os.makedirs(run_folder, exist_ok=True)
    # print(f"Created run folder: {run_folder}")

    # 生成文件名
    def gen_file(ext):
        filename = f"{table_name}_{start_time.replace('/', '').replace(' ', '').replace(':', '')}_{end_time.replace('/', '').replace(' ', '').replace(':', '')}{ext}"
        return os.path.join(run_folder, filename)

    od_file = gen_file(".od.xml")
    route_file = gen_file(".rou.xml")
    sumocfg_file = os.path.join(run_folder, "simulation.sumocfg")

    # 为每个时间段创建OD文件和收集flow数据
    segment_counter = 0

    for seg_start, seg_end in time_segments:
        # print(f"Processing segment #{segment_counter}: {seg_start} to {seg_end}")

        # 获取当前时间段的时长（秒）
        segment_duration = calculate_duration(seg_start, seg_end)

        # 查询数据库获取当前时间段的数据
        cursor = db_conn.cursor()
        query = f'''
                    SELECT * FROM "{schemas_name}"."{table_name}" 
                    WHERE "start_time" >= TO_TIMESTAMP('{seg_start}', 'YYYY/MM/DD HH24:MI:SS')
                    AND "start_time" < TO_TIMESTAMP('{seg_end}', 'YYYY/MM/DD HH24:MI:SS');
                '''
        cursor.execute(query)
        print("Database query oddata executed successfully.")

        # 获取数据
        colnames = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        # print(f"Retrieved {len(data)} rows for segment #{segment_counter}")

        # 关闭当前游标
        cursor.close()

        if not data:
            print(f"No data in segment #{segment_counter}, skipping...")
            segment_counter += 1
            continue

        # 创建DataFrame
        df = pd.DataFrame(data, columns=colnames)


        # 处理缺失的收费广场代码（向量化处理）
        df['start_square_code'] = df['start_square_code'].where(df['start_square_code'].notnull() & (df['start_square_code'] != ''), df['start_station_code'])
        df['end_square_code'] = df['end_square_code'].where(df['end_square_code'].notnull() & (df['end_square_code'] != ''), df['end_station_code'])

        # 筛选OD数据，删除起点或终点不在TAZ ID中的数据（向量化处理）
        mask = df['start_square_code'].isin(taz_ids) & df['end_square_code'].isin(taz_ids)
        filtered_df = df[mask]
        taz_filtered_count = len(df) - len(filtered_df)
        print(f"筛选掉不在TAZ ID列表中的OD对数量: {taz_filtered_count}")

        # 筛选有效的OD数据（向量化处理）
        od_data = filtered_df[['start_square_code', 'end_square_code', 'vehicle_type']].copy()
        
        # 统计单向TAZ的数量和比例
        source_only_tazs = [k for k, v in single_direction_tazs.items() if v == 'source']
        sink_only_tazs = [k for k, v in single_direction_tazs.items() if v == 'sink']
        print(f"单向TAZ统计: 仅起点TAZ: {len(source_only_tazs)}, 仅终点TAZ: {len(sink_only_tazs)}, 总TAZ数: {len(taz_ids)}")
        
        # 防止除以零错误
        if len(taz_ids) > 0:
            single_taz_percentage = (len(source_only_tazs) + len(sink_only_tazs)) / len(taz_ids) * 100
            print(f"单向TAZ占比: {single_taz_percentage:.2f}%")
        else:
            print("警告: TAZ ID列表为空，无法计算单向TAZ占比")
            single_taz_percentage = 0
        
        # 统计被单向TAZ筛选的OD对
        invalid_source = od_data['start_square_code'].isin(sink_only_tazs)
        invalid_dest = od_data['end_square_code'].isin(source_only_tazs)
        invalid_od_count = sum(invalid_source | invalid_dest)
        
        # 标记无效OD
        is_valid = (~od_data['start_square_code'].isin(sink_only_tazs)) & \
                  (~od_data['end_square_code'].isin(source_only_tazs))
        filtered_od_data = od_data[is_valid]
        
        print(f"因单向TAZ约束筛选掉的OD对数量: {invalid_od_count}, 占比: {invalid_od_count / len(od_data) * 100:.2f}%")
        
        # 如果单向TAZ筛选比例过高，发出警告
        if invalid_od_count > 0 and invalid_od_count / len(od_data) > 0.2:  # 超过20%被筛选则警告
            print(f"警告: 单向TAZ约束筛选掉了大量OD对 ({invalid_od_count / len(od_data) * 100:.2f}%)，请检查TAZ文件是否正确!")

        # 将原始vehicle_type转换为分类（向量化）
        # 修改为使用.loc方式赋值，避免SettingWithCopyWarning
        filtered_od_data.loc[:, 'vehicle_category'] = filtered_od_data['vehicle_type'].map(vehicle_mapping)

        # 按分类统计OD数据
        od_vtype_counts = filtered_od_data.groupby(
            ['start_square_code', 'end_square_code', 'vehicle_category'], as_index=False
        ).size().rename(columns={'size': 'count'})

        # 计算当前时间段在总仿真时间中的起始和结束（秒）
        segment_start_sec = calculate_duration(start_time, seg_start)
        segment_end_sec = calculate_duration(start_time, seg_end)

        # 收集当前时间段的flow数据
        flow_id_start = len(all_flow_data)  # 从已有flow数量开始编号

        # 用itertuples替代iterrows加速
        for i, row in enumerate(od_vtype_counts.itertuples(index=False)):
            vehicle_count = row.count
            if segment_duration > 0:
                vehs_per_hour = (vehicle_count / segment_duration) * 3600
            else:
                vehs_per_hour = 0
            flow_id = flow_id_start + i
            flow_data = {
                "id": f"f_{flow_id}",
                "type": row.vehicle_category,
                "begin": str(segment_start_sec),
                "end": str(segment_end_sec),
                "fromTaz": row.start_square_code,
                "toTaz": row.end_square_code,
                "vehsPerHour": f"{vehs_per_hour:.2f}"
            }
            all_flow_data.append(flow_data)
            if i < 3:
                print(f"  Added flow for {row.start_square_code} -> {row.end_square_code}: "
                      f"vehsPerHour={vehs_per_hour:.2f} in [{segment_start_sec}, {segment_end_sec}]")

        # print(f"Segment #{segment_counter} added {len(od_vtype_counts)} flows")
        segment_counter += 1

    # 所有时间段处理完毕后，关闭数据库连接
    connection_pool.putconn(db_conn)

    # 创建路由文件根元素
    routes_root = ET.Element("routes")
    routes_root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    routes_root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")

    # 生成路由文件
    generate_rou_file(routes_root, all_flow_data)


    # 直接用ElementTree写入XML，避免minidom美化带来的性能损耗
    tree = ET.ElementTree(routes_root)
    tree.write(route_file, encoding="UTF-8", xml_declaration=True)
    print(f"Generated rou file with {len(all_flow_data)} flows: {route_file}")

    # 生成OD文件（可选，主要用于记录数据）
    print("Generating aggregated OD file...")
    # 用pandas DataFrame批量聚合OD流量
    flow_df = pd.DataFrame(all_flow_data)
    # 转换vehsPerHour为float
    # 检查flow_df是否为空或是否包含vehsPerHour列
    if not flow_df.empty and 'vehsPerHour' in flow_df.columns:
        flow_df['vehsPerHour'] = flow_df['vehsPerHour'].astype(float)
    else:
        print("警告: 没有有效的流量数据生成")
        flow_df['vehicle_count'] = []
    # 计算车辆数 = (每小时车辆数 * 总时长(小时))
    flow_df['vehicle_count'] = flow_df['vehsPerHour'] * (total_duration / 3600)
    # 按OD对聚合
    od_matrix_df = flow_df.groupby(['fromTaz', 'toTaz'], as_index=False)['vehicle_count'].sum()
    # 透视成矩阵
    od_matrix = od_matrix_df.pivot(index='fromTaz', columns='toTaz', values='vehicle_count').fillna(0)

    # 生成OD文件
    generate_od_xml(od_matrix, start_time, end_time, od_file)

    # 构建输出选项字典
    output_options = {
        "summary": request.output_summary,
        "tripinfo": request.output_tripinfo,
        "vehroute": request.output_vehroute,
        "fcd": request.output_fcd,
        "netstate": request.output_netstate,
        "emission": request.output_emission
    }

    # 生成SUMO配置文件
    generate_sumocfg(route_file, net_file, start_time, end_time, additional_file=taz_file,
                     output_file=sumocfg_file, output_options=output_options, 
                     enable_mesoscopic=request.enable_mesoscopic)

    # 返回的结果
    return ProcessResult(
        run_folder=run_folder,
        od_file=os.path.abspath(od_file),
        route_file=os.path.abspath(route_file),
        sumocfg_file=os.path.abspath(sumocfg_file)
    )


# 添加新的请求模型用于运行仿真
class SimulationRequest(BaseModel):
    run_folder: str
    od_file: str
    route_file: str
    sumocfg_file: str
    gui: bool = True  # 默认启用GUI，与前端保持一致

# 精度分析请求模型
class AccuracyAnalysisRequest(BaseModel):
    sim_folder: str  # 仿真结果文件夹路径
    start_time: Optional[str] = None  # 仿真开始时间（可选，系统会自动解析）
    end_time: Optional[str] = None    # 仿真结束时间（可选，系统会自动解析）
    detector_files: Optional[List[str]] = None  # 检测器配置文件列表（可选）

@app.post("/run_simulation/")
async def run_simulation(request: SimulationRequest):
    """运行SUMO模拟的API端点"""
    print(f"Starting simulation for: {request.run_folder}")
    print(f"Config file: {request.sumocfg_file}")
    print(f"GUI mode requested: {request.gui}")

    # 确保配置文件存在
    if not os.path.exists(request.sumocfg_file):
        return {"status": "Error", "message": f"Configuration file not found: {request.sumocfg_file}"}

    # 确保在配置文件所在目录运行
    run_folder = os.path.dirname(request.sumocfg_file)
    if run_folder:
        os.chdir(run_folder)
        print(f"Changed working directory to: {run_folder}")
    
    # 获取配置文件的基本名称
    sumocfg_basename = os.path.basename(request.sumocfg_file)

    try:
        # 运行SUMO
        result = run_sumo(sumocfg_basename, gui=request.gui)
        
        if request.gui:
            return {"status": "SUMO GUI launched", "run_folder": request.run_folder, "pid": result}
        else:
            return {"status": "Simulation completed", "run_folder": request.run_folder, "return_code": result}
    except Exception as e:
        return {"status": "Error", "message": str(e), "run_folder": request.run_folder}


@app.post("/analyze_accuracy/")
async def analyze_accuracy(request: AccuracyAnalysisRequest):
    """执行仿真精度分析的API端点"""
    print(f"开始精度分析: {request.sim_folder}")
    if request.start_time and request.end_time:
        print(f"用户指定时间范围: {request.start_time} ~ {request.end_time}")
    else:
        print("使用自动解析的时间范围")
    
    try:
        # 确保仿真文件夹存在
        if not os.path.exists(request.sim_folder):
            return {
                "success": False,
                "error": f"仿真文件夹不存在: {request.sim_folder}"
            }
        
        # 创建精度分析器
        analyzer = AccuracyAnalyzer(
            run_folder=request.sim_folder,
            output_base_folder="accuracy_analysis"
        )
        
        # 执行分析
        result = analyzer.analyze_accuracy()
        
        # 确保返回的数据可以被JSON序列化
        def convert_numpy_types(obj):
            import numpy as np
            import pandas as pd
            
            # 处理numpy类型
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif hasattr(obj, 'item'):  # 其他numpy类型
                return obj.item()
            
            # 处理pandas类型
            elif isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            
            # 处理容器类型
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_numpy_types(v) for v in obj)
            elif isinstance(obj, set):
                return list(convert_numpy_types(v) for v in obj)
            
            # 处理其他类型
            elif hasattr(obj, '__dict__'):
                return {k: convert_numpy_types(v) for k, v in obj.__dict__.items()}
            else:
                return obj
        
        # 转换numpy类型
        result = convert_numpy_types(result)
        
        if result['success']:
            print(f"精度分析完成: {result['output_folder']}")
            return {
                "success": True,
                "message": "精度分析完成",
                "result": result
            }
        else:
            print(f"精度分析失败: {result.get('error', '未知错误')}")
            return {
                "success": False,
                "error": result.get('error', '精度分析失败'),
                "output_folder": result.get('output_folder')
            }
            
    except Exception as e:
        error_msg = f"精度分析过程中出现异常: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


@app.get("/get_folders/{prefix}")
async def get_folders(prefix: str):
    """获取指定前缀的文件夹列表"""
    try:
        folders = []
        current_dir = os.getcwd()
        
        print(f"正在查找前缀为 '{prefix}' 的文件夹")
        print(f"当前工作目录: {current_dir}")
        
        # 扫描当前目录
        if os.path.exists("."):
            print(f"扫描当前目录: {os.path.abspath('.')}")
            for item in os.listdir("."):
                if item.startswith(prefix) and os.path.isdir(item):
                    folders.append(item)
                    print(f"找到文件夹: {item}")
        
        # 扫描accuracy_analysis子目录（用于精度分析结果）
        if prefix.startswith("accuracy_results_"):
            accuracy_dir = "accuracy_analysis"
            if os.path.exists(accuracy_dir):
                print(f"扫描精度分析目录: {os.path.abspath(accuracy_dir)}")
                for item in os.listdir(accuracy_dir):
                    if item.startswith(prefix) and os.path.isdir(os.path.join(accuracy_dir, item)):
                        folders.append(item)
                        print(f"找到精度分析结果文件夹: {item}")
            else:
                print(f"精度分析目录不存在: {accuracy_dir}")
        
        # 按时间倒序排列（最新的在前面）
        folders.sort(reverse=True)
        
        print(f"总共找到 {len(folders)} 个文件夹: {folders}")
        
        return {
            "success": True,
            "folders": folders,
            "count": len(folders),
            "current_directory": current_dir
        }
        
    except Exception as e:
        print(f"获取文件夹列表时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "folders": []
        }


@app.get("/accuracy_analysis_status/{result_folder}")
async def get_accuracy_analysis_status(result_folder: str):
    """获取精度分析结果状态"""
    try:
        result_path = os.path.join("accuracy_analysis", result_folder)
        
        if not os.path.exists(result_path):
            return {
                "exists": False,
                "message": "分析结果不存在"
            }
        
        # 检查结果文件
        html_report = os.path.join(result_path, "accuracy_report.html")
        csv_files = [
            "accuracy_results.csv",
            "gantry_accuracy_analysis.csv",
            "time_accuracy_analysis.csv",
            "detailed_records.csv",
            "anomaly_analysis.csv",
            "accuracy_raw_data.csv",
            "accuracy_cleaned_data.csv"
        ]
        
        files_status = {
            "html_report": os.path.exists(html_report),
            "csv_files": {f: os.path.exists(os.path.join(result_path, f)) for f in csv_files},
            "charts_folder": os.path.exists(os.path.join(result_path, "charts"))
        }
        
        return {
            "exists": True,
            "result_folder": result_folder,
            "result_path": result_path,
            "files_status": files_status
        }
        
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7999)