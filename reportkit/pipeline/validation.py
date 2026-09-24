"""业务校验：把解析出来的字典变成规范化之后的字典。"""

from ..domain.constants import CHANNELS
from ..domain.errors import (
    E_BAD_DISCOUNT,
    E_BAD_PRICE,
    E_BAD_QTY,
    E_BAD_SKU,
    E_UNKNOWN_CHANNEL,
    ReportError,
)
from .conversion import parse_float, parse_int


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
