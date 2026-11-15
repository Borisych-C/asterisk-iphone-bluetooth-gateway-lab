# Call connects with missing audio or does not hang up

Case: `nat-rtp-range` · Evidence: **confirmed-local**

Search terms: Sagemcom port forwarding range InternalPort collapse hairpin NAT Contact ACK BYE local_net

## Diagnosis

The tested router API range rule mapped multiple external RTP ports to one internal port. Separately, broad local_net classification on hairpin calls advertised a private Contact.

## Resolution

Use verified per-port forwarding and narrow transport local_net appropriate to topology. Check Contact/SDP, ACK and BYE in both LAN hairpin and truly external calls.

## Evidence and limits

16 separate RTP port mappings were tested. This does not prove all router range implementations are defective. Original agent range assumption was wrong for this API.

## Code and reproduction

- [Implementation](../../network/public-sip/router-forwarding.py)
- [Test or detailed evidence](../../network/public-sip/probe.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
