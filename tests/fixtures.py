"""测试用的固定输入。别改这些常量，报表数字都挂在上面。"""

ONE = "A1|SKU-1|online|2|10.00|0"

PAIR = "A1|SKU-1|online|1|0.25|50\nA2|SKU-1|online|1|0.25|50"

TWO_CHANNELS = "A1|SKU-1|online|2|10.00|0\nA2|SKU-2|retail|1|5.50|10"

FOUR = (
    "A1|SKU-1|online|2|10.00|0\n"
    "A2|SKU-1|retail|1|5.50|10\n"
    "A3|SKU-2|partner|3|7.25|0\n"
    "A4|SKU-2|wholesale|1|100.00|50"
)

MIXED = (
    "# 注释\n"
    "A1|SKU-1|online|2|10.00|0\n"
    "A2|SKU-2|retail|1|5.50|10\n"
    "坏行\n"
    "A3|SKU-1|wholesale|1|1200.00|0"
)

UNSORTED = (
    "A1|SKU-2|online|1|1.00|0\n"
    "A2|SKU-1|online|1|1.00|0\n"
    "A3|SKU-3|online|1|1.00|0"
)

RULE = "-" * 38

HEADER_DAILY = (
    "REPORT: Daily\n"
    "profile: bankers  scale=2  hooks=2\n"
    "version: reportkit 1.3.0\n"
)
