# Contributing useful diagnostic evidence

Start with AGENTS.md. Keep a contribution narrow: observed symptom, exact version/build, reproduction, relevant layer, proposed change, test result and remaining uncertainty. Use docs/cases as the template and update docs/issues.json. A reproduced bug, a device quirk and a suspected cause are different evidence levels.

Prefer sanitized synthetic traffic to production captures. Keep public attribution and licenses. Do not submit credentials, caller numbers, device IDs, private endpoints, photos or message contents. Confirm that a new test cannot send a real SMS or place a real call in CI.

Run `python3 scripts/check.py` and Gitleaks before proposing a change. Updated Asterisk builds require new compatibility evidence; do not silently extend the historical supported version list. Describe how a workaround can be removed once upstream is fixed.
