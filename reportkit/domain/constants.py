"""业务规则常量：渠道、字段数、税率、报表版本。"""

CHANNELS = ("online", "retail", "partner", "wholesale")

REPORT_VERSION = "1.3.0"

FIELD_COUNT = 6

TAX_RATES = {
    "online": 0.06,
    "retail": 0.13,
    "partner": 0.0,
    "wholesale": 0.03,
}
