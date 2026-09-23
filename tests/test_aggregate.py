import unittest

from reportkit import (
    ReportError,
    aggregate_by_channel,
    aggregate_legacy,
    aggregate_orders,
    bucket_list,
    net_amount,
    parse_rows,
    round_money,
    round_money_half_up,
    summarize_totals,
)

from tests import fixtures


class GroupingTest(unittest.TestCase):
    def setUp(self):
        self.rows = parse_rows(fixtures.FOUR)

    def test_group_by_sku(self):
        buckets = aggregate_orders(self.rows, group_by="sku")
        self.assertEqual(list(buckets), ["SKU-1", "SKU-2"])

    def test_group_by_channel(self):
        buckets = aggregate_orders(self.rows, group_by="channel")
        self.assertEqual(list(buckets), ["online", "retail", "partner", "wholesale"])

    def test_group_by_order_id(self):
        buckets = aggregate_orders(self.rows, group_by="order_id")
        self.assertEqual(list(buckets), ["A1", "A2", "A3", "A4"])

    def test_count_sums_the_quantities(self):
        buckets = aggregate_orders(self.rows, group_by="sku")
        self.assertEqual(buckets["SKU-1"]["count"], 3)
        self.assertEqual(buckets["SKU-2"]["count"], 4)

    def test_total_adds_the_line_amounts(self):
        buckets = aggregate_orders(self.rows, group_by="sku")
        self.assertAlmostEqual(buckets["SKU-1"]["total"], 24.95)
        self.assertAlmostEqual(buckets["SKU-2"]["total"], 71.75)

    def test_each_bucket_carries_its_key(self):
        buckets = aggregate_orders(self.rows, group_by="sku")
        self.assertEqual(buckets["SKU-1"]["key"], "SKU-1")

    def test_buckets_do_not_share_state(self):
        buckets = aggregate_orders(self.rows, group_by="sku")
        self.assertIsNot(buckets["SKU-1"], buckets["SKU-2"])

    def test_unknown_dimension(self):
        with self.assertRaises(ReportError) as caught:
            aggregate_orders(self.rows, group_by="colour")
        self.assertEqual(caught.exception.code, "E_GROUP_BY")
        self.assertEqual(caught.exception.message, "cannot group by 'colour'")

    def test_empty_input_gives_no_buckets(self):
        self.assertEqual(aggregate_orders([], group_by="sku"), {})

    def test_bucket_order_is_first_seen_order(self):
        rows = parse_rows(fixtures.UNSORTED)
        self.assertEqual(list(aggregate_orders(rows, group_by="sku")), ["SKU-2", "SKU-1", "SKU-3"])
        self.assertEqual(list(aggregate_legacy(rows)), ["SKU-2", "SKU-1", "SKU-3"])

    def test_bucket_list_matches_the_mapping_order(self):
        buckets = aggregate_orders(self.rows, group_by="sku")
        self.assertEqual([bucket["key"] for bucket in bucket_list(buckets)], ["SKU-1", "SKU-2"])


