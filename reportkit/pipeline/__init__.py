"""流水线层：输入文本的解析、业务校验。只许 import domain。"""

from .conversion import parse_float, parse_int
from .parsing import parse_line, parse_rows
from .validation import validate_row
