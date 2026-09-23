"""老调用方的兼容壳。

这里每一个函数的签名和输出都被下游脚本依赖着，改之前先数数有多少人在用。
"""

from .core import (
    aggregate_orders,
    parse_rows,
    render_report,
    summarize_totals,
)


def summarize(rows_text, title="Summary", channel_filter=[]):
    """老的汇总入口。

    channel_filter 的默认值是个可变对象，这是历史遗留行为：老版本会把这次见到的
    渠道记进去，所以下一次不传参数调用时，上一次的渠道还在里面。调用方靠这个做
    "连续报表"，测试里也把这个现象固定下来了。别改成 None。
    """
    rows, problems = parse_rows(rows_text, strict=False)
    for row in rows:
        if row["channel"] not in channel_filter:
            channel_filter.append(row["channel"])
    buckets = aggregate_orders(rows, group_by="channel")
    subtitle = title + " / " + ",".join(channel_filter)
    return render_report(buckets, title=subtitle, problems=problems)


def totals(rows_text):
    """老脚本用的总件数和总金额。"""
    rows = parse_rows(rows_text, strict=True)
    count, money = summarize_totals(aggregate_orders(rows))
    return {"count": count, "total": money}


def summarize_strict(rows_text, title="Summary"):
    """老入口的严格版：坏行直接抛。"""
    rows = parse_rows(rows_text, strict=True)
    buckets = aggregate_orders(rows, group_by="channel")
    return render_report(buckets, title=title)
