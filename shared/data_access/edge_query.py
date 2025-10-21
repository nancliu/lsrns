"""
边选择器数据查询模块

提供多维度筛选路段（edge）的功能
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from .connection import open_db_connection

logger = logging.getLogger(__name__)


@dataclass
class EdgeInfo:
    """路段信息"""
    edge_id: str
    route_code: str
    section_code: Optional[str]
    start_stake: Optional[float]
    end_stake: Optional[float]
    length: Optional[float]
    num_lanes: Optional[int]
    route_direction: Optional[str]
    node_type: Optional[str]  # 关联节点类型
    gantry_count: int = 0
    gantry_ids: List[str] = None

    def __post_init__(self):
        if self.gantry_ids is None:
            self.gantry_ids = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "edge_id": self.edge_id,
            "route_code": self.route_code,
            "section_code": self.section_code,
            "start_stake": self.start_stake,
            "end_stake": self.end_stake,
            "length": self.length,
            "num_lanes": self.num_lanes,
            "route_direction": self.route_direction,
            "node_type": self.node_type,
            "gantry_count": self.gantry_count,
            "gantry_ids": self.gantry_ids
        }


def query_edges_with_filters(
    route_codes: Optional[List[str]] = None,
    section_codes: Optional[List[str]] = None,
    node_types: Optional[List[str]] = None,
    min_stake: Optional[float] = None,
    max_stake: Optional[float] = None,
    min_length: Optional[float] = None,
    max_length: Optional[float] = None,
    route_direction: Optional[str] = None,
    demonstration_ids: Optional[List[int]] = None,
    min_lanes: Optional[int] = None,
    with_gantry: bool = False
) -> List[EdgeInfo]:
    """
    多维度筛选路段

    Args:
        route_codes: 路线编码列表（如 G4202, SA2）
        section_codes: 路段编码列表（如 G4202001, SA002002）
        node_types: 节点类型（diverging/merging/entrance/exit）
        min_stake: 最小桩号（公里）
        max_stake: 最大桩号（公里）
        min_length: 最小长度（米）
        max_length: 最大长度（米）
        route_direction: 方向（clockwise/counterclockwise）
        demonstration_ids: 示范段ID列表
        min_lanes: 最小车道数
        with_gantry: 是否仅返回有门架的路段

    Returns:
        List[EdgeInfo]: 路段信息列表
    """
    conn = None
    cur = None

    try:
        conn = open_db_connection()
        cur = conn.cursor()

        # 构建SQL查询
        sql = """
            SELECT DISTINCT
                e.edge_id,
                e.route_code,
                e.section_code,
                e.start_stake,
                e.end_stake,
                e.length,
                e.num_lanes,
                e.route_direction,
                n.node_type,
                COUNT(g.gantry_id) as gantry_count,
                STRING_AGG(g.gantry_id, ',') as gantry_ids
            FROM dim.sim_network_edges e
            LEFT JOIN dim.multiscale_node_units n
              ON e.from_junction::varchar = n.junction_id
            LEFT JOIN dim.point_gantry g
              ON e.route_code = g.route_code
              AND g.gantry_stake BETWEEN e.start_stake AND e.end_stake
            WHERE 1=1
        """

        params = []

        if route_codes:
            sql += " AND e.route_code = ANY(%s)"
            params.append(route_codes)

        if section_codes:
            sql += " AND e.section_code = ANY(%s)"
            params.append(section_codes)

        if node_types:
            sql += " AND n.node_type = ANY(%s)"
            params.append(node_types)

        if min_stake is not None:
            sql += " AND e.start_stake >= %s"
            params.append(min_stake)

        if max_stake is not None:
            sql += " AND e.end_stake <= %s"
            params.append(max_stake)

        if min_length is not None:
            sql += " AND e.length >= %s"
            params.append(min_length)

        if max_length is not None:
            sql += " AND e.length <= %s"
            params.append(max_length)

        if route_direction:
            sql += " AND e.route_direction = %s"
            params.append(route_direction)

        if demonstration_ids:
            sql += " AND e.demonstration_id = ANY(%s)"
            params.append(demonstration_ids)

        if min_lanes:
            sql += " AND e.num_lanes >= %s"
            params.append(min_lanes)

        sql += """
            GROUP BY e.edge_id, e.route_code, e.section_code,
                     e.start_stake, e.end_stake, e.length,
                     e.num_lanes, e.route_direction, n.node_type
        """

        if with_gantry:
            sql += " HAVING COUNT(g.gantry_id) > 0"

        sql += " ORDER BY e.route_code, e.start_stake"

        logger.info(f"Executing edge query with filters: {params}")
        cur.execute(sql, params)
        rows = cur.fetchall()

        # 转换为EdgeInfo对象
        edges = []
        for row in rows:
            edge = EdgeInfo(
                edge_id=str(row[0]),
                route_code=row[1],
                section_code=row[2],
                start_stake=float(row[3]) if row[3] is not None else None,
                end_stake=float(row[4]) if row[4] is not None else None,
                length=float(row[5]) if row[5] is not None else None,
                num_lanes=row[6],
                route_direction=row[7],
                node_type=row[8],
                gantry_count=row[9] or 0,
                gantry_ids=row[10].split(',') if row[10] else []
            )
            edges.append(edge)

        logger.info(f"Found {len(edges)} edges matching filters")
        return edges

    except Exception as e:
        logger.error(f"Error querying edges: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_available_route_codes() -> List[str]:
    """获取所有可用的路线编码（简单列表）"""
    conn = None
    cur = None

    try:
        conn = open_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT route_code
            FROM dim.sim_network_edges
            WHERE route_code IS NOT NULL
            ORDER BY route_code
        """)
        route_codes = [row[0] for row in cur.fetchall()]
        return route_codes
    except Exception as e:
        logger.error(f"Error getting route codes: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_available_routes() -> List[Dict]:
    """
    获取所有可用的路线信息（带边数统计）

    Returns:
        List[Dict]: 路线信息列表，包含 route_code 和 edge_count
    """
    conn = None
    cur = None

    try:
        conn = open_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                route_code,
                COUNT(*) as edge_count
            FROM dim.sim_network_edges
            WHERE route_code IS NOT NULL
            GROUP BY route_code
            ORDER BY route_code
        """)
        results = [
            {
                "route_code": row[0],
                "edge_count": row[1]
            }
            for row in cur.fetchall()
        ]
        return results
    except Exception as e:
        logger.error(f"Error getting available routes: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_available_section_codes(route_code: Optional[str] = None) -> List[Dict]:
    """
    获取可用的路段编码

    Args:
        route_code: 可选，指定路线编码，返回该路线下的路段

    Returns:
        List[Dict]: 路段信息列表，包含 section_code, route_code, edge_count
    """
    conn = None
    cur = None

    try:
        conn = open_db_connection()
        cur = conn.cursor()

        sql = """
            SELECT
                section_code,
                route_code,
                COUNT(*) as edge_count,
                MIN(start_stake) as min_stake,
                MAX(end_stake) as max_stake
            FROM dim.sim_network_edges
            WHERE section_code IS NOT NULL
        """

        params = []
        if route_code:
            sql += " AND route_code = %s"
            params.append(route_code)

        sql += """
            GROUP BY section_code, route_code
            ORDER BY route_code, section_code
        """

        cur.execute(sql, params)
        results = [
            {
                "section_code": row[0],
                "route_code": row[1],
                "edge_count": row[2],
                "min_stake": float(row[3]) if row[3] else None,
                "max_stake": float(row[4]) if row[4] else None,
                "stake_range": f"K{row[3]:.2f}-K{row[4]:.2f}" if row[3] and row[4] else "N/A"
            }
            for row in cur.fetchall()
        ]
        return results
    except Exception as e:
        logger.error(f"Error getting section codes: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_available_sections(route_code: Optional[str] = None) -> List[Dict]:
    """
    获取可用的路段信息（别名，与 get_available_section_codes 相同）

    Args:
        route_code: 可选，指定路线编码，返回该路线下的路段

    Returns:
        List[Dict]: 路段信息列表，包含 section_code, route_code, edge_count, stake_range
    """
    return get_available_section_codes(route_code)


def get_demonstration_info() -> List[Dict]:
    """获取示范段信息"""
    conn = None
    cur = None

    try:
        conn = open_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT
                demonstration_id,
                route_code,
                COUNT(*) as edge_count,
                MIN(start_stake) as min_stake,
                MAX(end_stake) as max_stake
            FROM dim.sim_network_edges
            WHERE demonstration_id IS NOT NULL
            GROUP BY demonstration_id, route_code
            ORDER BY demonstration_id
        """)
        results = [
            {
                "demonstration_id": row[0],
                "route_code": row[1],
                "edge_count": row[2],
                "stake_range": f"{row[3]:.2f}-{row[4]:.2f}km"
            }
            for row in cur.fetchall()
        ]
        return results
    except Exception as e:
        logger.error(f"Error getting demonstration info: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
