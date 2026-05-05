# Network latency affecting remote users

## Symptoms
- High TTFB or long TLS handshake only for certain regions/VPNs.
- Packet loss on traceroute segments.

## Common root causes
- Geographic distance without edge caching or CDN.
- VPN concentrator overload or suboptimal routing.
- MTU black holes or asymmetric paths.
- Wi-Fi or last-mile congestion (not data center).

## Resolution patterns
- Enable CDN and cache static assets; compress payloads.
- Split tunnel VPN for SaaS where policy allows.
- Tune TCP buffers; verify MSS clamping on tunnels.
