"""Generate one personalised invitation page per guest.

usage: python gen.py guests.xlsx      (or guests.csv; first column = guest name, one per row; a header row "guest"/"المدعو"/"الاسم" is skipped;
       CSV may be UTF-8 or Windows-1256 as Excel saves it)
Reads docs/index.html (the built page), writes docs/i/<code>/index.html for each guest,
and keeps links.csv: guest,code,url,message.  Codes are stable across runs (reused from links.csv),
so re-running never changes a link already sent.
"""
import csv, html, io, pathlib, secrets, string, sys

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

def read_names(src):
    """First column of an .xlsx (first sheet) or a CSV; Excel on Arabic Windows saves CSV as cp1256, so fall back to it."""
    src = pathlib.Path(src)
    if src.suffix.lower() in ('.xlsx', '.xlsm'):
        import openpyxl
        ws = openpyxl.load_workbook(src, read_only=True, data_only=True).worksheets[0]
        return [str(r[0]) for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    raw = src.read_bytes()
    for enc in ('utf-8-sig', 'cp1256'):
        try:
            text = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    else:
        sys.exit(f'{src}: not UTF-8 or Windows-1256; save it as "CSV UTF-8" from Excel')
    return [r[0] for r in csv.reader(io.StringIO(text)) if r]

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
    for g in read_names(src):
        g = g.strip()
        if not g or g in ('guest', 'المدعو', 'الاسم') or g in guests:
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
