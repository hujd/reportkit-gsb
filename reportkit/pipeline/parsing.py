"""输入文本的解析。"""

from ..domain.constants import FIELD_COUNT
from ..domain.errors import E_EMPTY_FIELD, E_FIELDS, ReportError
from .validation import validate_row


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
