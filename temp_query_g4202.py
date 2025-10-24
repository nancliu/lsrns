"""
临时脚本：查询G4202路线的edge和entrance信息
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加路径
sys.path.insert(0, 'shared/data_access')
from connection import open_db_connection

def query_g4202_edges():
    """查询G4202的主线edge"""
    conn = open_db_connection()
    cursor = conn.cursor()

    query = '''
    SELECT
        sne.edge_id,
        sne.from_junction_id,
        sne.to_junction_id,
        sne.route_code,
        sne.section_code,
        sne.start_stake,
        sne.end_stake,
        sne.length,
        sne.num_lanes,
        sne.route_direction
    FROM dim.sim_network_edges sne
    WHERE sne.route_code = 'G4202'
        AND sne.demonstration_id = 1
        AND sne.num_lanes >= 3
    ORDER BY sne.start_stake
    LIMIT 15;
    '''

    cursor.execute(query)
    edges = cursor.fetchall()

    print('=' * 140)
    print('G4202路线主线edge信息（前15条，3车道及以上）：')
    print('=' * 140)
    print(f"{'Edge ID':<20} | {'From Junction':<15} | {'To Junction':<15} | {'Section':<12} | {'Stake Range':<18} | {'Length':<10} | {'Lanes':<6} | {'Direction':<12}")
    print('-' * 140)

    for row in edges:
        edge_id, from_j, to_j, route, section, start_stake, end_stake, length, lanes, direction = row
        stake_range = f"{start_stake:.3f}-{end_stake:.3f}km"
        length_str = f"{length:.1f}m"
        print(f"{edge_id:<20} | {from_j:<15} | {to_j:<15} | {section:<12} | {stake_range:<18} | {length_str:<10} | {lanes:<6} | {direction or 'N/A':<12}")

    conn.close()
    return edges

def query_g4202_entrances():
    """查询G4202的入口edge"""
    conn = open_db_connection()
    cursor = conn.cursor()

    query = '''
    SELECT
        sne.edge_id,
        sne.route_code,
        mnu.node_name,
        mnu.node_type,
        mnu.start_stake
    FROM dim.sim_network_edges sne
    JOIN dim.multiscale_node_units mnu
        ON sne.from_junction_id = mnu.junction_id
    WHERE sne.route_code = 'G4202'
        AND mnu.node_type = 'entrance'
        AND sne.demonstration_id = 1
    ORDER BY mnu.start_stake
    LIMIT 5;
    '''

    cursor.execute(query)
    entrances = cursor.fetchall()

    print('\n' + '=' * 100)
    print('G4202路线入口edge信息（前5条）：')
    print('=' * 100)
    print(f"{'Edge ID':<20} | {'Route':<8} | {'Node Name':<30} | {'Node Type':<12} | {'Stake':<10}")
    print('-' * 100)

    for row in entrances:
        edge_id, route, node_name, node_type, stake = row
        print(f"{edge_id:<20} | {route:<8} | {node_name or 'N/A':<30} | {node_type:<12} | {stake:.3f}km")

    conn.close()
    return entrances

if __name__ == '__main__':
    print('\n正在查询G4202路线信息...\n')
    edges = query_g4202_edges()
    entrances = query_g4202_entrances()

    print('\n' + '=' * 100)
    print('推荐测试配置：')
    print('=' * 100)
    if len(edges) >= 5:
        print(f"\nVSS/DHS测试路段（连续5条edge）：")
        for i in range(5):
            print(f"  - {edges[i][0]}")

    if len(entrances) >= 1:
        print(f"\nTEC测试入口：")
        print(f"  - {entrances[0][0]} ({entrances[0][2]})")

    print('\n查询完成！\n')