class RoundingTrioTest(unittest.TestCase):
    """三个口径在同一个输入上给三个不同的数，这是财务那边定下来的，别合并。"""

    def setUp(self):
        self.rows = parse_rows(fixtures.PAIR)

    def test_each_line_nets_one_eighth_of_a_unit(self):
        self.assertEqual([net_amount(row) for row in self.rows], [0.125, 0.125])

    def test_detail_totals_round_each_line_first(self):
        self.assertEqual(aggregate_orders(self.rows, group_by="sku")["SKU-1"]["total"], 0.24)

    def test_summary_totals_round_once_at_the_end(self):
        self.assertEqual(aggregate_by_channel(self.rows)["online"]["total"], 0.25)

    def test_ledger_totals_round_each_line_half_up(self):
        self.assertEqual(aggregate_legacy(self.rows)["SKU-1"]["total"], 0.26)

    def test_the_three_amounts_are_all_different(self):
        detail = aggregate_orders(self.rows, group_by="sku")["SKU-1"]["total"]
        summary = aggregate_by_channel(self.rows)["online"]["total"]
        ledger = aggregate_legacy(self.rows)["SKU-1"]["total"]
        self.assertNotEqual(detail, summary)
        self.assertNotEqual(detail, ledger)
        self.assertNotEqual(summary, ledger)

    def test_bankers_rounding_drops_the_half_to_even(self):
        self.assertEqual(round_money(0.125), 0.12)

    def test_half_up_rounding_keeps_the_half(self):
        self.assertEqual(round_money_half_up(0.125), 0.13)

    def test_detail_total_is_the_sum_of_per_line_bankers_rounding(self):
        expected = round_money(0.125) + round_money(0.125)
        self.assertEqual(aggregate_orders(self.rows, group_by="sku")["SKU-1"]["total"], expected)

    def test_ledger_total_is_the_sum_of_per_line_half_up_rounding(self):
        expected = round_money_half_up(0.125) + round_money_half_up(0.125)
        self.assertEqual(aggregate_legacy(self.rows)["SKU-1"]["total"], expected)

    def test_summary_total_is_the_rounding_of_the_raw_sum(self):
        self.assertEqual(aggregate_by_channel(self.rows)["online"]["total"], round_money(0.25))

    def test_whole_amounts_agree_across_all_three(self):
        rows = parse_rows(fixtures.ONE)
        detail = aggregate_orders(rows, group_by="sku")["SKU-1"]["total"]
        summary = aggregate_by_channel(rows)["online"]["total"]
        ledger = aggregate_legacy(rows)["SKU-1"]["total"]
        self.assertEqual(detail, 20.0)
        self.assertEqual(detail, summary)
        self.assertEqual(detail, ledger)


class ChannelTotalsTest(unittest.TestCase):
    def setUp(self):
        self.rows = parse_rows(fixtures.FOUR)
        self.buckets = aggregate_by_channel(self.rows)

    def test_grouped_by_channel(self):
        self.assertEqual(list(self.buckets), ["online", "retail", "partner", "wholesale"])

    def test_online_tax(self):
        self.assertAlmostEqual(self.buckets["online"]["tax"], 1.2)

    def test_retail_tax_is_rounded_at_the_end(self):
        self.assertEqual(self.buckets["retail"]["tax"], 0.64)

    def test_partner_has_no_tax(self):
        self.assertEqual(self.buckets["partner"]["tax"], 0.0)

    def test_wholesale_tax(self):
        self.assertAlmostEqual(self.buckets["wholesale"]["tax"], 1.5)

    def test_totals_are_rounded(self):
        self.assertEqual(self.buckets["retail"]["total"], 4.95)

    def test_detail_buckets_have_no_tax_key(self):
        self.assertNotIn("tax", aggregate_orders(self.rows, group_by="sku")["SKU-1"])

    def test_ledger_buckets_have_no_tax_key(self):
        self.assertNotIn("tax", aggregate_legacy(self.rows)["SKU-1"])

    def test_empty_input_gives_no_buckets(self):
        self.assertEqual(aggregate_by_channel([]), {})


class LedgerAggregateTest(unittest.TestCase):
    def test_ledger_groups_by_sku(self):
        self.assertEqual(list(aggregate_legacy(parse_rows(fixtures.FOUR))), ["SKU-1", "SKU-2"])

    def test_counts_match_the_detail_view(self):
        rows = parse_rows(fixtures.FOUR)
        self.assertEqual(aggregate_legacy(rows)["SKU-1"]["count"],
                         aggregate_orders(rows, group_by="sku")["SKU-1"]["count"])

    def test_ledger_keys_are_sku(self):
        self.assertEqual(aggregate_legacy(parse_rows(fixtures.FOUR))["SKU-2"]["key"], "SKU-2")


class TotalsHelperTest(unittest.TestCase):
    def test_counts_and_money(self):
        buckets = aggregate_orders(parse_rows(fixtures.FOUR), group_by="sku")
        count, money = summarize_totals(buckets)
        self.assertEqual(count, 7)
        self.assertAlmostEqual(money, 96.7)

    def test_empty(self):
        self.assertEqual(summarize_totals({}), (0, 0.0))

    def test_matches_the_rendered_total(self):
        rows = parse_rows(fixtures.ONE)
        count, money = summarize_totals(aggregate_orders(rows, group_by="sku"))
        self.assertEqual((count, money), (2, 20.0))


if __name__ == "__main__":
    unittest.main()
