# reportkit

销售报表生成：把订单行按维度聚合成文本报表。平台里所有日结、周结、对账报表都走它。

纯 Python，只用标准库，Python 3.8+。

## 输入格式

竖线分隔的六列，一行一个订单行：

```
order_id|sku|channel|qty|unit_price|discount_pct
A1001|SKU-9|online|3|19.99|10
```

- `channel` 只能是 `online`、`retail`、`partner`、`wholesale`
- 空行和以 `#` 开头的行为注释，正文里随便放
- `qty` 1..9999，`unit_price` 0..1000000，`discount_pct` 0..100

## 用法

```python
from reportkit import parse_rows, aggregate_orders, render_report

rows = parse_rows(text)                       # 坏行直接抛 ReportError
buckets = aggregate_orders(rows, group_by="sku")
print(render_report(buckets, title="日结"))
```

或者一条龙：

```python
from reportkit import run_pipeline

print(run_pipeline(text, title="日结", group_by="sku"))
```

## 三个聚合入口

三个入口都在，口径不一样，报表数字也不一样，各有各的用途：

| 入口 | 分组 | 金额口径 |
|---|---|---|
| `aggregate_orders(rows, group_by=...)` | `sku` / `channel` / `order_id` | 逐行舍入后相加（明细口径） |
| `aggregate_by_channel(rows)` | `channel` | 先全部相加、最后统一舍入；额外带 `tax`（汇总口径） |
| `aggregate_legacy(rows)` | `sku` | 逐行四舍五入（对账口径，财务认这个数） |

## 报表长什么样

```
REPORT: 日结
profile: bankers  scale=2  hooks=2
version: reportkit 1.3.0
--------------------------------------
SKU-1                    8       12.34
--------------------------------------
TOTAL                    8       12.34
skipped: 1 line(s)
note: contains an order of 1000.00 or more
```

- 分组按第一次出现的顺序排，不排序
- 字段宽度固定，`REPORT:` / `profile:` / `version:` 三行固定会有
- `skipped:` 只在有坏行被跳过时出现（`parse_rows(strict=False)` / `run_pipeline`）
- `note:` 是挂钩给的提示，一行一条

## 挂钩

`plugins.py` 里有 `register_hook(hook)` / `registered_hooks()`，默认两个挂钩在 import
的时候装好（报表头里的 `hooks=` 就是装好那一刻的数量）。

`core.py` 和 `plugins.py` 之间有一个互相 import：能跑，但动的时候小心。

## 兼容壳

`legacy_api.py` 是给老脚本留的：`summarize()`、`totals()`、`summarize_strict()`。
下游还有一堆定时任务在调，签名和输出都不能变。

## 测试

```bash
python3 -m unittest discover -s tests -t . -v
```
