# One-way audio despite successful Bluetooth writes

Case: `sco-host-packet-size` · Evidence: **confirmed-local**

Search terms: SCO_OPTIONS MTU, eSCO TX_Packet_Length, USB PCM 48 vs radio 60, CVSD

## Diagnosis

An intermediate agent change confused on-air eSCO packet length with host PCM framing. The tested device used 60-byte radio values and 48-byte host blocks; socket MTU is a limit.

## Resolution

Observe valid received 16-bit PCM block length, bounded by SCO_OPTIONS; reset partial buffers when size or socket changes. Do not hard-code 48 or 60.

## Evidence and limits

Tests cover 48/60/96/120 and MTU bounds. This is host packet inference for the tested transport, not a claim that all Bluetooth devices negotiate identical RX/TX framing.

## Code and reproduction

- [Implementation](../../recovery/2026-11-14/work/host_framing.inc)
- [Test or detailed evidence](../../recovery/2026-11-14/work/test.c)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
