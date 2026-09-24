"""兼容门面：挂钩实现搬到了 adapters/hooks.py，这里只做转发。

老代码直接 import reportkit.plugins，还摸 _REGISTERED 这种私有名，都保持可用。
_REGISTERED 与实现那边是同一个列表对象，原地修改两边都看得见。
"""

from .adapters.hooks import (
    _DEFAULT_HOOKS,
    _REGISTERED,
    flag_big_orders,
    flag_empty_report,
    install_default_hooks,
    register_hook,
    registered_hooks,
)

__all__ = [
    "flag_big_orders",
    "flag_empty_report",
    "install_default_hooks",
    "register_hook",
    "registered_hooks",
]
