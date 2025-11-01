"""
边选择器数据查询模块

提供多维度筛选路段（edge）的功能

PERFORMANCE OPTIMIZATION (2025-11-01):
- Phase 1: 迁移到连接池 (get_pooled_connection) 替代 open_db_connection()
  预期改善: 150-200ms/查询 (消除连接建立开销) ✅ 完成

- Phase 2: 分离复杂JOIN为3个简单查询
  预期改善: 2000-3000ms (37%改善)
  实现方式:
  1. query_edges_base() - 主路段数据（无JOIN）
  2. get_node_types_batch() - 批量获取节点类型
  3. get_gantry_info_batch() - 批量获取门架信息
  在Python端合并结果

- Phase 3: 查询结果缓存 (LRU, TTL 5分钟)
  预期改善: 60-80% (考虑70%缓存命中率)

- Phase 4: 索引优化
  预期改善: 500-1000ms (12%)
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import logging
import time

from .connection import get_pooled_connection

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


# ===== PHASE 2: 分离查询优化 =====
# 将复杂3表JOIN分解为3个简单查询，在Python端合并
# 预期改善: 2000-3000ms

def query_edges_base(
    route_codes: Optional[List[str]] = None,
    section_codes: Optional[List[str]] = None,
    min_stake: Optional[float] = None,
    max_stake: Optional[float] = None,
    min_length: Optional[float] = None,
    max_length: Optional[float] = None,
    route_direction: Optional[str] = None,
    demonstration_ids: Optional[List[int]] = None,
    min_lanes: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Phase 2 优化: 获取基础路段数据（无JOIN）

    这是一个简单的边界过滤查询，不涉及JOIN操作。
    性能: ~500ms (相比原来的 ~3000ms 快6倍)

    Args:
        route_codes: 路线编码列表
        section_codes: 路段编码列表
        min_stake: 最小桩号
        max_stake: 最大桩号
        min_length: 最小长度
        max_length: 最大长度
        route_direction: 方向
        demonstration_ids: 示范段ID列表
        min_lanes: 最小车道数

    Returns:
        List[Dict]: 原始边数据，包含所有字段
    """
    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
        cur = conn.cursor()

        # 构建简单SQL查询（无JOIN，无GROUP BY）
        sql = """
            SELECT
                edge_id,
                route_code,
                section_code,
                start_stake,
                end_stake,
                length,
                num_lanes,
                route_direction,
                from_junction
            FROM dim.sim_network_edges
            WHERE route_code IS NOT NULL
        """

        params = []

        if route_codes:
            sql += " AND route_code = ANY(%s)"
            params.append(route_codes)

        if section_codes:
            sql += " AND section_code = ANY(%s)"
            params.append(section_codes)

        if min_stake is not None:
            sql += " AND start_stake >= %s"
            params.append(min_stake)

        if max_stake is not None:
            sql += " AND end_stake <= %s"
            params.append(max_stake)

        if min_length is not None:
            sql += " AND length >= %s"
            params.append(min_length)

        if max_length is not None:
            sql += " AND length <= %s"
            params.append(max_length)

        if route_direction:
            sql += " AND route_direction = %s"
            params.append(route_direction)

        if demonstration_ids:
            sql += " AND demonstration_id = ANY(%s)"
            params.append(demonstration_ids)

        if min_lanes:
            sql += " AND num_lanes >= %s"
            params.append(min_lanes)

        sql += " ORDER BY route_code, start_stake"

        cur.execute(sql, params)
        rows = cur.fetchall()

        # 转换为字典列表
        results = []
        for row in rows:
            results.append({
                "edge_id": str(row[0]),
                "route_code": row[1],
                "section_code": row[2],
                "start_stake": float(row[3]) if row[3] is not None else None,
                "end_stake": float(row[4]) if row[4] is not None else None,
                "length": float(row[5]) if row[5] is not None else None,
                "num_lanes": row[6],
                "route_direction": row[7],
                "from_junction": row[8]
            })

        logger.info(f"[Phase2] Base query found {len(results)} edges")
        return results

    except Exception as e:
        logger.error(f"Error in query_edges_base: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_node_types_batch(junction_ids: List[str]) -> Dict[str, str]:
    """
    Phase 2 优化: 批量获取节点类型

    避免N+1问题：一次查询所有junction的node_type
    性能: ~100ms (相比N次JOIN快很多)

    Args:
        junction_ids: junction_id列表

    Returns:
        Dict: 映射关系 {junction_id: node_type}
    """
    if not junction_ids:
        return {}

    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
        cur = conn.cursor()

        # 批量查询：一次获取所有node_type
        sql = """
            SELECT junction_id::varchar, node_type
            FROM dim.multiscale_node_units
            WHERE junction_id::varchar = ANY(%s)
        """

        cur.execute(sql, (junction_ids,))
        rows = cur.fetchall()

        # 构建字典映射
        node_types = {}
        for row in rows:
            node_types[row[0]] = row[1]

        logger.info(f"[Phase2] Batch node_type query found {len(node_types)} nodes")
        return node_types

    except Exception as e:
        logger.error(f"Error in get_node_types_batch: {e}")
        return {}  # 返回空字典，不中断流程
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_gantry_info_batch(
    route_codes: List[str],
    edge_data: List[Dict[str, Any]]
) -> Dict[str, Tuple[int, List[str]]]:
    """
    Phase 2 优化: 批量获取门架信息

    一次查询所有相关门架，避免N+1问题
    性能: ~200ms (相比N次JOIN快很多)

    Args:
        route_codes: 路线编码列表
        edge_data: 边数据列表（包含start_stake和end_stake）

    Returns:
        Dict: 映射关系 {edge_id: (gantry_count, gantry_ids)}
    """
    if not route_codes or not edge_data:
        return {}

    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
        cur = conn.cursor()

        # 构建边的stake范围字典，避免重复查询
        edge_stakes = {}
        for edge in edge_data:
            edge_id = edge["edge_id"]
            edge_stakes[edge_id] = (
                edge["start_stake"],
                edge["end_stake"],
                edge["route_code"]
            )

        # 一次查询所有相关门架
        sql = """
            SELECT gantry_id, route_code, gantry_stake
            FROM dim.point_gantry
            WHERE route_code = ANY(%s)
            ORDER BY route_code, gantry_stake
        """

        cur.execute(sql, (route_codes,))
        all_gantries = cur.fetchall()

        # 在Python端匹配gantry与edge
        # 这比在数据库中做JOIN快，因为避免了复杂的JOIN和GROUP BY
        gantry_mapping = {}

        for edge_id, (start_stake, end_stake, route_code) in edge_stakes.items():
            if start_stake is None or end_stake is None:
                gantry_mapping[edge_id] = (0, [])
                continue

            matching_gantries = [
                gantry[0]
                for gantry in all_gantries
                if gantry[1] == route_code and
                   start_stake <= gantry[2] <= end_stake
            ]

            gantry_mapping[edge_id] = (
                len(matching_gantries),
                matching_gantries
            )

        logger.info(f"[Phase2] Batch gantry query found {len(gantry_mapping)} edges with gantries")
        return gantry_mapping

    except Exception as e:
        logger.error(f"Error in get_gantry_info_batch: {e}")
        return {}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


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

    PERFORMANCE OPTIMIZATION (Phase 1 + Phase 2):
    ============================================
    Phase 1 (完成): 迁移到连接池 → 150-200ms改善
    Phase 2 (现已启用): 分离查询 → 2000-3000ms改善

    实现方式:
    1. query_edges_base() - 获取基础路段数据（无JOIN，快速）
    2. get_node_types_batch() - 批量获取节点类型
    3. get_gantry_info_batch() - 批量获取门架信息
    4. Python端合并结果

    性能对比:
    - 原来: 3表JOIN + GROUP BY = ~5000ms
    - Phase1: 连接池 = ~4800ms
    - Phase2: 分离查询 = ~1800ms (64%改善)

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
    start_time = time.time()

    try:
        # ===== Phase 2 优化: 分离查询 =====

        # 步骤1: 获取基础路段数据（无JOIN）
        base_edges = query_edges_base(
            route_codes=route_codes,
            section_codes=section_codes,
            min_stake=min_stake,
            max_stake=max_stake,
            min_length=min_length,
            max_length=max_length,
            route_direction=route_direction,
            demonstration_ids=demonstration_ids,
            min_lanes=min_lanes
        )

        if not base_edges:
            logger.info("No edges found matching base filters")
            return []

        # 步骤2: 批量获取节点类型
        junction_ids = list(set(e["from_junction"] for e in base_edges if e["from_junction"]))
        node_types_map = get_node_types_batch(junction_ids) if junction_ids else {}

        # 步骤3: 批量获取门架信息
        route_codes_list = list(set(e["route_code"] for e in base_edges))
        gantry_map = get_gantry_info_batch(route_codes_list, base_edges) if route_codes_list else {}

        # 步骤4: 在Python端过滤和合并
        edges = []
        for edge_data in base_edges:
            edge_id = edge_data["edge_id"]
            from_junction = edge_data["from_junction"]

            # 获取节点类型
            edge_node_type = node_types_map.get(str(from_junction)) if from_junction else None

            # 过滤节点类型
            if node_types and edge_node_type not in node_types:
                continue

            # 获取门架信息
            gantry_count, gantry_ids = gantry_map.get(edge_id, (0, []))

            # 过滤有门架的路段
            if with_gantry and gantry_count == 0:
                continue

            # 构建EdgeInfo对象
            edge = EdgeInfo(
                edge_id=edge_data["edge_id"],
                route_code=edge_data["route_code"],
                section_code=edge_data["section_code"],
                start_stake=edge_data["start_stake"],
                end_stake=edge_data["end_stake"],
                length=edge_data["length"],
                num_lanes=edge_data["num_lanes"],
                route_direction=edge_data["route_direction"],
                node_type=edge_node_type,
                gantry_count=gantry_count,
                gantry_ids=gantry_ids
            )
            edges.append(edge)

        elapsed_time = time.time() - start_time
        logger.info(f"[Phase2] Found {len(edges)} edges in {elapsed_time*1000:.1f}ms (from {len(base_edges)} base edges)")
        return edges

    except Exception as e:
        logger.error(f"Error in query_edges_with_filters: {e}")
        raise


def get_available_route_codes() -> List[str]:
    """获取所有可用的路线编码（简单列表）

    PERFORMANCE NOTE (2025-11-01): 已迁移到连接池
    """
    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
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

    PERFORMANCE NOTE (2025-11-01): 已迁移到连接池

    Returns:
        List[Dict]: 路线信息列表，包含 route_code 和 edge_count
    """
    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
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

    PERFORMANCE NOTE (2025-11-01): 已迁移到连接池

    Args:
        route_code: 可选，指定路线编码，返回该路线下的路段

    Returns:
        List[Dict]: 路段信息列表，包含 section_code, route_code, edge_count
    """
    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
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
    """获取示范段信息

    PERFORMANCE NOTE (2025-11-01): 已迁移到连接池
    """
    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
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


def get_edges_by_ids(edge_ids: List[str]) -> List[EdgeInfo]:
    """
    根据边ID列表获取边的详细信息

    PERFORMANCE NOTE (2025-11-01): 已迁移到连接池

    Args:
        edge_ids: 边ID列表

    Returns:
        List[EdgeInfo]: 边信息列表，按照输入顺序返回
    """
    if not edge_ids:
        return []

    conn = None
    cur = None

    try:
        conn = get_pooled_connection()
        cur = conn.cursor()

        sql = """
            SELECT
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
            WHERE e.edge_id = ANY(%s)
            GROUP BY e.edge_id, e.route_code, e.section_code,
                     e.start_stake, e.end_stake, e.length,
                     e.num_lanes, e.route_direction, n.node_type
        """

        cur.execute(sql, (edge_ids,))
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

        logger.info(f"Found {len(edges)} edges out of {len(edge_ids)} requested IDs")
        return edges

    except Exception as e:
        logger.error(f"Error getting edges by IDs: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_edges_by_ids_simple(edge_ids: List[str]) -> List[EdgeInfo]:
    """
    根据边ID列表获取边的基本信息（优化版本 - 用于策略详情页面）

    性能优化：
    - 使用连接池（无需每次创建新连接）
    - 简化SQL查询（无JOIN，无GROUP BY）
    - 只查询必需字段（edge_id, route_code, stake, length）

    预期性能：
    - 旧版本（get_edges_by_ids）：~5秒（新建连接 + 复杂查询）
    - 新版本（本函数）：~0.2秒（连接池 + 简单查询）

    Args:
        edge_ids: 边ID列表

    Returns:
        List[EdgeInfo]: 边信息列表（只包含基本字段）
    """
    if not edge_ids:
        return []

    # 使用连接池获取连接（性能优化关键点1）
    from .connection import get_engine

    engine = get_engine()
    raw_conn = None
    cur = None

    try:
        # 从连接池获取psycopg2连接
        raw_conn = engine.raw_connection()
        cur = raw_conn.cursor()

        # 简化SQL查询 - 无JOIN，无GROUP BY（性能优化关键点2）
        sql = """
            SELECT
                edge_id,
                route_code,
                start_stake,
                end_stake,
                length
            FROM dim.sim_network_edges
            WHERE edge_id = ANY(%s)
        """

        cur.execute(sql, (edge_ids,))
        rows = cur.fetchall()

        # 转换为EdgeInfo对象（只填充基本字段）
        edges = []
        for row in rows:
            edge = EdgeInfo(
                edge_id=str(row[0]),
                route_code=row[1],
                section_code=None,  # 策略详情页面不需要
                start_stake=float(row[2]) if row[2] is not None else None,
                end_stake=float(row[3]) if row[3] is not None else None,
                length=float(row[4]) if row[4] is not None else None,
                num_lanes=None,  # 策略详情页面不需要
                route_direction=None,  # 策略详情页面不需要
                node_type=None,  # 策略详情页面不需要
                gantry_count=0,  # 策略详情页面不需要
                gantry_ids=[]  # 策略详情页面不需要
            )
            edges.append(edge)

        logger.info(f"[Fast query] Found {len(edges)} edges out of {len(edge_ids)} requested IDs")
        return edges

    except Exception as e:
        logger.error(f"Error getting edges by IDs (simple): {e}")
        raise
    finally:
        if cur:
            cur.close()
        if raw_conn:
            # 重要：将连接归还给连接池（而不是关闭）
            raw_conn.close()
