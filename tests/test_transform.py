import unittest

from reportkit import line_total, net_amount, parse_rows, tax_amount

from tests import fixtures


class NetAmountTest(unittest.TestCase):
    def test_no_discount(self):
        row = parse_rows("A1|SKU-1|online|2|10.00|0")[0]
        self.assertAlmostEqual(net_amount(row), 20.0)

    def test_ten_percent_off(self):
        row = parse_rows("A1|SKU-1|online|1|5.50|10")[0]
        self.assertAlmostEqual(net_amount(row), 4.95)

    def test_hundred_percent_off_is_zero(self):
        row = parse_rows("A1|SKU-1|online|4|8.00|100")[0]
        self.assertEqual(net_amount(row), 0.0)

    def test_quantity_multiplies(self):
        row = parse_rows("A1|SKU-1|online|3|2.00|0")[0]
        self.assertAlmostEqual(net_amount(row), 6.0)

    def test_half_price_of_a_quarter(self):
        row = parse_rows("A1|SKU-1|online|1|0.25|50")[0]
        self.assertEqual(net_amount(row), 0.125)

    def test_free_item(self):
        row = parse_rows("A1|SKU-1|online|1|0.00|0")[0]
        self.assertEqual(net_amount(row), 0.0)


class TaxAmountTest(unittest.TestCase):
    def row(self, channel, price="10.00", qty="1", discount="0"):
        return parse_rows("A1|SKU-1|%s|%s|%s|%s" % (channel, qty, price, discount))[0]

    def test_online_six_percent(self):
        self.assertAlmostEqual(tax_amount(self.row("online")), 0.6)

    def test_retail_thirteen_percent(self):
        self.assertAlmostEqual(tax_amount(self.row("retail")), 1.3)

    def test_partner_is_tax_free(self):
        self.assertEqual(tax_amount(self.row("partner")), 0.0)

    def test_wholesale_three_percent(self):
        self.assertAlmostEqual(tax_amount(self.row("wholesale")), 0.3)

    def test_tax_on_a_discounted_line(self):
        self.assertAlmostEqual(tax_amount(self.row("retail", price="5.50", discount="10")), 0.6435)

    def test_tax_is_zero_when_nothing_is_due(self):
        self.assertEqual(tax_amount(self.row("retail", price="0.00")), 0.0)


class LineTotalTest(unittest.TestCase):
    def test_net_plus_tax(self):
        row = parse_rows("A1|SKU-1|retail|2|10.00|0")[0]
        self.assertAlmostEqual(line_total(row), 20.0 + 2.6)

    def test_partner_total_equals_net(self):
        row = parse_rows("A1|SKU-1|partner|2|10.00|0")[0]
        self.assertEqual(line_total(row), net_amount(row))

    def test_fixture_rows_are_consistent(self):
        rows = parse_rows(fixtures.FOUR)
        for row in rows:
            self.assertAlmostEqual(line_total(row), net_amount(row) + tax_amount(row))


if __name__ == "__main__":
    unittest.main()
