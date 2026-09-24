"""领域层：错误类型、业务规则常量、金额舍入、行到金额的变换、聚合。

这一层不许 import pipeline / formatting / adapters。
"""

from .aggregate import (
    aggregate_by_channel,
    aggregate_legacy,
    aggregate_orders,
    bucket_list,
)
from .constants import (
    CHANNELS,
    COUNT_WIDTH,
    FIELD_COUNT,
    GROUP_WIDTH,
    REPORT_VERSION,
    RULE_WIDTH,
    TAX_RATES,
    TOTAL_WIDTH,
)
from .errors import (
    E_BAD_DISCOUNT,
    E_BAD_PRICE,
    E_BAD_QTY,
    E_BAD_SKU,
    E_EMPTY_FIELD,
    E_FIELDS,
    E_GROUP_BY,
    E_TITLE,
    E_UNKNOWN_CHANNEL,
    ReportError,
)
from .meta import report_meta
from .rounding import round_money, round_money_half_up
from .transform import line_total, net_amount, tax_amount

__all__ = [
    "CHANNELS",
    "COUNT_WIDTH",
    "E_BAD_DISCOUNT",
    "E_BAD_PRICE",
    "E_BAD_QTY",
    "E_BAD_SKU",
    "E_EMPTY_FIELD",
    "E_FIELDS",
    "E_GROUP_BY",
    "E_TITLE",
    "E_UNKNOWN_CHANNEL",
    "FIELD_COUNT",
    "GROUP_WIDTH",
    "REPORT_VERSION",
    "RULE_WIDTH",
    "ReportError",
    "TAX_RATES",
    "TOTAL_WIDTH",
    "aggregate_by_channel",
    "aggregate_legacy",
    "aggregate_orders",
    "bucket_list",
    "line_total",
    "net_amount",
    "report_meta",
    "round_money",
    "round_money_half_up",
    "tax_amount",
]
