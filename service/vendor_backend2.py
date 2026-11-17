# -*- coding: utf-8 -*-
"""从清华镜像解析并安装后端依赖到 backend/vendor（迷你 pip，处理 Requires-Dist 递归）。

用法：
    python vendor_backend2.py fastapi uvicorn sqlalchemy python-dotenv
"""
import email.parser
import os
import re
import ssl
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urljoin

BASE = Path(__file__).resolve().parent
VENDOR = str(BASE / "backend" / "vendor")
DL = str(BASE / ".wheels")
MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple/{pkg}/"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "pip/24"}
TAGS = ["cp313-cp313-win_amd64", "py3-none-any", "py2.py3-none-any", "cp313-abi3-win_amd64"]

os.makedirs(VENDOR, exist_ok=True)
os.makedirs(DL, exist_ok=True)

_index_cache: dict[str, str] = {}


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_version(v: str):
    parts = re.split(r"[.\-+]", v)
    out = []
    for p in parts:
        out.append(int(p) if p.isdigit() else 0)
    return tuple(out)


def index_html(pkg: str) -> str:
    key = norm(pkg)
    if key not in _index_cache:
        url = MIRROR.format(pkg=key)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=CTX) as r:
            _index_cache[key] = r.read().decode("utf-8", "replace")
    return _index_cache[key]


def candidates(pkg: str):
    html = index_html(pkg)
    base = MIRROR.format(pkg=norm(pkg))
    out = []
    for m in re.finditer(r'href="([^"]+\.whl#[^"]*)"', html):
        href = m.group(1)
        full = urljoin(base, href)
        fn = os.path.basename(href.split("#")[0])
        stem = fn[:-4]
        parts = stem.split("-")
        if len(parts) < 5:
            continue
        version = parts[1]
        tag = "-".join(parts[-3:])
        rank = None
        for i, t in enumerate(TAGS):
            if t in tag:
                rank = i
                break
        if rank is None:
            continue
        out.append((parse_version(version), rank, version, tag, full))
    out.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    return out


def pick(pkg: str):
    cands = candidates(pkg)
    if not cands:
        return None
    best_ver = cands[0][0]
    same = [c for c in cands if c[0] == best_ver]
    same.sort(key=lambda x: x[1])
    return same[0]


def requires_of(zip_path: str, pkg: str):
    with zipfile.ZipFile(zip_path) as z:
        meta = [n for n in z.namelist() if n.endswith(".dist-info/METADATA")]
        if not meta:
            return []
        raw = z.read(meta[0]).decode("utf-8", "replace")
    msg = email.parser.HeaderParser().parsestr(raw)
    reqs = []
    for line in msg.get_all("Requires-Dist") or []:
        if "extra ==" in line:
            continue
        if "python_version" in line and "< '3.13'" in line.replace('"', "'"):
            continue
        if "platform_system == 'Windows'" not in line and "platform_system" in line:
            continue
        name = re.split(r"[\[\s<>=!~;(]", line.strip(), maxsplit=1)[0]
        if name:
            reqs.append(norm(name))
    return reqs


def installed_requires(key: str):
    """已解压包：从 dist-info/METADATA 读依赖。"""
    for d in os.listdir(VENDOR):
        if not d.endswith(".dist-info"):
            continue
        base = d[: -len(".dist-info")]
        if norm(base).split("-")[0] != key:
            continue
        meta_path = os.path.join(VENDOR, d, "METADATA")
        if not os.path.exists(meta_path):
            continue
        msg = email.parser.HeaderParser().parsestr(open(meta_path, encoding="utf-8", errors="replace").read())
        reqs = []
        for line in msg.get_all("Requires-Dist") or []:
            if "extra ==" in line:
                continue
            if "python_version" in line and "< '3.13'" in line.replace('"', "'"):
                continue
            name = re.split(r"[\[\s<>=!~;(]", line.strip(), maxsplit=1)[0]
            if name:
                reqs.append(norm(name))
        return reqs
    return []


def install(pkg: str, seen: set, depth: int = 0) -> None:
    key = norm(pkg)
    if key in seen:
        return
    seen.add(key)
    if os.path.isdir(os.path.join(VENDOR, key.replace("-", "_"))) or os.path.isdir(os.path.join(VENDOR, key)):
        print("skip(已存在)", key)
        for dep in installed_requires(key):
            install(dep, seen, depth + 1)
        return
    c = pick(pkg)
    if not c:
        print("!! 找不到可用 wheel:", pkg)
        return
    _, rank, version, tag, url = c
    fn = os.path.basename(url)
    path = os.path.join(DL, fn)
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        t = time.time()
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120, context=CTX) as r, open(path, "wb") as f:
            f.write(r.read())
        speed = os.path.getsize(path) / 1024 / max(time.time() - t, 0.01)
        print(f"下载 {fn} {os.path.getsize(path)//1024}KB {speed:.0f}KB/s")
    with zipfile.ZipFile(path) as z:
        z.extractall(VENDOR)
    print("  " * depth + f"安装 {key}=={version}")
    for dep in requires_of(path, pkg):
        if dep in ("python",) or dep.startswith("extra"):
            continue
        install(dep, seen, depth + 1)


def main():
    roots = sys.argv[1:] or ["fastapi", "uvicorn", "sqlalchemy", "python-dotenv"]
    seen: set[str] = set()
    for p in roots:
        install(p, seen)
    print("done")


if __name__ == "__main__":
    main()
