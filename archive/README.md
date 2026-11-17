# archive · 归档目录

本目录存放**不再参与运行**、但为了可追溯而保留的文件。**不要在这里直接运行脚本**——它们内部的路径是相对原位置（`astock_sectors\`）写的，移到这里后相对路径会失效。

## one-off-scripts/

2026-11-15 清理时从根目录移入的一次性脚本：

| 文件 | 当时的用途 | 是否还需要 |
|---|---|---|
| `probe.py` / `probe2.py` / `probe3.py` / `probe4.py` | 探测东方财富/腾讯/新浪接口可用性 | 否（已定源 baostock） |
| `probe_sw.py` | 探测申万宏源成分股接口 | 否（已稳定使用） |
| `fetch_boards.py` | 抓东方财富行业/概念板块（接口被 WAF 拒绝） | 否 |
| `fetch_kline.py` / `fetch_kline2.py` | 腾讯月K抓取（被 baostock 取代） | 否，但可复制回根目录重抓 `data\kline_month` |
| `try_baostock.py` | baostock 连通性测试 | 否 |
| `render_pdf_pages.py` | PyMuPDF 渲染 PDF（3.13 不可用） | 否 |
| `vendor_matplotlib.py` / `vendor_office.py` | 早期手动解压 wheel 的脚本 | 否（已被 `service\vendor_backend2.py` 取代） |
| `check_adjust.py` | 查看复权因子，验证前复权口径 | 否（结论已写入 `service/docs/00`） |
| `crosscheck.py` / `crosscheck2.py` | 腾讯/新浪/baostock 三源比对 | 否（结论已固化：只用 baostock） |
| `validate_docx.py` / `validate_xlsx.py` | 报告交付前的结构与宽度校验 | 否（一次性） |

## data-probes/

| 文件 | 内容 |
|---|---|
| `crosscheck_report.json` | 151 只股票的三源月度收益差异统计（决定「只用 baostock」的证据） |
| `kline_meta.json` | 早期腾讯月K抓取的元数据（对应 `data\kline_month`） |

## 恢复方式

```powershell
# 例如需要重新抓腾讯月K
Copy-Item archive\one-off-scripts\fetch_kline.py .
python fetch_kline.py
```

## 清理原则

- 能由现有脚本重新生成的 → 删除（如 `charts/`、临时缓存）。
- 一次性、不再运行的 → 移入本目录，不删除，保留决策证据。
- 运行依赖（`vendor/`、`node_modules/`、`data/*.json`、`交付/`）→ 不动。
