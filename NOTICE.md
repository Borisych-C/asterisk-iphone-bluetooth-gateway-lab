# Licensing and provenance

Project-authored additions and documentation are offered under GPL-2.0-or-later, unless a file states otherwise. The root LICENSE provides GPL version 2. This does not replace upstream licenses or notices.

- Asterisk-derived C code, patches and extracted Asterisk headers retain their original Digium/contributor notices and GPL terms. `app_rtp_source_reset.c` explicitly states GPL-2.0-or-later. The build input manifest records original upstream/package URLs and versions; public checksums reflect anonymization of examples, not signatures from the original package.
- BlueZ headers in `input/include-bluetooth` retain their LGPL-2.1-or-later notices; see LICENSES/LGPL-2.1.txt.
- Historical Browser-Phone code is from InnovateAsterisk/Browser-Phone, commit `33902782876259957b18f9ca71f811ae0f29b6b3` (0.3.29), with project-specific stage1 overlays. Its AGPL-3.0 license remains in `stage1/browser-phone/LICENSE` and LICENSES/AGPL-3.0.txt. Bundled libraries keep their source-header licenses (including MIT/BSD notices); they are not relicensed under the root license.
- Public upstream contributor names and attribution email addresses are retained deliberately. They are not the operator's private contact details.
- Original device manuals, user photographs, device web dumps and private service snapshots are excluded. Upstream research excerpts retain original notices.

The original Browser-Phone non-code assets (fonts, icons, sample sounds and images) are not included in this text/source export. The historical PWA directory is not a complete deployable UI bundle. Restore upstream assets at the recorded commit if studying that optional branch; preserve their licenses. The active Linphone/MAP gateway does not depend on that branch.
