"""错误类型与错误码。code 给程序看，message 给人看。"""

E_FIELDS = "E_FIELDS"
E_EMPTY_FIELD = "E_EMPTY_FIELD"
E_BAD_SKU = "E_BAD_SKU"
E_UNKNOWN_CHANNEL = "E_UNKNOWN_CHANNEL"
E_BAD_QTY = "E_BAD_QTY"
E_BAD_PRICE = "E_BAD_PRICE"
E_BAD_DISCOUNT = "E_BAD_DISCOUNT"
E_GROUP_BY = "E_GROUP_BY"
E_TITLE = "E_TITLE"


class ReportError(Exception):
    """所有报表错误。code 给程序看，message 给人看，line 是原始输入里的行号。"""

    def __init__(self, code, message, line=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.line = line

    def __str__(self):
        if self.line is None:
            return self.message
        return "line %d: %s" % (self.line, self.message)
