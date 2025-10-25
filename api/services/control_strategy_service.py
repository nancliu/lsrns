"""
Control strategy service for managing road edge selection and control parameters.

This service provides business logic for filtering road segments using
multi-dimensional criteria and managing control strategy configurations.
"""

import logging
import time
from functools import wraps
from typing import List, Optional, Callable, Any, Dict
from sqlalchemy.exc import OperationalError, DBAPIError

from .base_service import BaseService
from shared.data_access.connection import get_pooled_connection
from shared.utilities.cache_utils import cached_with_ttl

logger = logging.getLogger(__name__)


def retry_on_db_failure(
    max_attempts: int = 2,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0
) -> Callable:
    """
    Decorator for retrying database operations with exponential backoff.

    Implements retry logic per FR-050 to FR-053:
    - Maximum 2 attempts (immediate first, retry after delay)
    - Exponential backoff (default: 0.5s, 1.0s)
    - Retries only on transient errors (connection timeout, refused)
    - Logs retry attempts with structured data

    Args:
        max_attempts: Maximum number of attempts (default: 2)
        initial_delay: Initial delay in seconds (default: 0.5)
        backoff_factor: Multiplier for delay (default: 2.0)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_db_failure(max_attempts=2, initial_delay=0.5)
        def query_database():
            return execute_query()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except (OperationalError, DBAPIError) as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Check if error is retryable
                    is_retryable = any([
                        'connection' in error_msg,
                        'timeout' in error_msg,
                        'refused' in error_msg
                    ])

                    if not is_retryable:
                        logger.error(
                            f"Non-retryable database error in {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "attempt": attempt
                            }
                        )
                        raise

                    if attempt < max_attempts:
                        delay = initial_delay * (backoff_factor ** (attempt - 1))
                        logger.warning(
                            f"Database operation failed, retrying {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "attempt_number": attempt,
                                "max_attempts": max_attempts,
                                "delay_ms": int(delay * 1000)
                            }
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Database operation failed after {max_attempts} attempts",
                            extra={
                                "function": func.__name__,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "total_attempts": max_attempts
                            }
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


class ControlStrategyService(BaseService):
    """
    Service for control strategy management and edge selection.

    Provides methods for:
    - Multi-dimensional edge filtering
    - Hierarchical route/section metadata queries
    - Control strategy parameter management
    """

    def __init__(self):
        """Initialize control strategy service."""
        super().__init__()
        logger.info("ControlStrategyService initialized")

    @retry_on_db_failure(max_attempts=2, initial_delay=0.5)
    def query_edges_with_filters(
        self,
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
    ) -> List[Any]:
        """
        Query road edges with multi-dimensional filters.

        Implements FR-001 to FR-014 filter parameters and logging
        per FR-045 to FR-049.

        Args:
            route_codes: List of route codes (e.g., ['G4202', 'SA2'])
            section_codes: List of section codes
            node_types: List of node types
            min_stake: Minimum stake (km)
            max_stake: Maximum stake (km)
            min_length: Minimum length (m)
            max_length: Maximum length (m)
            route_direction: Direction ('clockwise'/'counterclockwise')
            demonstration_ids: List of demonstration area IDs
            min_lanes: Minimum number of lanes
            with_gantry: Only return edges with gantries

        Returns:
            List of EdgeInfo dataclass objects

        Raises:
            OperationalError: Database connection failed after retries
        """
        start_time = time.time()

        # Log query parameters (FR-045)
        logger.info(
            "Querying edges with filters",
            extra={
                "filter_parameters": {
                    "route_codes": route_codes,
                    "section_codes": section_codes,
                    "node_types": node_types,
                    "min_stake": min_stake,
                    "max_stake": max_stake,
                    "min_length": min_length,
                    "max_length": max_length,
                    "route_direction": route_direction,
                    "demonstration_ids": demonstration_ids,
                    "min_lanes": min_lanes,
                    "with_gantry": with_gantry
                }
            }
        )

        try:
            # Import here to avoid circular dependency
            from shared.data_access.edge_query import query_edges_with_filters

            # Execute query
            edges = query_edges_with_filters(
                route_codes=route_codes,
                section_codes=section_codes,
                node_types=node_types,
                min_stake=min_stake,
                max_stake=max_stake,
                min_length=min_length,
                max_length=max_length,
                route_direction=route_direction,
                demonstration_ids=demonstration_ids,
                min_lanes=min_lanes,
                with_gantry=with_gantry
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Log results (FR-046: result count, FR-047: execution time)
            logger.info(
                "Edge query completed successfully",
                extra={
                    "result_count": len(edges),
                    "execution_time_ms": execution_time_ms
                }
            )

            # Log slow query warning (FR-048: >1500ms threshold)
            if execution_time_ms > 1500:
                logger.warning(
                    "Slow query detected",
                    extra={
                        "execution_time_ms": execution_time_ms,
                        "result_count": len(edges),
                        "filter_parameters": {
                            "route_codes": route_codes,
                            "section_codes": section_codes,
                            "node_types": node_types
                        }
                    }
                )

            return edges

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Log error (FR-049: error type, error message)
            logger.error(
                "Edge query failed",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "execution_time_ms": execution_time_ms,
                    "filter_parameters": {
                        "route_codes": route_codes,
                        "section_codes": section_codes
                    }
                },
                exc_info=True
            )
            raise

    @cached_with_ttl(maxsize=100, ttl=300)
    @retry_on_db_failure(max_attempts=2, initial_delay=0.5)
    def get_available_routes(self) -> List[dict]:
        """
        Get list of available routes with edge counts.

        Cached for 5 minutes (TTL=300s) per FR-062.

        Returns:
            List of dicts with route_code and edge_count

        Example:
            [{"route_code": "G4202", "edge_count": 1198}, ...]
        """
        logger.info("Fetching available routes")

        from shared.data_access.edge_query import get_available_routes

        routes = get_available_routes()

        logger.info(
            "Available routes fetched",
            extra={"route_count": len(routes)}
        )

        return routes

    @cached_with_ttl(maxsize=200, ttl=300)
    @retry_on_db_failure(max_attempts=2, initial_delay=0.5)
    def get_available_sections(
        self,
        route_code: Optional[str] = None
    ) -> List[dict]:
        """
        Get list of available sections with metadata.

        Optionally filtered by route_code. Cached for 5 minutes (TTL=300s).

        Args:
            route_code: Optional route code filter

        Returns:
            List of dicts with section metadata

        Example:
            [{"section_code": "G4202001", "route_code": "G4202",
              "edge_count": 621, "stake_range": "K0.0-K85.68"}, ...]
        """
        logger.info(
            "Fetching available sections",
            extra={"route_code": route_code}
        )

        from shared.data_access.edge_query import get_available_sections

        sections = get_available_sections(route_code=route_code)

        logger.info(
            "Available sections fetched",
            extra={
                "section_count": len(sections),
                "route_code": route_code
            }
        )

        return sections

    @cached_with_ttl(maxsize=50, ttl=300)
    @retry_on_db_failure(max_attempts=2, initial_delay=0.5)
    def get_demonstration_info(self) -> List[dict]:
        """
        Get demonstration area information.

        Cached for 5 minutes (TTL=300s) per FR-062.

        Returns:
            List of dicts with demonstration metadata

        Example:
            [{"demonstration_id": 5, "route_code": "G4202",
              "edge_count": 461, "stake_range": "1.17-85.68km"}, ...]
        """
        logger.info("Fetching demonstration area info")

        from shared.data_access.edge_query import get_demonstration_info

        demonstrations = get_demonstration_info()

        logger.info(
            "Demonstration info fetched",
            extra={"demonstration_count": len(demonstrations)}
        )

        return demonstrations

    @cached_with_ttl(maxsize=50, ttl=600)
    @retry_on_db_failure(max_attempts=2, initial_delay=0.5)
    def get_network_geometry(
        self,
        route_codes: Optional[List[str]] = None
    ) -> dict:
        """
        Get network geometry for visualization (Phase 1B - US4/T046).

        Returns junction coordinates and edge connections for Canvas rendering.
        Cached for 10 minutes (TTL=600s) as network geometry changes infrequently.

        Args:
            route_codes: Optional list of route codes to filter geometry

        Returns:
            Dict with junctions and edges for network visualization
            {
                "junctions": [
                    {"junction_id": "123", "longitude": 104.12, "latitude": 30.67},
                    ...
                ],
                "edges": [
                    {"edge_id": "-5880", "from_junction": "123", "to_junction": "456"},
                    ...
                ]
            }

        Example:
            geometry = service.get_network_geometry(route_codes=['G4202'])
        """
        logger.info(
            "Fetching network geometry",
            extra={"route_codes": route_codes}
        )

        try:
            from shared.data_access.connection import open_db_connection
            conn = open_db_connection()
            cur = conn.cursor()

            # Build WHERE clause for route filtering
            where_clause = ""
            params = []
            if route_codes:
                placeholders = ','.join(['%s'] * len(route_codes))
                where_clause = f"WHERE e.route_code IN ({placeholders})"
                params = route_codes

            # Query junction coordinates
            junction_query = f"""
                SELECT DISTINCT
                    j.junction_id,
                    j.longitude,
                    j.latitude
                FROM dim.sim_network_junctions j
                JOIN dim.sim_network_edges e ON (
                    e.from_junction = j.junction_id OR
                    e.to_junction = j.junction_id
                )
                {where_clause}
                ORDER BY j.junction_id
            """
            cur.execute(junction_query, params)
            junctions = [
                {
                    "junction_id": row[0],
                    "longitude": float(row[1]) if row[1] is not None else None,
                    "latitude": float(row[2]) if row[2] is not None else None
                }
                for row in cur.fetchall()
            ]

            # Query edge connections with additional metadata for tooltip
            # Note: edge_name field may not exist in database, using section_code as fallback
            edge_query = f"""
                SELECT
                    e.edge_id,
                    e.from_junction,
                    e.to_junction,
                    e.route_code,
                    e.num_lanes,
                    e.start_stake,
                    e.end_stake,
                    e.length,
                    e.section_code
                FROM dim.sim_network_edges e
                {where_clause}
                ORDER BY e.edge_id
            """
            cur.execute(edge_query, params)
            edges = [
                {
                    "edge_id": row[0],
                    "from_junction": row[1],
                    "to_junction": row[2],
                    "route_code": row[3],
                    "num_lanes": row[4],
                    "start_stake": float(row[5]) if row[5] is not None else None,
                    "end_stake": float(row[6]) if row[6] is not None else None,
                    "length": float(row[7]) if row[7] is not None else None,
                    "section_code": row[8]
                }
                for row in cur.fetchall()
            ]

            cur.close()
            conn.close()

            logger.info(
                "Network geometry fetched successfully",
                extra={
                    "junction_count": len(junctions),
                    "edge_count": len(edges),
                    "route_codes": route_codes
                }
            )

            return {
                "junctions": junctions,
                "edges": edges
            }

        except Exception as e:
            logger.error(
                "Failed to fetch network geometry",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "route_codes": route_codes
                },
                exc_info=True
            )
            raise

    def get_batch_edge_info(self, edge_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取路段详细信息 (Phase 2: Task 2.1)

        Args:
            edge_ids: Edge ID列表

        Returns:
            List of edge information dictionaries with full details:
            - edge_id: Edge ID
            - route_code: 路线代码
            - section_code: 路段代码
            - start_stake: 起始桩号(米)
            - end_stake: 结束桩号(米)
            - length_m: 长度(米)
            - lane_count: 车道数
            - direction: 方向
            - node_type: 节点类型

        Raises:
            Exception: If database query fails
        """
        try:
            from shared.data_access.edge_query import get_edges_by_ids

            logger.info(f"[get_batch_edge_info] Fetching info for {len(edge_ids)} edges")

            # 调用数据访问层获取路段详细信息
            edges_info_objs = get_edges_by_ids(edge_ids)

            # 转换EdgeInfo对象为字典，并调整字段名以匹配前端期望
            edges_info = []
            for edge in edges_info_objs:
                edge_dict = {
                    "edge_id": edge.edge_id,
                    "route_code": edge.route_code,
                    "section_code": edge.section_code,
                    "start_stake": edge.start_stake,
                    "end_stake": edge.end_stake,
                    "length_m": edge.length,  # 映射 length -> length_m
                    "lane_count": edge.num_lanes,  # 映射 num_lanes -> lane_count
                    "direction": edge.route_direction,  # 映射 route_direction -> direction
                    "node_type": edge.node_type,
                    "gantry_count": edge.gantry_count
                }
                edges_info.append(edge_dict)

            logger.info(f"[get_batch_edge_info] Successfully fetched {len(edges_info)} edges")

            return edges_info

        except Exception as e:
            logger.error(
                "Failed to fetch batch edge info",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "edge_count": len(edge_ids)
                },
                exc_info=True
            )
            raise
