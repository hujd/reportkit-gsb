"""领域层：错误类型、业务规则常量、金额舍入、行到金额的变换、聚合。

不 import 其它三层（pipeline / formatting / adapters）。
"""

from .aggregate import (
    aggregate_by_channel,
    aggregate_legacy,
    aggregate_orders,
    bucket_list,
    summarize_totals,
)
from .constants import CHANNELS, FIELD_COUNT, REPORT_VERSION, TAX_RATES
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
from .rounding import round_money, round_money_half_up
from .transform import line_total, net_amount, tax_amount
