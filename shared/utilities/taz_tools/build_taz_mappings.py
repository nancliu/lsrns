import os
import sys
from typing import Iterable, List, Optional

import click
from sqlalchemy import create_engine, text


def _build_pg_dsn(
    host: Optional[str],
    port: Optional[str],
    database: Optional[str],
    user: Optional[str],
    password: Optional[str],
) -> str:
    missing: List[str] = []
    if not host:
        missing.append("PGHOST")
    if not port:
        missing.append("PGPORT")
    if not database:
        missing.append("PGDATABASE")
    if not user:
        missing.append("PGUSER")
    if not password:
        missing.append("PGPASSWORD")
    if missing:
        raise click.ClickException(
            f"缺少数据库环境变量: {', '.join(missing)}，请设置后重试"
        )
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def _iter_taz_ids(xml_path: str) -> Iterable[str]:
    # 采用轻量解析，按行扫描 taz id，避免一次性载入大文件
    # 匹配形如 <taz id="..."> 的片段
    import re

    pattern = re.compile(r"<taz\s+[^>]*?id=\"([^\"]+)\"")
    with open(xml_path, "r", encoding="utf-8") as f:
        for line in f:
            # 快速过滤
            if "<taz" not in line:
                continue
            for match in pattern.finditer(line):
                yield match.group(1)


