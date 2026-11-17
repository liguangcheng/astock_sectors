# -*- coding: utf-8 -*-
"""在不依赖 pip 的情况下，从 PyPI 直接下载 wheel 并解压到本地 vendor 目录。"""
import json
import os
import ssl
import sys
import urllib.request
import zipfile

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0"}

VENDOR = r"D:\deepseek\astock_sectors\vendor"
DL = r"D:\deepseek\astock_sectors\_tmp\wheels"
os.makedirs(VENDOR, exist_ok=True)
os.makedirs(DL, exist_ok=True)

WANT = [
    ("matplotlib", None),
    ("contourpy", None),
    ("cycler", None),
    ("fonttools", None),
    ("kiwisolver", None),
    ("packaging", None),
    ("pyparsing", None),
    ("python-dateutil", None),
    ("pillow", None),
    ("numpy", None),
]

TAGS = ["cp313-cp313-win_amd64", "py3-none-any", "cp313-abi3-win_amd64", "py2.py3-none-any", "cp39-abi3-win_amd64"]


def pypi_json(name):
    url = f"https://pypi.org/pypi/{name}/json"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=CTX) as r:
        return json.loads(r.read())


def pick(files, name):
    best = None
    for f in files:
        fn = f["filename"]
        if not fn.endswith(".whl"):
            continue
        if not fn.lower().startswith(name.replace("-", "_").lower()):
            continue
        for tag in TAGS:
            if tag in fn:
                rank = TAGS.index(tag)
                if best is None or rank < best[0]:
                    best = (rank, fn, f["url"])
    return best


installed = {}
import importlib.metadata as md
for name in ["numpy", "pillow", "python-dateutil", "packaging", "pyparsing", "cycler", "kiwisolver", "fonttools", "contourpy", "matplotlib"]:
    try:
        installed[name] = md.version(name)
    except Exception:
        pass
print("已安装:", installed, flush=True)

for name, _ in WANT:
    if name in installed:
        continue
    try:
        js = pypi_json(name)
        b = pick(js["urls"], name)
        if not b:
            print("NO WHEEL", name, flush=True)
            continue
        _, fn, url = b
        path = os.path.join(DL, fn)
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            print("下载", fn, flush=True)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120, context=CTX) as r, open(path, "wb") as f:
                f.write(r.read())
        with zipfile.ZipFile(path) as z:
            z.extractall(VENDOR)
        print("解压完成", fn, os.path.getsize(path) // 1024, "KB", flush=True)
    except Exception as e:
        print("FAIL", name, repr(e)[:200], flush=True)

sys.path.insert(0, VENDOR)
try:
    import matplotlib
    print("matplotlib OK", matplotlib.__version__, matplotlib.__file__)
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    print("pyplot OK")
except Exception as e:
    print("IMPORT FAIL", repr(e)[:300])
