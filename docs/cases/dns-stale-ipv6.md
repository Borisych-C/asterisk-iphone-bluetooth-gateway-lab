# Public name points to unavailable IPv6

Case: `dns-stale-ipv6` · Evidence: **confirmed-local**

Search terms: DuckDNS AAAA IPv6 prefix delegation absent stale global address IPv4

## Diagnosis

ISP prefix availability varied; stale AAAA could point to an address no longer assigned.

## Resolution

Update A/AAAA from the intended host and explicitly clear obsolete AAAA when no valid global IPv6 exists. Distinguish address absence from observation failure.

## Evidence and limits

Working voice acceptance used IPv4. Returning IPv6 requires separate SIP/RTP/firewall verification.

## Code and reproduction

- [Implementation](../../network/duckdns/update_duckdns.sh)
- [Test or detailed evidence](../../network/duckdns/test_updater.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
