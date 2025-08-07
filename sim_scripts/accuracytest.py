import os
import xml.etree.ElementTree as ET
import pandas as pd
import psycopg2
import numpy as np
from datetime import datetime, timedelta
import warnings

# 忽略特定的UserWarning
warnings.filterwarnings("ignore", category=UserWarning, message="pandas only supports SQLAlchemy connectable")

# 定义数据库连接参数
DB_NAME = "sdzg"
DB_USER = "lsrns"
DB_PASSWORD = "Abcd@1234"
DB_HOST = "10.149.235.123"
DB_PORT = "5432"

# 定义文件路径
ADDITIONAL_FILE = 'E1_detector.add.xml'  # 主 additional 文件路径
SIMDATA_FOLDER = 'simdata_1'  # 仿真数据文件夹路径

# 定义时间间隔（以分钟为单位）
TIME_INTERVAL = 5

# 定义仿真开始时间（模拟时间的起点）
SIMULATION_START_TIME = datetime.strptime("2024-08-22 16:00", "%Y-%m-%d %H:%M")

# 定义仿真结束时间
SIMULATION_END_TIME = datetime.strptime("2024-08-22 17:00", "%Y-%m-%d %H:%M")
# SIMULATION_END_TIME = datetime.strptime("2024-08-15 10:00", "%Y-%m-%d %H:%M")


# 定义GEH计算函数
def calculate_geh(E, V):
    """
    计算GEH指标
    E: 仿真流量 (nVehContrib)
    V: 观测流量 (nVehContrib)
    """
    denominator = (E + V) / 2
    if denominator == 0:
        return np.nan  # 避免除以零
    return np.sqrt(((E - V) ** 2) / denominator)


# Step 1: 解析 additional 文件，获取检测器及其关联的数据文件
def parse_additional_file(additional_file):
    """
    解析additional.xml文件，提取所有检测器的ID和关联的数据文件
    """
    if not os.path.exists(additional_file):
        print(f"additional 文件 {additional_file} 不存在。请检查路径。")
        return []

    tree = ET.parse(additional_file)
    root = tree.getroot()

    detectors = []
    for loop in root.findall('inductionLoop'):
        detector_id = loop.get('id')
        file_name = loop.get('file')
        lane_id = loop.get('lane')
        detectors.append({
            'detector_id': detector_id,
            'file': file_name,
            'lane_id': lane_id
        })
    if not detectors:
        print("未找到任何检测器。请检查 additional 文件内容。")
    return detectors


