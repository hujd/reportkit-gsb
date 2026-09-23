"""reportkit —— 销售报表生成。

这个文件一个人把五件事都干了：解析、校验、变换、聚合、渲染与落盘。
别问为什么，问就是历史原因。
"""

import math
import os

CHANNELS = ("online", "retail", "partner", "wholesale")

REPORT_VERSION = "1.3.0"

FIELD_COUNT = 6

TAX_RATES = {
    "online": 0.06,
    "retail": 0.13,
    "partner": 0.0,
    "wholesale": 0.03,
}

GROUP_WIDTH = 20
COUNT_WIDTH = 6
TOTAL_WIDTH = 12
RULE_WIDTH = GROUP_WIDTH + COUNT_WIDTH + TOTAL_WIDTH

E_FIELDS = "E_FIELDS"
E_EMPTY_FIELD = "E_EMPTY_FIELD"
E_BAD_SKU = "E_BAD_SKU"
E_UNKNOWN_CHANNEL = "E_UNKNOWN_CHANNEL"
E_BAD_QTY = "E_BAD_QTY"
E_BAD_PRICE = "E_BAD_PRICE"
E_BAD_DISCOUNT = "E_BAD_DISCOUNT"
E_GROUP_BY = "E_GROUP_BY"
E_TITLE = "E_TITLE"


