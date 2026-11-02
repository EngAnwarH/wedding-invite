"""Generate one personalised invitation page per guest.

usage: python gen.py guests.csv            (columns: guest,inviter  — header row optional, UTF-8)
Reads docs/index.html (the built page), writes docs/i/<code>/index.html for each guest,
and appends to links.csv: guest,inviter,code,url,message.  Codes are kept stable across runs
by reusing links.csv, so re-running never changes a link already sent.
"""
import csv, html, pathlib, secrets, string, sys, urllib.parse

ROOT = pathlib.Path(__file__).parent
BASE = 'https://dawah-abdulrahman.vercel.app'
HONORIFIC = 'الأكرم'
ALPHABET = string.ascii_lowercase + string.digits

def code():
    return ''.join(secrets.choice(ALPHABET) for _ in range(6))

def message(url):
    return ('بسم الله الرحمن الرحيم\nالسلام عليكم ورحمة الله وبركاته\n\n'
            'يسرّني ويشرّفني دعوتكم لحضور حفل زواجي، وذلك بمشيئة الله تعالى:\n\n'
            'تفاصيل الدعوة وموقع القاعة في الرابط:\n' + url)

def main(src):
    tpl = (ROOT / 'docs' / 'index.html').read_text(encoding='utf-8')
    assert '{{GUEST}}' in tpl and '{{INVITER}}' in tpl, 'docs/index.html has no name slots; rebuild it'
    links = ROOT / 'links.csv'
    known = {}
    if links.exists():
        with links.open(encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                known[(r['guest'], r['inviter'])] = r['code']
    rows = []
    with open(src, encoding='utf-8-sig', newline='') as f:
        for r in csv.reader(f):
            if len(r) < 2 or not r[0].strip() or r[0].strip() in ('guest', 'المدعو'):
                continue
            rows.append((r[0].strip(), r[1].strip()))
    out = []
    used = set(known.values())
    for guest, inviter in rows:
        c = known.get((guest, inviter))
        if not c:
            c = code()
            while c in used: c = code()
            used.add(c); known[(guest, inviter)] = c
        page = (tpl.replace('<div class="guest-w" id="guestW" hidden>', '<div class="guest-w" id="guestW">')
                   .replace('<p class="inviter" id="inviterW" hidden>', '<p class="inviter" id="inviterW">')
                   .replace('>الأكرم<', '>' + html.escape(HONORIFIC) + '<')
                   .replace('{{GUEST}}', html.escape(guest))
                   .replace('{{INVITER}}', html.escape(inviter))
                   .replace('url("bg.jpg")', 'url("../../bg.jpg")')
                   .replace('<title>دعوة حفل زواجي</title>', '<title>دعوة حفل زواجي — ' + html.escape(guest) + '</title>'))
        d = ROOT / 'docs' / 'i' / c
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page, encoding='utf-8')
        url = f'{BASE}/i/{c}'
        out.append({'guest': guest, 'inviter': inviter, 'code': c, 'url': url, 'message': message(url)})
    # rewrite links.csv with everything known (old + new)
    allrows = {(r['guest'], r['inviter']): r for r in out}
    if links.exists():
        with links.open(encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                allrows.setdefault((r['guest'], r['inviter']), r)
    with links.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['guest', 'inviter', 'code', 'url', 'message'])
        w.writeheader(); w.writerows(allrows.values())
    for r in out:
        print(r['guest'], '|', r['inviter'], '->', r['url'])
    print(f'{len(out)} pages written, {len(allrows)} links in links.csv')

if __name__ == '__main__':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
    main(sys.argv[1])
