# Call connects with missing audio or does not hang up

Case: `nat-rtp-range` · Evidence: **confirmed-local**

Search terms: Sagemcom port forwarding range InternalPort collapse hairpin NAT Contact ACK BYE local_net

## Diagnosis

The tested router API range rule mapped multiple external RTP ports to one internal port. Separately, broad local_net classification on hairpin calls advertised a private Contact.

## Resolution

Use verified per-port forwarding and narrow transport local_net appropriate to topology. Check Contact/SDP, ACK and BYE in both LAN hairpin and truly external calls.

## Evidence and limits

Sagemcom F@ST 5670 HW 2.00, firmware SGFx10000381. Hairpin UDP probes to external 10000, 10002 and 10198 were delivered to internal 10000. Sixteen individual mappings preserved their ports. Return traffic was verified on 10000, 10006 and 10014. Direct WAN behavior of the original range rule was not isolated.

The original range used ExternalPort=10000, ExternalPortEndRange=10199 and InternalPort=10000. A trial with InternalPort=0 did not deliver the expected traffic. Individual mappings used matching external and internal ports from 10000 through 10015. External calls passed after the workaround. The original range test used LAN hairpin traffic.

The [Broadband Forum TR-181 NAT model](https://github.com/BroadbandForum/cwmp-data-models/blob/master/tr-181-2-20-0-nat.xml) describes incrementing the target for each port in a range. The tested vendor API uses similar field names. Its conformance and the cause inside the firmware are unverified.

## Code and reproduction

- [Implementation](../../network/public-sip/router-forwarding.py)
- [Test or detailed evidence](../../network/public-sip/probe.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
