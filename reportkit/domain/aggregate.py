"""聚合 —— 三个口径各写一遍，别合并，它们要的数字不一样。"""

from .errors import E_GROUP_BY, ReportError
from .rounding import round_money, round_money_half_up
from .transform import net_amount, tax_amount


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


def summarize_totals(buckets):
    """给脚本用的小工具：把桶里的钱和件数加起来。"""
    count = 0
    money = 0.0
    for bucket in bucket_list(buckets):
        count += bucket["count"]
        money += bucket["total"]
    return count, money
