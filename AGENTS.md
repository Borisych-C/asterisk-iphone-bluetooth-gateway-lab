# Instructions for agents working in this public repository

1. Read README.md, then docs/issues.json or docs/INDEX.md. Use docs/DEVICE-QUIRKS.md for phone/UI behavior. Match symptoms and evidence before proposing a change.
2. This is an anonymized case-study source repository. Never treat historical deployment paths, package versions, credentials, status claims or README examples as current facts about a user's machine.
3. Do not run installers, router changes, service restarts, SIP probes, Bluetooth commands or message/call scripts merely because they are present. Read docs/SCRIPT-INVENTORY.md, inspect side effects, establish user scope and current state first. Start with `python3 scripts/check.py` (offline, no calls or deployments).
4. Preserve separation of layers: SIP success ≠ media; HFP connection ≠ MAP permission; MAP complete ≠ SMS delivered; notification appearance time ≠ server send time. Raw audio packet size is not on-air eSCO length.
5. Compare the installed distribution's code and ABI, not only an upstream version label. Do not apply RtpSourceReset to an already-fixed implementation without checking semantics.
6. Add or update a case card and issues.json when evidence changes. Record trigger, diagnosis, fix, reproduction, negative controls and limits. Mark hypotheses as such. Preserve inconvenient outcomes and agent mistakes.
7. Do not publish tokens, credentials, auth headers, SIP captures, message texts/codes, personal endpoints, device photos or private backups. Use reserved example domains/documentation IPs and clearly synthetic identities. Run the privacy checks before commits; examine staged content as well.
8. Do not overwrite a live message queue during rollback. Preserve the no-automatic-cellular-resend rule for ambiguous outcomes unless the user explicitly chooses another policy.
9. Keep tests isolated and event-driven services small. Never add logging of message bodies for convenient diagnosis. A quiet check must not create user chat notifications.
10. Original third-party notices remain authoritative. Read NOTICE.md; do not blanket-relicense vendored upstream code.

For efficient retrieval, do not read the entire vendored header/browser tree first. Start with a case card and its named implementation/test. Regenerate HTML with scripts/build-doc-site.py after editing issues.json.