# Step 2: 读取仿真输出的XML文件
def read_simulation_data(detectors, simdata_folder, time_interval):
    """
    读取每个检测器的数据文件，提取车辆流量数据，并按 gantry_id 合并
    """
    data = []
    gantry_ids = set()

    for detector in detectors:
        detector_id = detector['detector_id']
        lane_id = detector['lane_id']
        file_name = detector['file']
        file_path = os.path.join(simdata_folder, file_name)

        if not os.path.exists(file_path):
            print(f"数据文件 {file_path} 不存在。")
            continue

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # 假设每个数据文件包含多个 <interval> 元素，每个元素有 'begin', 'end', 'nVehContrib' 属性
            for interval in root.findall('interval'):
                begin_time_sec = float(interval.get('begin'))  # 以秒为单位
                nVehContrib = interval.get('nVehContrib')

                if nVehContrib is None:
                    print(f"警告: {file_path} 中的 <interval> 元素缺少 'nVehContrib' 属性。")
                    continue

                # 将 begin_time 转换为分钟数
                interval_start_min = int(begin_time_sec // 60)  # 向下取整到分钟

                # 根据时间间隔进行分组
                interval_group = (interval_start_min // time_interval) * time_interval

                data.append({
                    'detector_id': detector_id,
                    'gantry_id': detector_id.split('_')[0],  # 提取 gantry_id（假设格式为 gantryID_laneIndex）
                    'lane_id': lane_id,
                    'interval_start': interval_group,  # 以分钟为单位
                    'sim_nVehContrib': float(nVehContrib)
                })

                gantry_ids.add(detector_id.split('_')[0])

        except ET.ParseError as e:
            print(f"解析 {file_path} 时出错: {e}")
        except Exception as e:
            print(f"处理 {file_path} 时出错: {e}")

    df_sim = pd.DataFrame(data)
    if df_sim.empty:
        print("仿真数据为空。请检查数据文件内容。")
        return df_sim, gantry_ids
    else:
        # 聚合每个 gantry_id 和时间间隔的流量
        df_sim_agg = df_sim.groupby(['gantry_id', 'interval_start']).agg({'sim_nVehContrib': 'sum'}).reset_index()
        return df_sim_agg, gantry_ids


# Step 3: 连接并查询 PostgreSQL 数据库
def read_observed_data(db_name, db_user, db_password, db_host, db_port, gantry_ids, sim_start_time, sim_end_time,
                       time_interval):
    """
    从 PostgreSQL 数据库中读取观测的车辆流量数据，并按 gantry_id 和时间间隔聚合
    """
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
    except psycopg2.Error as e:
        print(f"无法连接到数据库: {e}")
        return pd.DataFrame()

    # 构建查询语句
    try:
        query = """
            SELECT gantry_id, start_time, k1, k2, k3, k4, h1, h2, h3, h4, h5, h6
            FROM dwd.dwd_flow_gantry
            WHERE gantry_id = ANY(%s)
              AND start_time >= %s
              AND start_time < %s
        """
        df_obs = pd.read_sql_query(query, conn, params=(
            list(gantry_ids),
            sim_start_time,
            sim_end_time
        ))
    except Exception as e:
        print(f"查询数据库时出错: {e}")
        conn.close()
        return pd.DataFrame()

    conn.close()

    if df_obs.empty:
        print("观测数据为空。请检查数据库中的数据。")
        return df_obs

    # 打印查询结果的列名和前几行数据用于调试
    print("观测数据列名:", df_obs.columns.tolist())
    print("观测数据预览:")
    print(df_obs.head())

    # 确保 'start_time' 字段是 datetime 类型
    if not np.issubdtype(df_obs['start_time'].dtype, np.datetime64):
        df_obs['start_time'] = pd.to_datetime(df_obs['start_time'])

    # 计算时间间隔的起始时间，以分钟为单位
    df_obs['interval_start'] = df_obs['start_time'].apply(
        lambda x: int(((x - sim_start_time).total_seconds() // 60) // time_interval * time_interval)
    )

    # 计算总车辆数（nVehContrib，忽略车型）
    flow_columns = ['k1', 'k2', 'k3', 'k4', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    # 将流量列转换为数值类型，无法转换的值设为NaN
    df_obs[flow_columns] = df_obs[flow_columns].apply(pd.to_numeric, errors='coerce')
    df_obs['nVehContrib'] = df_obs[flow_columns].sum(axis=1)

    # 聚合每个 gantry_id 和时间间隔的车辆数
    df_obs_agg = df_obs.groupby(['gantry_id', 'interval_start']).agg({'nVehContrib': 'sum'}).reset_index()
    df_obs_agg.rename(columns={'nVehContrib': 'obs_nVehContrib'}, inplace=True)
    return df_obs_agg


# Step 4: 数据对齐与处理
def merge_data(df_sim, df_obs):
    """
    将仿真数据和观测数据合并
    """
    df_merged = pd.merge(df_obs, df_sim, on=['gantry_id', 'interval_start'], how='inner')
    if df_merged.empty:
        print("合并后的数据为空。请检查仿真数据和观测数据的匹配情况。")
    return df_merged


# Step 5: 计算GEH指标
def compute_geh(df):
    """
    在合并后的数据框中计算GEH指标
    """
    # 确保 'sim_nVehContrib' 和 'obs_nVehContrib' 是数值类型
    df['sim_nVehContrib'] = pd.to_numeric(df['sim_nVehContrib'], errors='coerce')
    df['obs_nVehContrib'] = pd.to_numeric(df['obs_nVehContrib'], errors='coerce')

    # 检查是否存在NaN值
    if df[['sim_nVehContrib', 'obs_nVehContrib']].isnull().any().any():
        print("警告: 存在 NaN 值，GEH 计算可能不准确。")
        # 可选择删除包含NaN的行
        df = df.dropna(subset=['sim_nVehContrib', 'obs_nVehContrib'])

    df['GEH'] = df.apply(lambda row: calculate_geh(row['sim_nVehContrib'], row['obs_nVehContrib']), axis=1)
    return df


# 主函数
def main():
    # Step 1: 解析 additional 文件
    print("解析 additional 文件，提取检测器信息...")
    detectors = parse_additional_file(ADDITIONAL_FILE)
    if not detectors:
        print("未找到任何检测器。请检查 additional 文件内容。")
        return

    print(f"找到 {len(detectors)} 个检测器。")

    # Step 2: 读取仿真数据
    print("读取仿真数据...")
    df_sim, gantry_ids = read_simulation_data(detectors, SIMDATA_FOLDER, TIME_INTERVAL)
    if df_sim.empty:
        print("没有仿真数据可处理。")
        return
    print("仿真数据读取成功。")

    # Step 3: 读取观测数据
    print("从 PostgreSQL 数据库读取观测数据...")
    df_obs = read_observed_data(
        DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
        gantry_ids,
        SIMULATION_START_TIME,
        SIMULATION_END_TIME,
        TIME_INTERVAL
    )
    if df_obs.empty:
        print("没有观测数据可处理。")
        return
    print("观测数据读取成功。")

    # Step 4: 合并数据
    print("合并仿真数据和观测数据...")
    df_merged = merge_data(df_sim, df_obs)
    if df_merged.empty:
        print("合并后的数据为空。无法计算GEH指标。")
        return
    print("数据合并成功。")

    # Step 5: 计算GEH
    print("计算GEH指标...")
    df_result = compute_geh(df_merged)

    # 输出结果
    output_file = 'geh_results.csv'
    df_result.to_csv(output_file, index=False)
    print(f"GEH计算完成。结果已保存到 {output_file}。")

    # 可选：输出GEH统计信息
    geh_summary = df_result['GEH'].describe()
    print("\nGEH指标统计信息:")
    print(geh_summary)

    # 可选：导出数据中 GEH 指标异常高或低的记录
    geh_threshold_high = 10
    geh_threshold_low = 5
    geh_anomalies = df_result[(df_result['GEH'] >= geh_threshold_high) | (df_result['GEH'] < geh_threshold_low)]
    if not geh_anomalies.empty:
        geh_anomalies_file = 'geh_anomalies.csv'
        geh_anomalies.to_csv(geh_anomalies_file, index=False)
        print(f"\nGEH 异常记录已保存到 {geh_anomalies_file}。")
    else:
        print("\n没有发现 GEH 异常记录。")


if __name__ == "__main__":
    main()
