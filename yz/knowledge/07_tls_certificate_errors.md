# TLS / certificate errors

## Symptoms
- Clients fail handshake with unknown CA or hostname mismatch.
- Chain incomplete errors in browser or API clients.

## Common root causes
- Expired certificate or missed renewal automation.
- Wrong SAN for service hostname.
- Intermediate cert not installed on load balancer.

## Resolution patterns
- Renew cert; verify full chain on LB.
- Automate ACME renewals with alerting 30 days before expiry.
