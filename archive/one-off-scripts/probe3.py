# -*- coding: utf-8 -*-
"""探测新浪行业/申万行业板块列表，以及 akshare 申万接口的可用性。"""
import inspect
import json
import re
import ssl
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "https://finance.sina.com.cn/"}


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


def parse_sina_var(raw):
    txt = raw.decode("gbk", errors="replace")
    a, b = txt.find("{"), txt.rfind("}")
    return json.loads(txt[a : b + 1])


print("== 新浪行业分类 ==")
d = parse_sina_var(get("https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"))
print("板块数", len(d))
rows = []
for code, v in d.items():
    p = v.split(",")
    rows.append((code, p[1], int(p[2]), p[-4]))
rows.sort(key=lambda x: -x[2])
for r in rows:
    print(r)
with open(r"D:\deepseek\astock_sectors\data\sina_industry.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print()
print("== akshare 申万接口 URL ==")
import akshare as ak
for n in ["sw_index_first_info", "sw_index_second_info", "index_component_sw", "stock_board_industry_cons_em",
          "stock_zh_a_spot_em", "stock_zh_a_hist", "stock_zh_a_hist_tx"]:
    f = getattr(ak, n, None)
    if f is None:
        print("MISSING", n)
        continue
    try:
        src = inspect.getsource(f)
        urls = list(dict.fromkeys(re.findall(r"https?://[^\s\"']+", src)))
        print("---", n, inspect.signature(f))
        for u in urls:
            print("    ", u[:150])
    except Exception as e:
        print(n, "ERR", e)
