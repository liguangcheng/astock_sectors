# -*- coding: utf-8 -*-
"""1) 申万一级行业清单与成分股分页测试；2) 腾讯月K线接口测试。"""
import json
import ssl
import urllib.parse
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}


def get(url, referer=None, timeout=25):
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


print("== 申万一/二级行业清单（legulegu 源，akshare） ==")
import akshare as ak
try:
    df = ak.sw_index_first_info()
    print(df.shape)
    print(df.to_string())
    df.to_csv(r"D:\deepseek\astock_sectors\data\sw_first_raw.csv", index=False, encoding="utf-8-sig")
except Exception as e:
    print("sw_index_first_info FAIL", repr(e)[:300])

print()
print("== 成分股分页 & 权重合计 ==")
for ps in [10, 50, 200, 500]:
    u = f"https://www.swsresearch.com/institute-sw/api/index_publish/details/component_stocks/?swindexcode=801010&page=1&page_size={ps}"
    try:
        d = json.loads(get(u, "https://www.swsresearch.com/"))
        res = d["data"]["results"]
        print("page_size", ps, "got", len(res), "count", d["data"]["count"], "weightsum", round(sum(float(x['newweight']) for x in res), 3))
    except Exception as e:
        print("page_size", ps, "FAIL", repr(e)[:200])

print()
print("== 腾讯月K线 ==")
u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,month,2024-01-01,2026-11-15,300,qfq"
b = get(u, "https://gu.qq.com/")
js = json.loads(b)
d = js["data"]["sh600519"]
print("keys", list(d.keys()))
for k in ("qfqmonth", "month"):
    if k in d:
        print(k, "rows", len(d[k]))
        for row in d[k][:2] + d[k][-2:]:
            print("   ", row)
