# fc2_crawl_to_csv.py
import argparse, csv, os, re, time, urllib.parse
from collections import deque
from typing import Set, Tuple
import requests
from bs4 import BeautifulSoup

# ---------- 設定 ----------
DEFAULT_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {
    "User-Agent": DEFAULT_UA,
    "Referer": "https://adult.contents.fc2.com/",
    "Accept-Language": "ja,en;q=0.8",
}
COOKIES = {
    # 必要に応じて年齢同意系のCookieを追加する想定。基本は不要で取れるケースが多い。
    # 例: "age_check": "1"
}

DOMAIN = "adult.contents.fc2.com"
PRODUCT_PAT = re.compile(r"^https?://adult\.contents\.fc2\.com/article/\d+/?$", re.I)

def abs_url(base: str, href: str) -> str:
    if not href:
        return ""
    return urllib.parse.urljoin(base, href)

def in_domain(url: str) -> bool:
    try:
        return urllib.parse.urlparse(url).netloc == DOMAIN
    except Exception:
        return False

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=20)
    r.raise_for_status()
    return r.text

def extract_links(base_url: str, html: str) -> Tuple[Set[str], Set[str]]:
    """戻り値: (次に辿る候補URL, 商品URL)"""
    soup = BeautifulSoup(html, "html.parser")
    next_links, product_links = set(), set()
    for a in soup.find_all("a", href=True):
        u = abs_url(base_url, a["href"])
        if not in_domain(u):
            continue
        if PRODUCT_PAT.match(u):
            product_links.add(u)
        else:
            # 余計に広がりすぎないよう典型のリスト/カテゴリっぽいURLだけ拾う
            if any(seg in u for seg in ("/category/", "/list/", "/?page=", "/ranking", "/")):
                next_links.add(u)
    return next_links, product_links

def og_content(soup: BeautifulSoup, prop: str) -> str:
    m = soup.find("meta", property=prop)
    return (m.get("content").strip() if m and m.get("content") else "") or ""

def build_aff_url(url: str, affuid: str) -> str:
    p = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    qs = [(k, v) for (k, v) in qs if k.lower() != "affuid"]
    qs.append(("affuid", affuid))
    new_qs = urllib.parse.urlencode(qs)
    return urllib.parse.urlunparse(p._replace(query=new_qs))

def scrape_product(url: str) -> dict:
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    title = og_content(soup, "og:title") or (soup.title.text.strip() if soup.title else "")
    thumb = og_content(soup, "og:image")
    # 任意メタ（まずは空でOK。必要に応じてCSSセレクタ追加）
    price = ""
    seller = ""
    return {
        "title": title,
        "thumbnail": thumb,
        "product_url": url,
        "price": price,
        "seller": seller,
    }

def crawl(seed: str, max_pages: int, max_products: int, delay: float) -> Set[str]:
    """seed から幅優先で商品URLを集める（軽量・堅牢）"""
    q = deque([seed])
    seen_pages, products = set(), set()
    while q and len(seen_pages) < max_pages and len(products) < max_products:
        url = q.popleft()
        if url in seen_pages:
            continue
        try:
            html = fetch(url)
        except Exception:
            continue
        seen_pages.add(url)
        next_links, product_links = extract_links(url, html)
        for pu in product_links:
            if len(products) >= max_products:
                break
            products.add(pu)
        for nu in next_links:
            if len(seen_pages) + len(q) >= max_pages:
                break
            if nu not in seen_pages:
                q.append(nu)
        time.sleep(delay)
    return products

def main():
    ap = argparse.ArgumentParser(description="FC2 top/category -> collect product URLs -> CSV")
    ap.add_argument("--seed", required=True, help="開始URL（例: https://adult.contents.fc2.com/）")
    ap.add_argument("--max-pages", type=int, default=20, help="巡回する最大ページ数（default: 20）")
    ap.add_argument("--max-products", type=int, default=50, help="収集する最大商品数（default: 50）")
    ap.add_argument("--delay", type=float, default=0.8, help="アクセス間隔秒（default: 0.8）")
    ap.add_argument("--out", default="materials_fc2.csv", help="出力CSV（default: materials_fc2.csv）")
    ap.add_argument("--compat-hugo", action="store_true",
                    help="Hugo向け互換列（detail_url=aff_url を含める）を出力")
    args = ap.parse_args()

    affuid = os.getenv("FC2_AFFUID") or ""
    if not affuid:
        print("※ 環境変数 FC2_AFFUID が未設定です。`export FC2_AFFUID=xxxx` を実行してください。")
        return

    print(f"[INFO] Seed: {args.seed}")
    print(f"[INFO] Max pages: {args.max_pages}, Max products: {args.max_products}")

    # 1) URL収集
    products = crawl(args.seed, args.max_pages, args.max_products, args.delay)
    print(f"[INFO] Found products: {len(products)}")

    # 2) 各商品ページからメタ取得 → CSV
    rows = []
    for i, url in enumerate(sorted(products), 1):
        try:
            meta = scrape_product(url)
            aff_url = build_aff_url(url, affuid)
            link_tag = f'<a href="{aff_url}" target="_blank" rel="noopener"><img src="{meta["thumbnail"]}" alt="{meta["title"]}"></a>'
            row = {
                "title": meta["title"],
                "thumbnail": meta["thumbnail"],
                "product_url": url,
                "aff_url": aff_url,
                "link_tag": link_tag,
                "price": meta["price"],
                "seller": meta["seller"],
            }
            if args.compat_hugo:
                row["detail_url"] = aff_url  # 以前のジェネレーター互換
            rows.append(row)
            print(f"[{i}/{len(products)}] OK: {meta['title']}")
            time.sleep(args.delay)
        except Exception as e:
            print(f"[{i}/{len(products)}] NG: {url} -> {e}")

    # 3) 出力
    fieldnames = ["title","thumbnail","product_url","aff_url","link_tag","price","seller"]
    if args.compat_hugo:
        fieldnames.insert(3, "detail_url")  # aff_urlの直前に追加
    with open(args.out, "w", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ 完了: {args.out}（{len(rows)}件）")

if __name__ == "__main__":
    main()

