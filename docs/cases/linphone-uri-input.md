# SIP URI pasted into search fails or uses unexpected transport

Case: `linphone-uri-input` · Evidence: **observed-client**

Search terms: Linphone iOS search field sip sips leading colon transport=tls 5061

## Diagnosis

The client log showed unexpected UDP in one attempt and a malformed leading colon in another. Origin of the extra character was not established.

## Resolution

Clear search completely; in the observed UI enter user@home.example.net:5061;transport=tls without sip: and select the exact result. Full SIP URI syntax in other APIs remains valid.

## Evidence and limits

Verified on the tested client workflow. Do not generalize to every Linphone version or claim SIPS is inherently broken.

## Code and reproduction

- [Implementation](../../PUBLIC-SIP.txt)
- [Test or detailed evidence](../../network/public-sip/probe.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
