# -*- coding: utf-8 -*-
"""逐步探测 push2 接口哪些参数组合会触发断连。"""
import json
import ssl
import urllib.parse
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def try_get(params, ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"):
    url = "https://push2.eastmoney.com/api/qt/clist/get?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Referer": "https://quote.eastmoney.com/", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            b = r.read()
        js = json.loads(b.decode("utf-8"))
        d = js.get("data") or {}
        diff = d.get("diff") or []
        return f"OK len={len(b)} total={d.get('total')} n={len(diff)}"
    except Exception as e:
        return "FAIL " + repr(e)[:120]


tests = {
    "minimal": {"pn": 1, "pz": 5, "po": 1, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f12,f14"},
    "with_np": {"pn": 1, "pz": 5, "po": 1, "np": 1, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f12,f14"},
    "fltt_invt": {"pn": 1, "pz": 5, "po": 1, "np": 1, "fltt": 2, "invt": 2, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f12,f14"},
    "bigfields": {"pn": 1, "pz": 5, "po": 1, "fid": "f3", "fs": "m:90+t:2+f:!50",
                  "fields": "f1,f2,f3,f4,f8,f12,f13,f14,f20,f104,f105,f128,f136,f140,f141,f207,f208,f209,f222"},
    "pz100": {"pn": 1, "pz": 100, "po": 1, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f12,f14"},
    "pz200": {"pn": 1, "pz": 200, "po": 1, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f12,f14"},
    "pz500": {"pn": 1, "pz": 500, "po": 1, "fid": "f3", "fs": "m:90+t:2+f:!50", "fields": "f12,f14"},
}
for name, p in tests.items():
    print(name, "->", try_get(p))
