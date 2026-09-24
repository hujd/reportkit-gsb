"""报表挂钩：注册、默认挂钩，以及挂钩列表这块模块级状态。

_HOOKS 在 import 时就装好默认挂钩，报表头里的 hooks= 数量也在这一刻冻结
（见 domain.meta）。老调用方按 core._HOOKS / plugins._REGISTERED 的名字直接
摸这两个列表并原地改，所以它们必须始终是同一个列表对象，别重新赋值。
"""

from ..domain import meta as _meta

_DEFAULT_HOOKS = ("flag_big_orders", "flag_empty_report")

_REGISTERED = []


def flag_big_orders(rows, buckets):
    """有千元以上的单子就给报表加一条提示。"""
    for row in rows:
        if row["qty"] * row["unit_price"] >= 1000:
            return "contains an order of 1000.00 or more"
    return None


def flag_empty_report(rows, buckets):
    """一行都没解析出来时给报表加一条提示。"""
    if not rows:
        return "no rows parsed"
    return None


def install_default_hooks():
    """把默认挂钩交出去。import 的时候就调它，报表头里的 hooks= 就是这个数。"""
    return [flag_big_orders, flag_empty_report]


def register_hook(hook):
    """老调用方插自己的挂钩，返回现在的挂钩总数。"""
    if not callable(hook):
        raise TypeError("hook must be callable")
    _REGISTERED.append(hook)
    _HOOKS.append(hook)
    return len(_HOOKS)


def registered_hooks():
    """已经注册过的挂钩（不含默认那两个）。"""
    return list(_REGISTERED)


def apply_hooks(rows, buckets):
    """老 API 用的手动挂钩入口。"""
    out = []
    for hook in _HOOKS:
        outcome = hook(rows, buckets)
        if outcome:
            out.append(outcome)
    return out


# 模块加载时就装好默认挂钩，并把数量冻进报表头元信息。顺序别动。
_HOOKS = install_default_hooks()
_meta._freeze_hook_count(len(_HOOKS))
