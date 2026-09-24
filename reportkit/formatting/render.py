"""文本报表的渲染。字段宽度固定，输出的每一个字节都别改。"""

from ..domain.aggregate import bucket_list
from ..domain.constants import (
    COUNT_WIDTH,
    GROUP_WIDTH,
    REPORT_VERSION,
    RULE_WIDTH,
    TOTAL_WIDTH,
)
from ..domain.errors import E_TITLE, ReportError
from ..domain.meta import report_meta


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
