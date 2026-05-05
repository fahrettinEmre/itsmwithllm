# Message queue backlog and consumer lag

## Symptoms
- Growing queue depth; consumers cannot keep up.
- Processing latency SLA breaches.

## Common root causes
- Downstream dependency slow (DB, HTTP).
- Too few consumer instances or low prefetch.
- Poison messages causing retries.

## Resolution patterns
- Scale consumers; tune batch size and concurrency.
- Add DLQ for poison messages; fix failing handler.
- Cache or debounce bursty producers.
