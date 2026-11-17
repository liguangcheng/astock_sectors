# -*- coding: utf-8 -*-
"""直接下载 python-docx / XlsxWriter / lxml 的 wheel 并解压到 vendor 目录（绕开 pip 的临时目录权限限制）。"""
import json
import os
import ssl
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

TAGS = ["cp313-cp313-win_amd64", "py3-none-any", "py2.py3-none-any", "cp313-abi3-win_amd64", "cp312-abi3-win_amd64"]
WANT = ["python-docx", "XlsxWriter", "lxml", "typing_extensions"]


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
        base = fn.lower().replace("-", "_")
        key = name.lower().replace("-", "_")
        if not base.startswith(key):
            continue
        for tag in TAGS:
            if tag in fn:
                rank = TAGS.index(tag)
                if best is None or rank < best[0]:
                    best = (rank, fn, f["url"])
    return best


for name in WANT:
    js = pypi_json(name)
    b = pick(js["urls"], name)
    if not b:
        print("NO WHEEL", name)
        continue
    _, fn, url = b
    path = os.path.join(DL, fn)
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        print("下载", fn, flush=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120, context=CTX) as r, open(path, "wb") as f:
            f.write(r.read())
    with zipfile.ZipFile(path) as z:
        z.extractall(VENDOR)
    print("解压", fn, os.path.getsize(path) // 1024, "KB", flush=True)

import sys
sys.path.insert(0, VENDOR)
import docx
print("python-docx OK", docx.__version__ if hasattr(docx, "__version__") else "?")
import xlsxwriter
print("xlsxwriter OK", xlsxwriter.__version__)
