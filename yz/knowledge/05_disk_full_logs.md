# Disk full on log or data partition

## Symptoms
- Writes fail; services crash-loop.
- Monitoring alerts on disk usage >90%.

## Common root causes
- Log rotation misconfigured or missing.
- Debug logging left on in production.
- Core dumps or heap dumps filling temp.
- Database WAL or replication lag consuming space.

## Resolution patterns
- Enable logrotate or ship logs off-box; drop log level.
- Expand volume or attach larger disk; prune old archives.
- Clean temp; cap retention jobs.
