import csv, glob, os, re
OUT = 'materials_from_posts.csv'
fields = ['title','thumbnail','product_url','aff_url','link_tag','slug']

def get(text, key):
    # "key: "value"" or "key: value" の両方に対応（1行値のみ）
    m = re.search(r'^\s*'+re.escape(key)+r'\s*:\s*"(.*?)"\s*$', text, re.MULTILINE)
    if not m:
        m = re.search(r'^\s*'+re.escape(key)+r'\s*:\s*([^\n]+)\s*$', text, re.MULTILINE)
    return (m.group(1).strip() if m else '')

rows=[]
for path in glob.glob('content/posts/*.md'):
    slug = os.path.splitext(os.path.basename(path))[0]
    if not slug.startswith('fc2-'): 
        continue
    with open(path, encoding='utf-8') as f:
        txt = f.read()
    rows.append({
        'title':       get(txt,'title') or slug,
        'thumbnail':   get(txt,'thumbnail'),
        'product_url': get(txt,'product_url'),
        'aff_url':     get(txt,'aff_url'),
        'link_tag':    get(txt,'link_tag'),
        'slug':        slug,
    })

with open(OUT,'w',encoding='utf-8',newline='') as f:
    wr=csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)
print(f'[DONE] {len(rows)} rows -> {OUT}')
