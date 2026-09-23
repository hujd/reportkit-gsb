import os
import tempfile
import unittest

from reportkit import (
    aggregate_by_channel,
    aggregate_orders,
    parse_rows,
    render_report,
    run_pipeline,
    write_report,
)

from tests import fixtures

RULE = "-" * 38

HEAD = (
    "REPORT: %s\n"
    "profile: bankers  scale=2  hooks=2\n"
    "version: reportkit 1.3.0\n"
)

DAILY = (
    HEAD % "Daily"
    + RULE + "\n"
    + "SKU-1                    2       20.00\n"
    + RULE + "\n"
    + "TOTAL                    2       20.00\n"
)

CENTS = (
    HEAD % "Cents"
    + RULE + "\n"
    + "SKU-1                    2        0.24\n"
    + RULE + "\n"
    + "TOTAL                    2        0.24\n"
)

WEEKLY = (
    HEAD % "Weekly"
    + RULE + "\n"
    + "SKU-1                    3     1220.00\n"
    + "SKU-2                    1        4.95\n"
    + RULE + "\n"
    + "TOTAL                    4     1224.95\n"
    + "skipped: 1 line(s)\n"
    + "note: contains an order of 1000.00 or more\n"
)

TAXED = (
    HEAD % "Taxed"
    + RULE + "\n"
    + "online                   2       20.00        1.20\n"
    + "retail                   1        4.95        0.64\n"
    + RULE + "\n"
    + "TOTAL                    3       24.95        1.84\n"
)

EMPTY = (
    HEAD % "Empty"
    + RULE + "\n"
    + RULE + "\n"
    + "TOTAL                    0        0.00\n"
    + "note: no rows parsed\n"
)

ORDER = (
    HEAD % "Order"
    + RULE + "\n"
    + "SKU-2                    1        1.00\n"
    + "SKU-1                    1        1.00\n"
    + "SKU-3                    1        1.00\n"
    + RULE + "\n"
    + "TOTAL                    3        3.00\n"
)


class GoldenReportTest(unittest.TestCase):
    """整份报表逐字节比对。这些字符串是财务和下游对账用的原文，改一个空格都算回归。"""

    def test_daily(self):
        self.assertEqual(run_pipeline(fixtures.ONE, title="Daily", group_by="sku"), DAILY)

    def test_cents(self):
        self.assertEqual(run_pipeline(fixtures.PAIR, title="Cents", group_by="sku"), CENTS)

    def test_weekly_with_a_bad_line_and_a_big_order(self):
        self.assertEqual(run_pipeline(fixtures.MIXED, title="Weekly", group_by="sku"), WEEKLY)

    def test_taxed(self):
        text = run_pipeline(fixtures.TWO_CHANNELS, title="Taxed", include_tax=True)
        self.assertEqual(text, TAXED)

    def test_empty(self):
        self.assertEqual(run_pipeline("", title="Empty"), EMPTY)

    def test_comment_only_input_looks_like_an_empty_report(self):
        text = run_pipeline("# 什么都没有\n", title="Empty")
        self.assertEqual(text, EMPTY)

    def test_groups_keep_first_seen_order(self):
        self.assertEqual(run_pipeline(fixtures.UNSORTED, title="Order", group_by="sku"), ORDER)

    def test_run_pipeline_matches_the_manual_chain(self):
        rows, problems = parse_rows(fixtures.MIXED, strict=False)
        buckets = aggregate_orders(rows, group_by="sku")
        manual = render_report(
            buckets,
            title="Weekly",
            problems=problems,
            notes=["contains an order of 1000.00 or more"],
        )
        self.assertEqual(manual, WEEKLY)

    def test_channel_grouping_uses_the_summary_column(self):
        self.assertEqual(run_pipeline(fixtures.TWO_CHANNELS, title="Taxed", include_tax=True),
                         TAXED)
        buckets = aggregate_by_channel(parse_rows(fixtures.TWO_CHANNELS))
        self.assertEqual(list(buckets), ["online", "retail"])

    def test_written_file_is_byte_identical(self):
        rows = parse_rows(fixtures.ONE)
        buckets = aggregate_orders(rows, group_by="sku")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.txt")
            write_report(buckets, path, title="Daily")
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), DAILY.encode("utf-8"))

    def test_no_carriage_returns_anywhere(self):
        self.assertNotIn("\r", run_pipeline(fixtures.MIXED, title="Weekly"))

    def test_every_line_is_at_most_the_rule_width_plus_a_tax_column(self):
        text = run_pipeline(fixtures.TWO_CHANNELS, title="Taxed", include_tax=True)
        for line in text.splitlines():
            self.assertLessEqual(len(line), 50)


if __name__ == "__main__":
    unittest.main()
