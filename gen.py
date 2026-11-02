"""Generate one personalised invitation page per guest.

usage: python gen.py guests.csv       (one guest name per line; a header row "guest"/"المدعو" is skipped; UTF-8)
Reads docs/index.html (the built page), writes docs/i/<code>/index.html for each guest,
and keeps links.csv: guest,code,url,message.  Codes are stable across runs (reused from links.csv),
so re-running never changes a link already sent.
"""
import csv, html, pathlib, secrets, string, sys

ROOT = pathlib.Path(__file__).parent
BASE = 'https://dawah-abdulrahman.vercel.app'
HONORIFIC = 'العزيز'
ALPHABET = string.ascii_lowercase + string.digits

def code():
    return ''.join(secrets.choice(ALPHABET) for _ in range(6))

def message(url):
    return ('بسم الله الرحمن الرحيم\nالسلام عليكم ورحمة الله وبركاته\n\n'
            'يسرّني ويشرّفني دعوتكم لحضور حفل زواجي، وذلك بمشيئة الله تعالى:\n\n'
            'تفاصيل الدعوة وموقع القاعة في الرابط:\n' + url)

def main(src):
    tpl = (ROOT / 'docs' / 'index.html').read_text(encoding='utf-8')
    assert '{{GUEST}}' in tpl, 'docs/index.html has no guest slot; rebuild it'
    links = ROOT / 'links.csv'
    known = {}
    if links.exists():
        with links.open(encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                known[r['guest']] = r['code']
    guests = []
    with open(src, encoding='utf-8-sig', newline='') as f:
        for r in csv.reader(f):
            g = (r[0] if r else '').strip()
            if not g or g in ('guest', 'المدعو') or g in guests:
                continue
            guests.append(g)
    used = set(known.values())
    out = []
    for g in guests:
        c = known.get(g)
        if not c:
            c = code()
            while c in used: c = code()
            used.add(c); known[g] = c
        page = (tpl.replace('<p class="env-g" id="guestW" hidden>', '<p class="env-g" id="guestW">')
                   .replace('id="guestW">العزيز<', 'id="guestW">' + html.escape(HONORIFIC) + '<')
                   .replace('{{GUEST}}', html.escape(g))
                   .replace('url("bg.jpg")', 'url("../../bg.jpg")')
                   .replace('<title>دعوة حفل زواجي</title>', '<title>دعوة حفل زواجي — ' + html.escape(g) + '</title>'))
        d = ROOT / 'docs' / 'i' / c
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page, encoding='utf-8')
        url = f'{BASE}/i/{c}'
        out.append({'guest': g, 'code': c, 'url': url, 'message': message(url)})
    allrows = {r['guest']: r for r in out}
    if links.exists():
        with links.open(encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                allrows.setdefault(r['guest'], {'guest': r['guest'], 'code': r['code'], 'url': r['url'], 'message': r.get('message') or message(r['url'])})
    with links.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['guest', 'code', 'url', 'message'])
        w.writeheader(); w.writerows(allrows.values())
    for r in out:
        print(r['guest'], '->', r['url'])
    print(f'{len(out)} pages written, {len(allrows)} links in links.csv')

if __name__ == '__main__':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
    main(sys.argv[1])
