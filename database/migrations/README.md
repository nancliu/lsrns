# Database Migrations

This directory contains SQL migration scripts for the OD_SIM database.

## Migration Files

| File | Date | Purpose | Status |
|------|------|---------|--------|
| `004_add_edge_query_indexes.sql` | 2025-10-22 | Add indexes for edge query performance | Ready to apply |

## How to Apply Migrations

### Prerequisites
- PostgreSQL client tools (`psql`) installed
- Database credentials configured in `.env` file at project root
- Admin access to the database

### Apply a Migration

```powershell
# From project root directory
.\database\apply_migration.ps1 -MigrationFile "004_add_edge_query_indexes.sql"
```

### Verify Migration Applied

```powershell
# Check indexes exist
psql -h $env:DB_HOST -p $env:DB_PORT -U $env:DB_USER -d $env:DB_NAME -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'sim_network_edges' AND schemaname = 'dim'
ORDER BY indexname;
"
```

### Manual Application (if PowerShell script fails)

```bash
# Set password environment variable
export PGPASSWORD=your_password

# Apply migration directly
psql -h 10.149.235.123 -p 5432 -U your_username -d sdzg -f database/migrations/004_add_edge_query_indexes.sql

# Clear password
unset PGPASSWORD
```

## Migration Naming Convention

Format: `{number}_{description}.sql`

- `{number}`: 3-digit sequential number (001, 002, 003, etc.)
- `{description}`: Snake_case description of the change
- Example: `004_add_edge_query_indexes.sql`

## Testing Migrations

Before applying to production:

1. **Test on development database first**
2. **Verify query performance improvement**
3. **Check for index creation errors**
4. **Monitor application behavior after migration**

### Performance Testing Example

```sql
-- Before migration (expect 5-10 seconds)
EXPLAIN ANALYZE
SELECT section_code, route_code, COUNT(*) as edge_count
FROM dim.sim_network_edges
WHERE section_code IS NOT NULL AND route_code = 'G4202'
GROUP BY section_code, route_code
ORDER BY route_code, section_code;

-- After migration (expect <500ms)
-- Same query should now use index scan
```

## Rollback

If you need to rollback a migration:

```sql
-- Remove indexes created by 004_add_edge_query_indexes.sql
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_code;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_section_code;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_section;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_demonstration_id;
```

## Best Practices

1. **Always backup** before applying migrations to production
2. **Test migrations** on development environment first
3. **Apply during low-traffic** periods if possible
4. **Monitor performance** after migration
5. **Document changes** in this README
6. **Keep migrations idempotent** (use `IF NOT EXISTS`)
