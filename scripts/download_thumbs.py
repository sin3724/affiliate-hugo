#!/usr/bin/env python3
import csv, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

CSV_PATH = sys.argv[1] if len(sys.argv)>1 else "materials_fc2.csv"
OUT_DIR  = sys.argv[2] if len(sys.argv)>2 else "static/img"
CONC     = int(sys.argv[3]) if len(sys.argv)>3 else 16

os.makedirs(OUT_DIR, exist_ok=True)
sess = requests.Session()
sess.headers.update({"User-Agent":"Mozilla/5.0 (ThumbFetcher/1.0)"})

def slug_from_row(row):
    url = (row.get("product_url") or "").strip()
    m = re.search(r"/article/(\d+)/", url)
    if m: return f"fc2-{m.group(1)}"
    t = (row.get("title") or "item").strip().replace(" ","-")
    return re.sub(r"[^a-zA-Z0-9_-]+","-", t.lower())[:60] or "item"

def ext_from_thumb(url):
    url = url.split("?")[0]
    for e in (".jpg",".jpeg",".png",".webp"):
        if url.lower().endswith(e): return e
    return ".jpg"

def fetch(row):
    title = (row.get("title") or "").strip()
    thumb = (row.get("thumbnail") or "").strip()
    if not thumb:
        return ("SKIP_NO_THUMB", title, "", "")
    slug = slug_from_row(row)
    ext  = ext_from_thumb(thumb)
    out  = os.path.join(OUT_DIR, slug+ext)
    if os.path.exists(out) and os.path.getsize(out) > 1024:
        return ("EXIST", title, thumb, out)
    try:
        r = sess.get(thumb, timeout=(5,10), stream=True)
        if r.status_code == 200 and int(r.headers.get("content-length","0"))>500:
            with open(out,"wb") as f:
                for chunk in r.iter_content(64*1024):
                    if chunk: f.write(chunk)
            return ("OK", title, thumb, out)
        return ("HTTP_FAIL", title, thumb, out)
    except Exception:
        return ("ERR", title, thumb, out)

rows=[]
with open(CSV_PATH,"r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f)
    for row in rd: rows.append(row)

report_csv = "logs/thumbs_report.csv"
ok=ng=exist=skip=0
with ThreadPoolExecutor(max_workers=CONC) as ex, open(report_csv,"w",encoding="utf-8",newline="") as rf:
    wr=csv.writer(rf)
    wr.writerow(["status","title","thumbnail","saved_path"])
    futs=[ex.submit(fetch,row) for row in rows]
    for i,ft in enumerate(as_completed(futs),1):
        s,t,th,sp = ft.result()
        wr.writerow([s,t,th,sp])
        if s=="OK": ok+=1
        elif s=="EXIST": exist+=1
        elif s=="SKIP_NO_THUMB": skip+=1
        else: ng+=1
        if i%50==0: print(f"[{i}/{len(rows)}] OK={ok} EXIST={exist} NG={ng} SKIP={skip}")
print(f"[DONE] OK={ok} EXIST={exist} NG={ng} SKIP={skip} -> {report_csv}")
