# Database connection timeout

## Symptoms
- Applications log "connection timed out" or JDBC/ODBC timeout errors.
- Pool wait times increase under load.

## Common root causes
- Connection pool size too small for concurrent requests.
- Long-running queries or locks holding connections.
- Network path MTU/firewall issues between app and DB.
- Database server at connection limit (`max_connections`).

## Resolution patterns
- Increase pool max size and tune idle timeout; verify no connection leaks.
- Optimize slow queries; add indexes; break large transactions.
- Verify DNS resolution and TCP health; check security group rules.
