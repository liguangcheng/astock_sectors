# -*- coding: utf-8 -*-
"""探测东方财富不同接入域名与备用行情接口（腾讯/新浪/baostock）的可达性。"""
import json
import ssl
import time
import urllib.parse
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def get(url, headers=None, timeout=15):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            b = r.read()
        return f"OK {r.status} {len(b)}B {int((time.time()-t)*1000)}ms :: {b[:120]}"
    except Exception as e:
        return f"FAIL {int((time.time()-t)*1000)}ms " + repr(e)[:110]


q = "pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!50&fields=f12,f14"
hosts = ["push2.eastmoney.com", "82.push2.eastmoney.com", "17.push2.eastmoney.com",
         "45.push2.eastmoney.com", "quote.eastmoney.com", "push2his.eastmoney.com"]
for h in hosts:
    print(h, "->", get(f"https://{h}/api/qt/clist/get?{q}", {"Referer": "https://quote.eastmoney.com/"}))

print()
print("tencent-index ->", get("https://qt.gtimg.cn/q=sh000001"))
print("tencent-kline ->", get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,month,2024-01-01,2026-11-15,100,qfq"))
print("sina-hq ->", get("https://hq.sinajs.cn/list=sh600519", {"Referer": "https://finance.sina.com.cn/"}))
print("sina-kline ->", get("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=30"))
print("sse ->", get("https://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L&type=inParams&isPagination=true&pageHelp.pageSize=5&pageHelp.pageNo=1", {"Referer": "https://www.sse.com.cn/"}))
