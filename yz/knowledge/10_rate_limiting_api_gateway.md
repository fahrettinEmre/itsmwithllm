# Rate limiting and 429 errors at API gateway

## Symptoms
- Legitimate clients receive 429 Too Many Requests.
- Bursty traffic rejected at edge.

## Common root causes
- Global default quota too low for peak.
- Shared key across tenants without fairness.
- Retry storms amplifying traffic.

## Resolution patterns
- Token bucket per client with burst allowance.
- Exponential backoff with jitter on clients.
- Raise limits for verified partners with monitoring.
