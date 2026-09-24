"""编排入口：把解析、聚合、挂钩、渲染串起来。"""

from ..domain.aggregate import aggregate_by_channel, aggregate_orders, bucket_list
from ..formatting.render import render_report
from ..pipeline.parse import parse_rows
from . import hooks as _hooks


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

    hooks = _hooks._HOOKS
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
