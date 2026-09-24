"""字符串到数字的转换，解析和校验共用。"""

from ..domain.errors import ReportError


def parse_int(value, field, code, line_no):
    """整数转换。老调用方传进来的已经可能是 int 了。"""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ReportError(code, "field %s is not an integer: %r" % (field, value), line_no)


def parse_float(value, field, code, line_no):
    if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        raise ReportError(code, "field %s is not a number: %r" % (field, value), line_no)
