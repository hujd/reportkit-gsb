"""业务规则常量：渠道、税率、报表版本、栏宽。改任何一个都会动到报表原文。"""

CHANNELS = ("online", "retail", "partner", "wholesale")

REPORT_VERSION = "1.3.0"

FIELD_COUNT = 6

TAX_RATES = {
    "online": 0.06,
    "retail": 0.13,
    "partner": 0.0,
    "wholesale": 0.03,
}

GROUP_WIDTH = 20
COUNT_WIDTH = 6
TOTAL_WIDTH = 12
RULE_WIDTH = GROUP_WIDTH + COUNT_WIDTH + TOTAL_WIDTH
