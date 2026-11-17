# -*- coding: utf-8 -*-
"""探测申万宏源研究 API：一级行业列表 + 成分股。"""
import json
import ssl
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "https://www.swsresearch.com/"}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


urls = [
    "https://www.swsresearch.com/institute-sw/api/index_publish/details/component_stocks/?swindexcode=801010&page=1&page_size=10",
    "https://www.swsresearch.com/institute-sw/api/index_publish/details/component_stocks/?swindexcode=801010",
    "https://www.swsresearch.com/institute-sw/api/index_publish/details/component_stocks/?swindexcode=801010&pageNo=1&pageSize=10",
    "https://www.swsresearch.com/institute-sw/api/index_publish/details/index_list/?level=1",
]
for u in urls:
    try:
        b = get(u)
        print("OK", len(b), u[:110])
        print(b[:400].decode("utf-8", errors="replace"))
    except Exception as e:
        print("FAIL", repr(e)[:150], u[:110])
    print()
