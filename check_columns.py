"""Quick script to check database columns."""
from shared.data_access.connection import open_db_connection

conn = open_db_connection()
cur = conn.cursor()

# Check all columns in sim_network_edges table
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_schema = 'dim' AND table_name = 'sim_network_edges'
    ORDER BY ordinal_position;
""")

print("=" * 70)
print("dim.sim_network_edges 表的所有列：")
print("=" * 70)
print(f"{'列名':<30} {'数据类型':<20} {'长度':<10}")
print("-" * 70)

for col in cur.fetchall():
    col_name, data_type, max_length = col
    length_str = str(max_length) if max_length else ""
    print(f"{col_name:<30} {data_type:<20} {length_str:<10}")

# Check if the specific columns we need exist
print("\n" + "=" * 70)
print("检查所需的列是否存在：")
print("=" * 70)

needed_cols = ['num_lanes', 'start_stake', 'end_stake', 'length', 'section_code']
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'dim'
      AND table_name = 'sim_network_edges'
      AND column_name = ANY(%s);
""", (needed_cols,))

existing_cols = [row[0] for row in cur.fetchall()]
for col in needed_cols:
    status = "✓ 存在" if col in existing_cols else "✗ 不存在"
    print(f"{col:<20} {status}")

# Test actual query
print("\n" + "=" * 70)
print("测试实际查询 (前3条记录)：")
print("=" * 70)

try:
    cur.execute("""
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
        WHERE e.route_code = 'G4202'
        ORDER BY e.edge_id
        LIMIT 3;
    """)

    rows = cur.fetchall()
    print(f"\n查询返回 {len(rows)} 条记录：")
    for i, row in enumerate(rows, 1):
        print(f"\n记录 {i}:")
        print(f"  edge_id: {row[0]}")
        print(f"  from_junction: {row[1]}")
        print(f"  to_junction: {row[2]}")
        print(f"  route_code: {row[3]}")
        print(f"  num_lanes: {row[4]}")
        print(f"  start_stake: {row[5]}")
        print(f"  end_stake: {row[6]}")
        print(f"  length: {row[7]}")
        print(f"  section_code: {row[8]}")
except Exception as e:
    print(f"\n查询失败: {e}")

cur.close()
conn.close()
