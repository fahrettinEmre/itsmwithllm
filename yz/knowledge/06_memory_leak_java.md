# Memory pressure in JVM services

## Symptoms
- Frequent Full GC pauses; heap near max.
- OOM kills after sustained uptime.

## Common root causes
- Unbounded caches or collections.
- Classloader leaks on redeploy in dev-like setups.
- Native memory growth from Netty/direct buffers.

## Resolution patterns
- Capture heap dump; fix retention in caches.
- Right-size `-Xmx`; tune GC algorithm for workload.
- Restart policy as mitigation while fixing leak.
