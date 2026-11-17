# -*- coding: utf-8 -*-
"""探查东方财富行业板块列表与成分股接口，输出原始 JSON 到 data/ 目录。"""
import json
import os
import ssl
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get_json(url, params=None, referer="https://quote.eastmoney.com/"):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        raw = r.read()
    txt = raw.decode("utf-8", errors="replace")
    # eastmoney sometimes returns jsonp
    if txt.startswith("(") or txt.startswith("jQuery"):
        a, b = txt.find("("), txt.rfind(")")
        txt = txt[a + 1 : b]
    return json.loads(txt)


def fetch_paginated(base, params, pz=100):
    out = []
    page = 1
    total = None
    while True:
        p = dict(params)
        p.update({"pn": page, "pz": pz, "np": 1})
        js = get_json(base, p)
        d = js.get("data")
        if not d:
            break
        diff = d.get("diff") or []
        if isinstance(diff, dict):
            diff = list(diff.values())
        out.extend(diff)
        total = d.get("total", len(out))
        if len(out) >= total or not diff:
            break
        page += 1
    return out, total


BOARD_URL = "https://push2.eastmoney.com/api/qt/clist/get"
BOARD_FIELDS = "f1,f2,f3,f4,f8,f12,f13,f14,f20,f104,f105,f128,f136,f140,f141,f207,f208,f209,f222"

boards, total = fetch_paginated(BOARD_URL, {"po": 1, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": BOARD_FIELDS})
print("行业板块数:", total, "抓取:", len(boards))
with open(os.path.join(DATA, "boards_raw.json"), "w", encoding="utf-8") as f:
    json.dump({"total": total, "boards": boards}, f, ensure_ascii=False, indent=1)

for b in boards[:8]:
    print(b.get("f12"), b.get("f14"), b.get("f20"))

# 概念板块也一并留存，便于交叉验证
concepts, ctotal = fetch_paginated(BOARD_URL, {"po": 1, "fid": "f3", "fs": "m:90+t:3+f:!50", "fields": BOARD_FIELDS})
print("概念板块数:", ctotal, "抓取:", len(concepts))
with open(os.path.join(DATA, "concepts_raw.json"), "w", encoding="utf-8") as f:
    json.dump({"total": ctotal, "boards": concepts}, f, ensure_ascii=False, indent=1)
