import unittest

from reportkit import ReportError, legacy_api

ONLINE_ONLY = "A1|SKU-1|online|1|10.00|0"
RETAIL_ONLY = "A2|SKU-2|retail|1|20.00|0"


def default_filter():
    """summarize 那个可变默认参数就挂在这儿。"""
    return legacy_api.summarize.__defaults__[1]


def reset_default_filter():
    del default_filter()[:]


class SummarizeTest(unittest.TestCase):
    def setUp(self):
        reset_default_filter()

    def tearDown(self):
        reset_default_filter()

    def test_title_carries_the_channels_that_were_seen(self):
        text = legacy_api.summarize(ONLINE_ONLY)
        self.assertEqual(text.splitlines()[0], "REPORT: Summary / online")

    def test_grouped_by_channel(self):
        text = legacy_api.summarize(ONLINE_ONLY, title="Daily")
        self.assertIn("online", text.splitlines()[4])

    def test_the_default_filter_list_gets_written_to(self):
        legacy_api.summarize(ONLINE_ONLY)
        self.assertEqual(default_filter(), ["online"])

    def test_the_default_filter_leaks_into_the_next_call(self):
        """历史行为：不传 channel_filter 时，上一次见到的渠道还留在默认列表里。"""
        legacy_api.summarize(ONLINE_ONLY)
        text = legacy_api.summarize(RETAIL_ONLY)
        self.assertEqual(text.splitlines()[0], "REPORT: Summary / online,retail")

    def test_the_leak_survives_three_calls(self):
        legacy_api.summarize(ONLINE_ONLY, channel_filter=default_filter())
        legacy_api.summarize(RETAIL_ONLY, channel_filter=default_filter())
        legacy_api.summarize("A3|SKU-3|partner|1|1.00|0", channel_filter=default_filter())
        self.assertEqual(default_filter(), ["online", "retail", "partner"])

    def test_an_explicit_filter_wins(self):
        text = legacy_api.summarize(RETAIL_ONLY, channel_filter=[])
        self.assertEqual(text.splitlines()[0], "REPORT: Summary / retail")

    def test_bad_lines_are_skipped_not_raised(self):
        text = legacy_api.summarize("坏行\n" + ONLINE_ONLY)
        self.assertIn("skipped: 1 line(s)", text)

    def test_daily_total_row(self):
        text = legacy_api.summarize(ONLINE_ONLY)
        self.assertIn("TOTAL", text)


class TotalsTest(unittest.TestCase):
    def test_counts_and_money(self):
        self.assertEqual(legacy_api.totals(ONLINE_ONLY), {"count": 1, "total": 10.0})

    def test_two_rows_in_one_bucket(self):
        self.assertEqual(legacy_api.totals(ONLINE_ONLY + "\nA2|SKU-1|online|1|5.00|0"),
                         {"count": 2, "total": 15.0})

    def test_bad_line_raises(self):
        with self.assertRaises(ReportError):
            legacy_api.totals("坏行")


class SummarizeStrictTest(unittest.TestCase):
    def test_good_input(self):
        text = legacy_api.summarize_strict(ONLINE_ONLY, title="Daily")
        self.assertEqual(text.splitlines()[0], "REPORT: Daily")

    def test_bad_line_raises(self):
        with self.assertRaises(ReportError):
            legacy_api.summarize_strict("坏行\n" + ONLINE_ONLY)

    def test_empty_input_has_a_total_of_zero(self):
        self.assertIn("0        0.00", legacy_api.summarize_strict(""))


if __name__ == "__main__":
    unittest.main()
