import unittest

from reportkit import ReportError, parse_line, validate_row
from reportkit.core import (
    E_BAD_DISCOUNT,
    E_BAD_PRICE,
    E_BAD_QTY,
    E_BAD_SKU,
    E_UNKNOWN_CHANNEL,
    E_EMPTY_FIELD,
)

from tests import fixtures


def raw(**overrides):
    row = {
        "order_id": "A1",
        "sku": "SKU-1",
        "channel": "online",
        "qty": "2",
        "unit_price": "10.00",
        "discount_pct": "0",
        "line": 1,
    }
    row.update(overrides)
    return row


class NormalisationTest(unittest.TestCase):
    def test_numbers_become_numbers(self):
        row = validate_row(raw())
        self.assertEqual(row["qty"], 2)
        self.assertIsInstance(row["qty"], int)
        self.assertAlmostEqual(row["unit_price"], 10.0)
        self.assertIsInstance(row["unit_price"], float)
        self.assertEqual(row["discount_pct"], 0)

    def test_line_number_survives(self):
        self.assertEqual(validate_row(raw(line=42))["line"], 42)

    def test_input_dict_is_not_mutated(self):
        source = raw()
        validate_row(source)
        self.assertEqual(source["qty"], "2")

    def test_parsed_row_can_be_validated(self):
        row = validate_row(parse_line("A1|SKU-1|online|2|10.00|0"))
        self.assertEqual(row["qty"], 2)

    def test_unknown_channel_is_only_caught_here(self):
        parsed = parse_line("A1|SKU-1|web|2|10.00|0")
        self.assertEqual(parsed["channel"], "web")
        with self.assertRaises(ReportError):
            validate_row(parsed)


class SkuTest(unittest.TestCase):
    def test_single_letter(self):
        self.assertEqual(validate_row(raw(sku="A"))["sku"], "A")

    def test_digits_and_dashes(self):
        self.assertEqual(validate_row(raw(sku="9-SKU-2"))["sku"], "9-SKU-2")

    def test_sixteen_characters_is_allowed(self):
        self.assertEqual(validate_row(raw(sku="A" * 16))["sku"], "A" * 16)

    def test_seventeen_characters_is_not(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(sku="A" * 17))
        self.assertEqual(caught.exception.code, E_BAD_SKU)

    def test_lowercase_is_not(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(sku="sku-1"))
        self.assertEqual(caught.exception.message, "bad sku 'sku-1'")

    def test_underscore_is_not(self):
        with self.assertRaises(ReportError):
            validate_row(raw(sku="SKU_1"))

    def test_space_is_not(self):
        with self.assertRaises(ReportError):
            validate_row(raw(sku="SKU 1"))

    def test_empty_is_not(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(sku=""))
        self.assertEqual(caught.exception.code, E_BAD_SKU)

    def test_message_and_line(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(sku="bad!", line=9))
        self.assertEqual(str(caught.exception), "line 9: bad sku 'bad!'")

    def test_empty_field_from_parse_line_is_a_different_code(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(parse_line("A1||online|2|10.00|0"))
        self.assertEqual(caught.exception.code, E_EMPTY_FIELD)


class ChannelTest(unittest.TestCase):
    def test_all_four_channels_are_accepted(self):
        for channel in ("online", "retail", "partner", "wholesale"):
            self.assertEqual(validate_row(raw(channel=channel))["channel"], channel)

    def test_unknown_channel_message(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(channel="web"))
        self.assertEqual(caught.exception.code, E_UNKNOWN_CHANNEL)
        self.assertEqual(
            caught.exception.message,
            "unknown channel 'web', expected one of online, retail, partner, wholesale",
        )

    def test_channel_is_case_sensitive(self):
        with self.assertRaises(ReportError):
            validate_row(raw(channel="Online"))

    def test_channel_with_spaces_is_not_trimmed_by_validate(self):
        with self.assertRaises(ReportError):
            validate_row(raw(channel=" online "))


class QuantityTest(unittest.TestCase):
    def test_one_is_the_lower_bound(self):
        self.assertEqual(validate_row(raw(qty="1"))["qty"], 1)

    def test_9999_is_the_upper_bound(self):
        self.assertEqual(validate_row(raw(qty="9999"))["qty"], 9999)

    def test_zero_is_rejected(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(qty="0"))
        self.assertEqual(caught.exception.code, E_BAD_QTY)
        self.assertEqual(caught.exception.message, "qty out of range: 0")

    def test_10000_is_rejected(self):
        with self.assertRaises(ReportError):
            validate_row(raw(qty="10000"))

    def test_negative_is_rejected(self):
        with self.assertRaises(ReportError):
            validate_row(raw(qty="-3"))

    def test_text_is_rejected(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(qty="x", line=4))
        self.assertEqual(caught.exception.message, "field qty is not an integer: 'x'")

    def test_fraction_is_rejected(self):
        with self.assertRaises(ReportError):
            validate_row(raw(qty="1.5"))


class PriceTest(unittest.TestCase):
    def test_zero_is_allowed(self):
        self.assertAlmostEqual(validate_row(raw(unit_price="0"))["unit_price"], 0.0)

    def test_one_million_is_allowed(self):
        self.assertAlmostEqual(validate_row(raw(unit_price="1000000"))["unit_price"], 1000000.0)

    def test_negative_is_rejected(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(unit_price="-1"))
        self.assertEqual(caught.exception.code, E_BAD_PRICE)
        self.assertEqual(caught.exception.message, "unit_price out of range: -1.0")

    def test_over_a_million_is_rejected(self):
        with self.assertRaises(ReportError):
            validate_row(raw(unit_price="1000000.01"))

    def test_text_is_rejected(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(unit_price="abc"))
        self.assertEqual(caught.exception.message, "field unit_price is not a number: 'abc'")

    def test_integer_like_text_is_a_float_afterwards(self):
        value = validate_row(raw(unit_price="7"))["unit_price"]
        self.assertIsInstance(value, float)


class DiscountTest(unittest.TestCase):
    def test_zero_is_allowed(self):
        self.assertEqual(validate_row(raw(discount_pct="0"))["discount_pct"], 0)

    def test_hundred_is_allowed(self):
        self.assertEqual(validate_row(raw(discount_pct="100"))["discount_pct"], 100)

    def test_negative_is_rejected(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(discount_pct="-1"))
        self.assertEqual(caught.exception.code, E_BAD_DISCOUNT)

    def test_over_hundred_is_rejected(self):
        with self.assertRaises(ReportError) as caught:
            validate_row(raw(discount_pct="101"))
        self.assertEqual(caught.exception.message, "discount_pct out of range: 101")

    def test_text_is_rejected(self):
        with self.assertRaises(ReportError):
            validate_row(raw(discount_pct="half"))


class FixtureSanityTest(unittest.TestCase):
    def test_fixed_inputs_still_validate(self):
        from reportkit import parse_rows

        for text in (fixtures.ONE, fixtures.PAIR, fixtures.TWO_CHANNELS,
                     fixtures.FOUR, fixtures.UNSORTED):
            self.assertTrue(parse_rows(text))


if __name__ == "__main__":
    unittest.main()
