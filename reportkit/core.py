"""兼容门面：reportkit.core 的旧名字（含 _HOOKS 这类私有名）都还能用。

实现已经拆到 domain/ pipeline/ formatting/ adapters/ 四层，这里只做转发，
本身不含任何逻辑。老脚本 import reportkit.core 不需要改。
"""

import math  # noqa: F401  老脚本可能直接摸 core.math / core.os，留着
import os  # noqa: F401

from . import plugins  # noqa: F401  core.plugins 这个属性一直存在，别丢
from .adapters.hooks import _HOOKS, apply_hooks
from .adapters.orchestration import run_pipeline, summarize_totals
from .adapters.persistence import write_report
from .domain.aggregate import (
    aggregate_by_channel,
    aggregate_legacy,
    aggregate_orders,
    bucket_list,
)
from .domain.constants import (
    CHANNELS,
    COUNT_WIDTH,
    FIELD_COUNT,
    GROUP_WIDTH,
    REPORT_VERSION,
    RULE_WIDTH,
    TAX_RATES,
    TOTAL_WIDTH,
)
from .domain.errors import (
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
from .domain.meta import _CACHE, report_meta
from .domain.rounding import round_money, round_money_half_up
from .domain.transform import line_total, net_amount, tax_amount
from .formatting.render import (
    _pad_left,
    _pad_right,
    _render_bucket_line,
    format_money,
    render_report,
)
from .pipeline.convert import parse_float, parse_int
from .pipeline.parse import parse_line, parse_rows
from .pipeline.validate import _is_sku, validate_row

# ReportError 的 __module__ 保持指向这个旧模块名：未捕获异常时 traceback 打印的是
# "reportkit.core.ReportError: ..."，下游日志/告警可能按这串文字匹配。类本体住在
# domain.errors，这里只改它自报的家门，行为不变。
ReportError.__module__ = __name__
