#!/usr/bin/env python3
import csv, json, re, argparse, requests

UA=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
RX_PRODUCT=re.compile(r"^https://adult\.contents\.fc2\.com/article/\d+/?$")
RX_AFF=re.compile(r"^https://adult\.contents\.fc2\.com/article/\d+/(?:\?|&)(affuid|tag)=.+")
REQUIRED=["title","thumbnail","product_url","aff_url"]

def http_ok(url, referer, t_conn, t_read):
    h={"User-Agent":UA}
    if referer: h["Referer"]=referer
    try:
        r=requests.head(url,headers=h,allow_redirects=True,timeout=(t_conn,t_read))
        if 200<=r.status_code<400: return True,"ok",r.status_code
        r=requests.get(url,headers=h,allow_redirects=True,timeout=(t_conn,t_read),stream=True)
        if 200<=r.status_code<400: return True,"ok",r.status_code
        return False,f"http:{r.status_code}",r.status_code
    except requests.exceptions.Timeout:
        return False,"http:timeout",0
    except requests.exceptions.RequestException as e:
        return False,f"http:{type(e).__name__}",0

def validate_row(i,row,sample_http,t_conn,t_read,strict_http):
    g=lambda k:(row.get(k) or "").strip()
    title,thumb,purl,aff,ltag=g("title"),g("thumbnail"),g("product_url"),g("aff_url"),g("link_tag")
    reasons=[]; warns=[]
    for k in REQUIRED:
        if not g(k): reasons.append(f"missing:{k}")
    if purl and not RX_PRODUCT.match(purl): reasons.append("pattern:product_url")
    if aff  and not RX_AFF.match(aff):      reasons.append("pattern:aff_url")

    thumb_ok=None; aff_ok=None
    if sample_http and i<sample_http:
        if thumb:
            ok,why,_=http_ok(thumb,purl,t_conn,t_read); thumb_ok=ok
            (reasons if strict_http else warns).append(f"thumb:{why}") if not ok else None
        if aff:
            ok,why,_=http_ok(aff,purl,t_conn,t_read);   aff_ok=ok
            (reasons if strict_http else warns).append(f"aff:{why}") if not ok else None

    status="ok"
    if reasons: status="bad"
    elif warns: status="warn"
    return {
        "row":i+1,"title":title,"thumbnail":thumb,"product_url":purl,"aff_url":aff,
        "link_tag":ltag,"thumb_ok":thumb_ok,"aff_ok":aff_ok,
        "reasons":reasons,"warns":warns,"status":status
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv",required=True)
    ap.add_argument("--report",default="logs/validation_report.csv")
    ap.add_argument("--jsonl", default="logs/validation_report.jsonl")
    ap.add_argument("--sample-http",type=int,default=10)
    ap.add_argument("--t-connect",type=float,default=2.0)
    ap.add_argument("--t-read",   type=float,default=3.0)
    ap.add_argument("--strict-http",type=int,default=0)
    a=ap.parse_args()

    rows=[]
    with open(a.csv,"r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        rows=[(i,row) for i,row in enumerate(rd)]

    ok=warn=bad=0
    with open(a.jsonl,"w",encoding="utf-8") as jf:
        results=[]
        for i,row in rows:
            r=validate_row(i,row,a.sample_http,a.t_connect,a.t_read,bool(a.strict_http))
            results.append(r); jf.write(json.dumps(r,ensure_ascii=False)+"\n")
            ok += r["status"]=="ok"
            warn+= r["status"]=="warn"
            bad += r["status"]=="bad"

    fields=["row","title","thumbnail","product_url","aff_url","thumb_ok","aff_ok","status","reasons","warns"]
    with open(a.report,"w",encoding="utf-8",newline="") as cf:
        wr=csv.DictWriter(cf,fieldnames=fields); wr.writeheader()
        for r in results:
            wr.writerow({**{k:r.get(k) for k in fields[:-3]},
                         "status":r["status"],
                         "reasons":"|".join(r["reasons"]) if r["reasons"] else "",
                         "warns":"|".join(r["warns"]) if r["warns"] else ""})
    total=len(rows)
    print(f"[DONE] {total} rows validated → ok={ok}, warn={warn}, bad={bad}")
    print(f"CSV  -> {a.report}")
    print(f"JSONL-> {a.jsonl}")

if __name__=="__main__": main()
