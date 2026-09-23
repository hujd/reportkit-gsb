"""报表挂钩：注册和默认挂钩。

这个模块和 core.py 是互相 import 的（历史原因，动的时候小心）。
两边都只在函数体里用对面模块的东西，所以能跑起来；顺序一变就容易炸。
"""

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
    """把默认挂钩交出去。core 在 import 的时候就调它，报表头里的 hooks= 就是这个数。"""
    return [flag_big_orders, flag_empty_report]


def register_hook(hook):
    """老调用方插自己的挂钩，返回现在的挂钩总数。"""
    if not callable(hook):
        raise TypeError("hook must be callable")
    _REGISTERED.append(hook)
    from . import core

    core._HOOKS.append(hook)
    return len(core._HOOKS)


def registered_hooks():
    """已经注册过的挂钩（不含默认那两个）。"""
    return list(_REGISTERED)
