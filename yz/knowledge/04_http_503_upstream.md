# HTTP 503 Service Unavailable

## Symptoms
- Intermittent 503 from load balancer or reverse proxy.
- Healthy checks flap.

## Common root causes
- All upstream instances busy or restarting.
- Connection pool to upstream exhausted at proxy layer.
- Deploy rolling restart with insufficient capacity buffer.
- Circuit breaker open after repeated failures.

## Resolution patterns
- Increase replica count; tune max connections on LB.
- Stagger deploys; verify readiness probes.
- Inspect upstream error logs for OOM or thread exhaustion.
