"""适配层：挂钩、落盘，以及把 domain / pipeline / formatting 串起来的编排入口。

这一层可以 import 上面任意一层；上面三层不许反过来 import 这里。
"""

from .hooks import (
    apply_hooks,
    flag_big_orders,
    flag_empty_report,
    install_default_hooks,
    register_hook,
    registered_hooks,
)
from .orchestration import run_pipeline, summarize_totals
from .persistence import write_report

__all__ = [
    "apply_hooks",
    "flag_big_orders",
    "flag_empty_report",
    "install_default_hooks",
    "register_hook",
    "registered_hooks",
    "run_pipeline",
    "summarize_totals",
    "write_report",
]
