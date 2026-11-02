"""Wrap the artifact-style page (no doctype/html/head/body) into a complete HTML document for static hosting."""
import sys, re, shutil, pathlib
src = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
body = src.read_text(encoding='utf-8')
m = re.search(r'<title>(.*?)</title>', body)
title = m.group(1) if m else 'دعوة'
body = body.replace(m.group(0), '', 1) if m else body
body = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', '', body)
html = f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="robots" content="noindex">
<title>{title}</title>
<meta property="og:title" content="{title}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://dawah-abdulrahman.vercel.app/share.jpg">
<meta property="og:url" content="https://dawah-abdulrahman.vercel.app/">
<style>html{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
{body}
</body>
</html>
'''
(out / 'index.html').write_text(html, encoding='utf-8')
for f in ('bg.jpg', 'share.jpg'):
    p = src.parent / f
    if p.exists(): shutil.copy(p, out / f)
print('built', out / 'index.html', len(html))