def _ensure_schema(engine, schema_name: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE SCHEMA IF NOT EXISTS {schema_name};
                """
            )
        )


def _create_or_truncate_table(engine, create_sql: str, target_table: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        conn.execute(text(f"TRUNCATE TABLE {target_table};"))


def _build_demonstration_route_ref(
    engine,
    dim_schema: str,
    gantry_table: str,
) -> None:
    target_table = f"{dim_schema}.demonstration_route_ref"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {target_table} (
        demonstration_id integer PRIMARY KEY,
        demonstration_route_code text NOT NULL,
        demonstration_route_name text NOT NULL,
        source_table text NOT NULL DEFAULT 'dim.point_gantry'
    );
    """
    _create_or_truncate_table(engine, create_sql, target_table)

    insert_sql = text(
        f"""
        INSERT INTO {target_table} (demonstration_id, demonstration_route_code, demonstration_route_name)
        SELECT demonstration_id,
               MIN(demonstration_route_code) AS demonstration_route_code,
               MIN(demonstration_route_name) AS demonstration_route_name
        FROM {gantry_table}
        WHERE demonstration_id IS NOT NULL
        GROUP BY demonstration_id;
        """
    )
    with engine.begin() as conn:
        conn.execute(insert_sql)


def _build_gantry_mapping(
    engine,
    dim_schema: str,
    gantry_table: str,
) -> None:
    target_table = f"{dim_schema}.gantry_demonstration_mapping"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {target_table} (
        gantry_id text PRIMARY KEY,
        demonstration_id integer NOT NULL,
        demonstration_route_code text NOT NULL,
        demonstration_route_name text NOT NULL
    );
    """
    _create_or_truncate_table(engine, create_sql, target_table)

    insert_sql = text(
        f"""
        INSERT INTO {target_table} (gantry_id, demonstration_id, demonstration_route_code, demonstration_route_name)
        SELECT g.gantry_id, g.demonstration_id, r.demonstration_route_code, r.demonstration_route_name
        FROM {gantry_table} g
        JOIN {dim_schema}.demonstration_route_ref r USING (demonstration_id);
        """
    )
    with engine.begin() as conn:
        conn.execute(insert_sql)


def _build_toll_square_mapping(
    engine,
    dim_schema: str,
    toll_square_table: str,
) -> None:
    target_table = f"{dim_schema}.toll_square_demonstration_mapping"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {target_table} (
        square_code text PRIMARY KEY,
        demonstration_id integer,
        demonstration_route_code text,
        demonstration_route_name text
    );
    """
    _create_or_truncate_table(engine, create_sql, target_table)

    insert_sql = text(
        f"""
        INSERT INTO {target_table} (square_code, demonstration_id, demonstration_route_code, demonstration_route_name)
        SELECT s.square_code, s.demonstration_id, r.demonstration_route_code, r.demonstration_route_name
        FROM {toll_square_table} s
        LEFT JOIN {dim_schema}.demonstration_route_ref r USING (demonstration_id);
        """
    )
    with engine.begin() as conn:
        conn.execute(insert_sql)


def _build_taz_mapping(
    engine,
    dim_schema: str,
    taz_ids: Iterable[str],
    gantry_table: str,
    toll_square_table: str,
) -> None:
    target_table = f"{dim_schema}.taz_demonstration_mapping"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {target_table} (
        taz_id text PRIMARY KEY,
        source_type text,
        source_id text,
        demonstration_id integer,
        demonstration_route_code text,
        demonstration_route_name text
    );
    """
    _create_or_truncate_table(engine, create_sql, target_table)

    with engine.begin() as conn:
        # 1) 写入临时表
        conn.execute(text("DROP TABLE IF EXISTS temp__taz_ids;"))
        conn.execute(
            text(
                "CREATE TEMP TABLE temp__taz_ids (taz_id text PRIMARY KEY) ON COMMIT DROP;"
            )
        )
        # 批量插入
        batch: List[str] = []
        for tid in taz_ids:
            batch.append(tid)
            if len(batch) >= 1000:
                conn.execute(
                    text("INSERT INTO temp__taz_ids (taz_id) SELECT UNNEST(:ids)"),
                    {"ids": batch},
                )
                batch = []
        if batch:
            conn.execute(
                text("INSERT INTO temp__taz_ids (taz_id) SELECT UNNEST(:ids)"),
                {"ids": batch},
            )

        # 2) 生成映射（优先匹配门架，其次收费广场）
        insert_sql = text(
            f"""
            INSERT INTO {target_table} (taz_id, source_type, source_id, demonstration_id, demonstration_route_code, demonstration_route_name)
            SELECT
                t.taz_id,
                CASE WHEN g.gantry_id IS NOT NULL THEN 'gantry'
                     WHEN s.square_code IS NOT NULL THEN 'toll_square'
                     ELSE NULL END AS source_type,
                COALESCE(g.gantry_id, s.square_code) AS source_id,
                COALESCE(g.demonstration_id, s.demonstration_id) AS demonstration_id,
                r.demonstration_route_code,
                r.demonstration_route_name
            FROM temp__taz_ids t
            LEFT JOIN {gantry_table} g ON g.gantry_id = t.taz_id
            LEFT JOIN {toll_square_table} s ON s.square_code = t.taz_id
            LEFT JOIN {dim_schema}.demonstration_route_ref r
              ON r.demonstration_id = COALESCE(g.demonstration_id, s.demonstration_id)
            WHERE COALESCE(g.demonstration_id, s.demonstration_id) IS NOT NULL;
            """
        )
        conn.execute(insert_sql)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--xml-path",
    default=os.path.join("templates", "taz_files", "TAZ_5_validated.add.xml"),
    show_default=True,
    help="TAZ 追加文件路径（.add.xml）",
)
@click.option(
    "--dim-schema",
    default="dim",
    show_default=True,
    help="目标维度 schema 名称",
)
@click.option(
    "--gantry-table",
    default="dim.point_gantry",
    show_default=True,
    help="门架维度表 (包含 gantry_id, demonstration_id, demonstration_route_code, demonstration_route_name)",
)
@click.option(
    "--toll-square-table",
    default="dim.point_toll_square",
    show_default=True,
    help="收费广场维度表 (包含 square_code, demonstration_id)",
)
def main(xml_path: str, dim_schema: str, gantry_table: str, toll_square_table: str) -> None:
    """构建 TAZ/门架/收费广场 到示范路线的映射表并写入 dim schema。

    数据库连接从环境变量读取：PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD。
    """

    if not os.path.exists(xml_path):
        raise click.ClickException(f"未找到 XML 文件: {xml_path}")

    dsn = _build_pg_dsn(
        os.getenv("PGHOST"),
        os.getenv("PGPORT"),
        os.getenv("PGDATABASE"),
        os.getenv("PGUSER"),
        os.getenv("PGPASSWORD"),
    )
    engine = create_engine(dsn, pool_pre_ping=True)

    # 解析 TAZ id
    taz_ids = list(_iter_taz_ids(xml_path))
    if not taz_ids:
        raise click.ClickException("未从 XML 中解析到任何 <taz id=...> 标识")

    # 准备 schema
    _ensure_schema(engine, dim_schema)

    # 生成三类映射 + 参考表
    _build_demonstration_route_ref(engine, dim_schema, gantry_table)
    _build_gantry_mapping(engine, dim_schema, gantry_table)
    _build_toll_square_mapping(engine, dim_schema, toll_square_table)
    _build_taz_mapping(engine, dim_schema, taz_ids, gantry_table, toll_square_table)

    click.echo(
        "已生成以下表：\n"
        f"- {dim_schema}.demonstration_route_ref\n"
        f"- {dim_schema}.gantry_demonstration_mapping\n"
        f"- {dim_schema}.toll_square_demonstration_mapping\n"
        f"- {dim_schema}.taz_demonstration_mapping"
    )


if __name__ == "__main__":
    try:
        main()
    except click.ClickException as e:
        # 以非零退出码退出，便于脚本/CI 检测
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)

