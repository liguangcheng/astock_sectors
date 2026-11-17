# -*- coding: utf-8 -*-
"""抓取申万一级行业（31个）全部成分股及官方权重，落盘为 data/sw_components.json。"""
import json
import os
import ssl
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Referer": "https://www.swsresearch.com/"}

INDUSTRIES = [
    ("801010", "农林牧渔"), ("801030", "基础化工"), ("801040", "钢铁"), ("801050", "有色金属"),
    ("801080", "电子"), ("801880", "汽车"), ("801110", "家用电器"), ("801120", "食品饮料"),
    ("801130", "纺织服饰"), ("801140", "轻工制造"), ("801150", "医药生物"), ("801160", "公用事业"),
    ("801170", "交通运输"), ("801180", "房地产"), ("801200", "商贸零售"), ("801210", "社会服务"),
    ("801780", "银行"), ("801790", "非银金融"), ("801230", "综合"), ("801710", "建筑材料"),
    ("801720", "建筑装饰"), ("801730", "电力设备"), ("801890", "机械设备"), ("801740", "国防军工"),
    ("801750", "计算机"), ("801760", "传媒"), ("801770", "通信"), ("801950", "煤炭"),
    ("801960", "石油石化"), ("801970", "环保"), ("801980", "美容护理"),
]

API = "https://www.swsresearch.com/institute-sw/api/index_publish/details/component_stocks/"


def get_json(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
                return json.loads(r.read().decode("utf-8", errors="replace"))
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def fetch_industry(code):
    url = f"{API}?swindexcode={code}&page=1&page_size=2000"
    js = get_json(url)
    data = js["data"]
    results = data["results"]
    return {
        "count": data["count"],
        "stocks": [{"code": x["stockcode"], "name": x["stockname"], "weight": float(x["newweight"]),
                    "begin": x.get("beginningdate")} for x in results],
    }


def main():
    out = {}
    path = os.path.join(DATA, "sw_components.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            out = json.load(f)
    for code, name in INDUSTRIES:
        key = f"{code}.SI"
        if key in out and out[key].get("stocks"):
            print("skip", key, name, len(out[key]["stocks"]))
            continue
        for attempt in range(3):
            try:
                d = fetch_industry(code)
                out[key] = {"name": name, "count": d["count"], "stocks": d["stocks"]}
                ws = sum(s["weight"] for s in d["stocks"])
                print(f"{key} {name}: count={d['count']} got={len(d['stocks'])} weightsum={ws:.3f}", flush=True)
                break
            except Exception as e:
                print("FAIL", key, name, repr(e)[:120], flush=True)
                time.sleep(3)
        time.sleep(0.3)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("industries:", len(out), "stocks:", sum(len(v["stocks"]) for v in out.values()))


if __name__ == "__main__":
    main()
