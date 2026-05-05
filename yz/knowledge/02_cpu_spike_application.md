# CPU spike on application servers

## Symptoms
- Sustained high CPU after deploy or traffic increase.
- Latency grows while CPU pegs near 100%.

## Common root causes
- Inefficient hot loops, regex, or serialization in new code.
- Garbage collection pressure or memory churn.
- Thread pool saturation causing busy spin.
- Background jobs colliding with peak web traffic.

## Resolution patterns
- Profile CPU (flame graphs); fix hot methods.
- Scale out horizontally; add autoscaling rules tied to CPU.
- Separate batch workloads from online path.
