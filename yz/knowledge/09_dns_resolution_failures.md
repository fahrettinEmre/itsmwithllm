# DNS resolution failures in microservices

## Symptoms
- Sporadic "Name or service not known" in containers.
- Works after pod restart only briefly.

## Common root causes
- CoreDNS/kube-dns overload or upstream resolver limits.
- Stale nscd/cache in base image.
- VPC DNS attributes misconfigured.

## Resolution patterns
- Increase DNS replicas; enable NodeLocal DNSCache where applicable.
- Reduce per-request lookups via connection pooling and reuse.
