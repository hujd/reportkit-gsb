"""金额舍入。两套口径都留着，报表对账各用各的，别合并。"""

import math


def round_money(value):
    """金额舍入到分，走 Python 默认的银行家舍入。"""
    return round(value, 2)


def round_money_half_up(value):
    """金额舍入到分，四舍五入（老口径，报表对账用这个）。"""
    if value < 0:
        return -math.floor(-value * 100 + 0.5) / 100.0
    return math.floor(value * 100 + 0.5) / 100.0
