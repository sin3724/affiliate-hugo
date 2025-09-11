#!/usr/bin/env python3
import csv, json, re, argparse, sys

REQ = ["title","thumbnail","product_url","aff_url"]
RX_PRODUCT = re.compile(r"^https://adult\.contents\.fc2\.com/article/\d+/?$")
RX_AFF     = re.compile(r"^https://adult\.contents\.fc2\.com/article/\d+/(?:\?|&)(affuid|tag)=[^&]+")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--report", default="logs/validation_min.csv")
    ap.add_argument("--jsonl",  default="logs/validation_min.jsonl")
    a=ap.parse_args()

    rows=[]
    with open(a.csv,"r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        for i,row in enumerate(rd, start=1):
            rows.append((i,row))

    bad=0; ok=0
    with open(a.jsonl,"w",encoding="utf-8") as jf, open(a.report,"w",encoding="utf-8",newline="") as rf:
        fields=["row","title","thumbnail","product_url","aff_url","status","reasons"]
        wr=csv.DictWriter(rf, fieldnames=fields); wr.writeheader()
        for i,row in rows:
            g=lambda k:(row.get(k) or "").strip()
            reasons=[]
            for k in REQ:
                if not g(k): reasons.append(f"missing:{k}")
            if g("product_url") and not RX_PRODUCT.match(g("product_url")):
                reasons.append("pattern:product_url")
            if g("aff_url") and not RX_AFF.match(g("aff_url")):
                reasons.append("pattern:aff_url")
            status="ok" if not reasons else "bad"
            if status=="bad": bad+=1
            else: ok+=1
            out={"row":i,"title":g("title"),"thumbnail":g("thumbnail"),
                 "product_url":g("product_url"),"aff_url":g("aff_url"),
                 "status":status,"reasons":reasons}
            jf.write(json.dumps(out,ensure_ascii=False)+"\n")
            wr.writerow({**out, "reasons":"|".join(reasons)})

    total=ok+bad
    print(f"[DONE] {total} rows validated → ok={ok}, bad={bad}")
    print(f"CSV  -> {a.report}")
    print(f"JSONL-> {a.jsonl}")
if __name__=="__main__": main()
