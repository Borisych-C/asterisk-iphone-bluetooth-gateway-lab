# Russian SIP MESSAGE is mojibake despite Russian menus

Case: `t780p-character-map` · Evidence: **observed-device**

Search terms: T780P CP1251 CP1252 UTF-8 glyph chart bytes 0-255 transliteration Hebrew

## Diagnosis

Localized menu fonts did not imply Unicode support for received messages. Actual glyphs differed from assumed encoding tables.

## Resolution

Use empirical byte charts and the recorded visual-russian-v2 mapping for this firmware. Control bytes yielded no useful extra alphabet; NUL truncated display.

## Evidence and limits

On firmware V78.5.3.1 SVN13200 and hardware 18.01.01.0, incoming direct UTF-8 with an explicit charset still displayed incorrectly. ASCII was readable and the phone sent UTF-8 from its own web UI. These observations were sent privately to LVswitch service.

## Code and reproduction

- [Implementation](../../research/2026-11-14-message-encoding/visual-russian-v2.json)
- [Test or detailed evidence](../../tools/send-byte-chart.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[LVswitch service and support](https://www.lvswitches.com/page/service-and-support.html).
