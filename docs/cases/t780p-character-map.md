# Russian SIP MESSAGE is mojibake despite Russian menus

Case: `t780p-character-map` · Evidence: **observed-device**

Search terms: T780P CP1251 CP1252 UTF-8 glyph chart bytes 0-255 transliteration Hebrew

## Diagnosis

Localized menu fonts did not imply Unicode support for received messages. Actual glyphs differed from assumed encoding tables.

## Resolution

Use empirical byte charts and the recorded visual-russian-v2 mapping for this firmware. Control bytes yielded no useful extra alphabet; NUL truncated display.

## Evidence and limits

User approved visually readable approximations. This is not Unicode support or ordinary phonetic transliteration. Hebrew→Russian→glyph substitution was proposed for this debug phone, not used by the final Unicode Linphone bridge.

## Code and reproduction

- [Implementation](../../research/2026-11-14-message-encoding/visual-russian-v2.json)
- [Test or detailed evidence](../../tools/send-byte-chart.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
