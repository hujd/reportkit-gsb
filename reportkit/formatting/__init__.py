"""排版层：文本报表的渲染。只许 import domain。"""

from .render import format_money, render_report

__all__ = [
    "format_money",
    "render_report",
]
