"""报表头元信息。

模块加载时就建好，报表头要用。hooks 数量由 adapters 在 import 时冻结进来
（_freeze_hook_count），之后不再变 —— 移动或改成动态读取都会让报表头跟着变。
"""

_CACHE = {
    "profile": "bankers",
    "scale": 2,
    "hooks": 0,
}


def _freeze_hook_count(count):
    """adapters 装好默认挂钩后调一次，把数量冻进报表头。"""
    _CACHE["hooks"] = count


def report_meta():
    """报表头要用的那几个字段。"""
    return dict(_CACHE)
