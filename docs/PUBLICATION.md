# Publication boundary and release preparation

This directory is a fresh public Git candidate. It was built from a private working project using a source/text allowlist. The original folder and its backups remain private and were not made a Git parent.

## Included

Project scripts, final and intermediate source baselines needed to understand patches, tests, source-only target build inputs, anonymized configuration examples, curated English case cards, Russian narrative, and selected third-party source with its notices. No private code history is imported.

## Excluded

Live configuration snapshots/archives, phone backups, message queues/databases, raw diagnostic JSON/JSONL and packet captures, user device web pages, original photographs (including metadata), device manual binaries/text, compiled modules/executables, generated build records and caches. Upstream browser media assets are omitted; the optional historical PWA bundle is source-only. Diagnostic code is retained but not its private output.

Operator account names, email, domains, phone numbers, MAC addresses, global IPv4/IPv6 and home-directory paths were replaced with example identities. LAN topology uses substituted values. Public upstream attribution remains intact. Technical constants, package versions, historical dates and evidence numbers remain because they explain the failure. Full personal configuration must never be copied back into this candidate.

## What anonymization changes

Examples use `home.example.net`, `traveler-example`, `/home/gateway`, locally administered MAC placeholders and documentation IPs. They are not configured infrastructure. Numeric phone examples are for parsing/tests only; never dial them. Many deployment scripts retain case-specific assumptions and need adaptation. Historical prose can reference excluded private evidence: those references do not mean the evidence is secretly bundled.

Archived production hashes no longer describe anonymized files. The build header manifest was recalculated for the public tree; package provenance and ABI identifier were retained. Public Git gives the new version identity.

## Discoverability

Suggested name, description and up to 20 GitHub topics are in `github-metadata.json`. Set them in repository Settings/About when creating the public remote. README search terms, English symptom cards, `llms.txt`, AGENTS.md and issues.json provide internal discovery without promising search-engine indexing. The Russian overview and narrative preserve the original story.

The user authorized creation and publication of the public remote after preparation. The export/build scripts themselves do not create or push a remote. Only this Git directory is intended for upload—not its parent. Before the first push, rerun offline checks and Gitleaks on the Git history, inspect `git ls-files`, and verify that no private remote URL or commit identity was added.

## Handling future contributions

Use synthetic fixtures and minimal reproductions. Do not attach real SMS, codes, contacts, live SIP dumps or device photos to public issues. A log can contain private data even if no password appears. For sensitive findings use an appropriate private channel rather than a public issue.
