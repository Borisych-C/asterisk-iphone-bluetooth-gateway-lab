#!/usr/bin/env python3
"""Generate dependency-free static search-visible case pages; no network calls."""
from pathlib import Path
import html,json
root=Path(__file__).resolve().parents[1]
cases=json.loads((root/'docs/issues.json').read_text())['cases']
base='https://borisych-c.github.io/asterisk-iphone-bluetooth-gateway-lab/'
repo='https://github.com/Borisych-C/asterisk-iphone-bluetooth-gateway-lab'
e=html.escape
style='body{font:18px/1.6 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#18212b}a{color:#145ca4}code{background:#eef1f5;padding:2px 4px}li{margin:12px 0}footer{border-top:1px solid #bbb;margin-top:40px;font-size:15px}'
def page(title,description,path,body):
 return f'<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title><meta name="description" content="{e(description,quote=True)}"><link rel="canonical" href="{base+path}"><style>{style}</style><main>{body}</main><footer>Case-study evidence, not universal firmware guarantees. No live credentials or private captures. <a href="{repo}">Source repository</a> · <a href="{repo}/blob/main/AGENTS.md">Agent instructions</a></footer></html>\n'
links=''.join(f'<li><a href="cases/{c["id"]}.html">{e(c["title"])}</a><br><small>{e(", ".join(c["keywords"]))}</small></li>' for c in cases)
intro='<h1>Asterisk, iPhone and Bluetooth gateway troubleshooting</h1><p>Reproducible source fixes and observed phone quirks for AI agents and humans. Home SIM calls and SMS/iMessage bridged to Linphone through Asterisk and BlueZ MAP.</p><p>Find a symptom below, inspect the evidence level, then follow the source and test. Some findings are reproduced defects; others are observations of one device or unresolved hypotheses.</p>'
(root/'docs/index.html').write_text(page('Asterisk iPhone Bluetooth: one-way audio, MAP SMS and Linphone fixes','Evidence-led troubleshooting: chan_mobile SCO, RTP SSRC, iPhone missing MAP permission, Linphone SRTP and SMS, with source patches and tests.','',intro+'<ul>'+links+'</ul>'+f'<p><a href="issues.json">Machine-readable case index</a> · <a href="{repo}/blob/main/docs/UPSTREAM-REPORTS.md">Reports to maintainers</a> · <a href="{repo}/blob/main/docs/DEVICE-QUIRKS.md">Phone and client field notes</a> · <a href="{repo}/blob/main/README.ru.md">Русский обзор</a></p>'))
for c in cases:
 body=f'<nav><a href="../">All cases</a></nav><h1>{e(c["title"])}</h1><p>Evidence level: <strong>{e(c["evidence_level"])}</strong></p><p>{e(", ".join(c["keywords"]))}</p>'
 for title,key in [('Diagnosis','diagnosis'),('Resolution','resolution'),('Validation and limits','validation_and_limits')]:body+=f'<h2>{title}</h2><p>{e(c[key])}</p>'
 body+=f'<h2>Source and reproduction</h2><ul><li><a href="{repo}/blob/main/{c["source"]}">Implementation source</a></li><li><a href="{repo}/blob/main/{c["test_or_evidence"]}">Test or detailed evidence</a></li></ul><p>Read agent instructions before running code. Some scripts change services or send real calls/messages. Start with the offline checks.</p>'
 if c.get('reports'):
  body += '<h2>Reports</h2><ul>' + ''.join(f'<li><a href="{e(r["url"], quote=True)}">{e(r["label"])}</a></li>' for r in c['reports']) + '</ul>'
 (root/f'docs/cases/{c["id"]}.html').write_text(page(c['title']+' | Asterisk iPhone lab',c['diagnosis'],'cases/'+c['id']+'.html',body))
(root/'docs/.nojekyll').touch()
urls=[base]+[base+'cases/'+c['id']+'.html' for c in cases]
(root/'docs/sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(u)+'</loc></url>' for u in urls)+'</urlset>\n')
(root/'docs/llms.txt').write_text('# Asterisk iPhone Bluetooth Gateway Lab\n\n'+f'- [Source repository]({repo})\n- [Cases]({base}issues.json)\n'+''.join(f'- [{c["title"]}]({base}cases/{c["id"]}.html)\n' for c in cases))
print(f'Generated {len(cases) + 1} static HTML pages and sitemap')
