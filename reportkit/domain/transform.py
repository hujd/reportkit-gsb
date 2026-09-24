"""行到金额的变换。"""

from .constants import TAX_RATES


def net_amount(row):
    """扣完折扣、不含税的金额。"""
    gross = row["unit_price"] * row["qty"]
    return gross * (100 - row["discount_pct"]) / 100.0


def tax_amount(row):
    """按渠道税率算税。"""
    return net_amount(row) * TAX_RATES[row["channel"]]


def line_total(row):
    """含税金额，未舍入。"""
    return net_amount(row) + tax_amount(row)