class ReportError(Exception):
    """所有报表错误。code 给程序看，message 给人看，line 是原始输入里的行号。"""

    def __init__(self, code, message, line=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.line = line

    def __str__(self):
        if self.line is None:
            return self.message
        return "line %d: %s" % (self.line, self.message)


# --------------------------------------------------------------------------
# 挂钩：老版本放在 plugins.py 里，为了少一次 import 后来搬到这儿又搬回去过
# --------------------------------------------------------------------------
from . import plugins  # noqa: E402  （放这儿是历史原因，别动）

_HOOKS = plugins.install_default_hooks()

# 模块加载时就建好，报表头要用。移动它会让报表头跟着变。
_CACHE = {
    "profile": "bankers",
    "scale": 2,
    "hooks": len(_HOOKS),
}


def report_meta():
    """报表头要用的那几个字段。"""
    return dict(_CACHE)


# --------------------------------------------------------------------------
# 解析
# --------------------------------------------------------------------------
def parse_line(raw, line_no=1):
    """把一行文本解析成字典。字段数不对就报 E_FIELDS。"""
    parts = raw.split("|")
    if len(parts) != FIELD_COUNT:
        raise ReportError(
            E_FIELDS,
            "expected %d fields, got %d" % (FIELD_COUNT, len(parts)),
            line_no,
        )
    order_id = parts[0].strip()
    sku = parts[1].strip()
    channel = parts[2].strip()
    qty_raw = parts[3].strip()
    price_raw = parts[4].strip()
    discount_raw = parts[5].strip()

    for name, value in (("order_id", order_id), ("sku", sku), ("channel", channel),
                        ("qty", qty_raw), ("unit_price", price_raw), ("discount_pct", discount_raw)):
        if value == "":
            raise ReportError(E_EMPTY_FIELD, "field %s is empty" % name, line_no)

    return {
        "order_id": order_id,
        "sku": sku,
        "channel": channel,
        "qty": qty_raw,
        "unit_price": price_raw,
        "discount_pct": discount_raw,
        "line": line_no,
    }


def parse_int(value, field, code, line_no):
    """整数转换。老调用方传进来的已经可能是 int 了。"""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ReportError(code, "field %s is not an integer: %r" % (field, value), line_no)


def parse_float(value, field, code, line_no):
    if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        raise ReportError(code, "field %s is not a number: %r" % (field, value), line_no)


def parse_rows(text, strict=True):
    """把整段输入变成行列表。

    strict=True：碰到坏行立刻抛。
    strict=False：跳过坏行，把问题按出现顺序收集起来一起返回。
    """
    rows = []
    problems = []
    for index, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() == "" or raw.lstrip().startswith("#"):
            continue
        try:
            row = parse_line(raw, index)
            row = validate_row(row)
        except ReportError as exc:
            if strict:
                raise
            problems.append((exc.code, str(exc)))
            continue
        rows.append(row)
    if strict:
        return rows
    return rows, problems


# --------------------------------------------------------------------------
# 校验
# --------------------------------------------------------------------------
def validate_row(row):
    """把解析出来的字典变成规范化之后的字典（数字已经是数字了）。"""
    line_no = row.get("line")

    sku = str(row["sku"])
    if len(sku) > 16 or not _is_sku(sku):
        raise ReportError(E_BAD_SKU, "bad sku %r" % sku, line_no)

    channel = str(row["channel"])
    if channel not in CHANNELS:
        raise ReportError(
            E_UNKNOWN_CHANNEL,
            "unknown channel %r, expected one of %s" % (channel, ", ".join(CHANNELS)),
            line_no,
        )

    qty = parse_int(row["qty"], "qty", E_BAD_QTY, line_no)
    if qty < 1 or qty > 9999:
        raise ReportError(E_BAD_QTY, "qty out of range: %d" % qty, line_no)

    price = parse_float(row["unit_price"], "unit_price", E_BAD_PRICE, line_no)
    if price < 0 or price > 1000000:
        raise ReportError(E_BAD_PRICE, "unit_price out of range: %s" % price, line_no)

    discount = parse_int(row["discount_pct"], "discount_pct", E_BAD_DISCOUNT, line_no)
    if discount < 0 or discount > 100:
        raise ReportError(E_BAD_DISCOUNT, "discount_pct out of range: %d" % discount, line_no)

    return {
        "order_id": str(row["order_id"]),
        "sku": sku,
        "channel": channel,
        "qty": qty,
        "unit_price": price,
        "discount_pct": discount,
        "line": line_no,
    }


def _is_sku(sku):
    if not sku:
        return False
    for ch in sku:
        if not (ch.isdigit() or ("A" <= ch <= "Z") or ch == "-"):
            return False
    return True


# --------------------------------------------------------------------------
# 变换
# --------------------------------------------------------------------------
def net_amount(row):
    """扣完折扣、不含税的金额。"""
    gross = row["unit_price"] * row["qty"]
    return gross * (100 - row["discount_pct"]) / 100.0


def tax_amount(row):
    """按渠道税率算税。"""
    return net_amount(row) * TAX_RATES[row["channel"]]


def line_total(row):
    """含税金额，未舍入。"""
    return net_amount(row) + tax_amount(row)


# --------------------------------------------------------------------------
# 聚合 —— 三个口径各写一遍，别合并，它们要的数字不一样
# --------------------------------------------------------------------------
def round_money(value):
    """金额舍入到分，走 Python 默认的银行家舍入。"""
    return round(value, 2)


def round_money_half_up(value):
    """金额舍入到分，四舍五入（老口径，报表对账用这个）。"""
    if value < 0:
        return -math.floor(-value * 100 + 0.5) / 100.0
    return math.floor(value * 100 + 0.5) / 100.0


def aggregate_orders(rows, group_by="sku"):
    """按维度聚合，逐行舍入再相加（明细口径）。"""
    if group_by not in ("sku", "channel", "order_id"):
        raise ReportError(E_GROUP_BY, "cannot group by %r" % group_by)

    buckets = {}
    for row in rows:
        key = row[group_by]
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {"key": key, "count": 0, "total": 0.0}
            buckets[key] = bucket
        bucket["count"] += row["qty"]
        bucket["total"] += round_money(net_amount(row))
    return buckets


def aggregate_by_channel(rows):
    """按渠道聚合，先全部相加再统一舍入（汇总口径）。"""
    buckets = {}
    for row in rows:
        key = row["channel"]
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {"key": key, "count": 0, "total": 0.0, "tax": 0.0}
            buckets[key] = bucket
        bucket["count"] += row["qty"]
        bucket["total"] += net_amount(row)
        bucket["tax"] += tax_amount(row)
    for bucket in buckets.values():
        bucket["total"] = round_money(bucket["total"])
        bucket["tax"] = round_money(bucket["tax"])
    return buckets


def aggregate_legacy(rows):
    """给对账用的老口径：逐行四舍五入再相加。报表数字不变，别顺手改。"""
    buckets = {}
    for row in rows:
        key = row["sku"]
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {"key": key, "count": 0, "total": 0.0}
            buckets[key] = bucket
        bucket["count"] += row["qty"]
        bucket["total"] += round_money_half_up(net_amount(row))
    return buckets


def bucket_list(buckets):
    """按分组第一次出现的顺序导出成列表，渲染和写盘都按这个顺序。"""
    return list(buckets.values())


# --------------------------------------------------------------------------
# 渲染
# --------------------------------------------------------------------------
def _pad_right(text, width):
    text = str(text)
    if len(text) > width:
        return text[:width]
    return text + " " * (width - len(text))


def _pad_left(text, width):
    text = str(text)
    if len(text) > width:
        return text
    return " " * (width - len(text)) + text


def format_money(value):
    return "%.2f" % value


def render_report(buckets, title="Report", problems=None, notes=None, include_tax=False):
    """渲染成文本报表。字段宽度固定，输出的每一个字节都别改。"""
    if not isinstance(title, str) or title.strip() == "":
        raise ReportError(E_TITLE, "title must be a non-empty string")
    if "\n" in title:
        raise ReportError(E_TITLE, "title must not contain a newline")

    meta = report_meta()
    lines = []
    lines.append("REPORT: %s" % title)
    lines.append("profile: %s  scale=%d  hooks=%d" % (meta["profile"], meta["scale"], meta["hooks"]))
    lines.append("version: reportkit %s" % REPORT_VERSION)
    lines.append("-" * RULE_WIDTH)

    rows = bucket_list(buckets)
    total_count = 0
    total_money = 0.0
    total_tax = 0.0
    for bucket in rows:
        lines.append(_render_bucket_line(bucket, include_tax))
        total_count += bucket["count"]
        total_money += bucket["total"]
        if include_tax:
            total_tax += bucket.get("tax", 0.0)

    lines.append("-" * RULE_WIDTH)
    if include_tax:
        lines.append(
            _pad_right("TOTAL", GROUP_WIDTH)
            + _pad_left(total_count, COUNT_WIDTH)
            + _pad_left(format_money(total_money), TOTAL_WIDTH)
            + _pad_left(format_money(total_tax), TOTAL_WIDTH)
        )
    else:
        lines.append(
            _pad_right("TOTAL", GROUP_WIDTH)
            + _pad_left(total_count, COUNT_WIDTH)
            + _pad_left(format_money(total_money), TOTAL_WIDTH)
        )
    if problems:
        lines.append("skipped: %d line(s)" % len(problems))
    for note in notes or ():
        lines.append("note: %s" % note)
    return "\n".join(lines) + "\n"


def _render_bucket_line(bucket, include_tax):
    head = _pad_right(bucket["key"], GROUP_WIDTH) + _pad_left(bucket["count"], COUNT_WIDTH)
    if include_tax:
        return head + _pad_left(format_money(bucket["total"]), TOTAL_WIDTH) + _pad_left(
            format_money(bucket.get("tax", 0.0)), TOTAL_WIDTH
        )
    return head + _pad_left(format_money(bucket["total"]), TOTAL_WIDTH)


# --------------------------------------------------------------------------
# 落盘与串联
# --------------------------------------------------------------------------
def write_report(buckets, path, title="Report", problems=None, notes=None, include_tax=False):
    """把报表写到文件，返回写出去的字节数。"""
    text = render_report(buckets, title=title, problems=problems, notes=notes, include_tax=include_tax)
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return len(text.encode("utf-8"))


def run_pipeline(text, title="Report", group_by="sku", strict=False, include_tax=False):
    """解析 + 校验 + 聚合 + 渲染，一条龙。渲染好的报表文本直接返回。"""
    if strict:
        rows = parse_rows(text, strict=True)
        problems = []
    else:
        rows, problems = parse_rows(text, strict=False)

    if include_tax:
        buckets = aggregate_by_channel(rows)
    else:
        buckets = aggregate_orders(rows, group_by=group_by)

    hooks = _HOOKS
    notes = []
    for hook in hooks:
        outcome = hook(rows, buckets)
        if outcome:
            notes.append(str(outcome))
    return render_report(
        buckets, title=title, problems=problems, notes=notes, include_tax=include_tax
    )


def summarize_totals(buckets):
    """给脚本用的小工具：把桶里的钱和件数加起来。"""
    count = 0
    money = 0.0
    for bucket in bucket_list(buckets):
        count += bucket["count"]
        money += bucket["total"]
    return count, money


def apply_hooks(rows, buckets):
    """老 API 用的手动挂钩入口。"""
    out = []
    for hook in _HOOKS:
        outcome = hook(rows, buckets)
        if outcome:
            out.append(outcome)
    return out
