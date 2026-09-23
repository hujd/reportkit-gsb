import unittest

from reportkit import ReportError, parse_float, parse_int, parse_line, parse_rows
from reportkit.core import E_EMPTY_FIELD, E_FIELDS

from tests import fixtures


class ParseLineTest(unittest.TestCase):
    def test_six_fields_are_split_into_a_row(self):
        row = parse_line("A1|SKU-1|online|2|10.00|0")
        self.assertEqual(row["order_id"], "A1")
        self.assertEqual(row["sku"], "SKU-1")
        self.assertEqual(row["channel"], "online")
        self.assertEqual(row["qty"], "2")
        self.assertEqual(row["unit_price"], "10.00")
        self.assertEqual(row["discount_pct"], "0")

    def test_fields_keep_their_raw_text_until_validation(self):
        row = parse_line("A1|SKU-1|web|2|10.00|0")
        self.assertEqual(row["channel"], "web")
        self.assertEqual(row["qty"], "2")

    def test_too_few_fields(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("A1|SKU-1|online|2|10.00")
        self.assertEqual(caught.exception.code, E_FIELDS)
        self.assertEqual(str(caught.exception), "line 1: expected 6 fields, got 5")

    def test_too_many_fields(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("A1|SKU-1|online|2|10.00|0|extra")
        self.assertEqual(caught.exception.code, E_FIELDS)
        self.assertEqual(caught.exception.message, "expected 6 fields, got 7")

    def test_empty_line_is_one_field(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("")
        self.assertEqual(caught.exception.message, "expected 6 fields, got 1")

    def test_empty_order_id(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("|SKU-1|online|2|10.00|0")
        self.assertEqual(caught.exception.code, E_EMPTY_FIELD)
        self.assertEqual(caught.exception.message, "field order_id is empty")

    def test_empty_sku(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("A1||online|2|10.00|0")
        self.assertEqual(caught.exception.message, "field sku is empty")

    def test_empty_channel(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("A1|SKU-1||2|10.00|0")
        self.assertEqual(caught.exception.message, "field channel is empty")

    def test_empty_discount(self):
        with self.assertRaises(ReportError) as caught:
            parse_line("A1|SKU-1|online|2|10.00|")
        self.assertEqual(caught.exception.message, "field discount_pct is empty")

    def test_surrounding_whitespace_is_trimmed(self):
        row = parse_line("  A1 | SKU-1 | online | 2 | 10.00 | 0 ")
        self.assertEqual(row["sku"], "SKU-1")
        self.assertEqual(row["qty"], "2")

    def test_line_number_is_attached(self):
        row = parse_line("A1|SKU-1|online|2|10.00|0", line_no=17)
        self.assertEqual(row["line"], 17)


class ParseRowsTest(unittest.TestCase):
    def test_plain_text(self):
        rows = parse_rows(fixtures.ONE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sku"], "SKU-1")

    def test_strict_returns_a_list_not_a_tuple(self):
        rows = parse_rows(fixtures.TWO_CHANNELS, strict=True)
        self.assertIsInstance(rows, list)

    def test_blank_lines_are_skipped(self):
        rows = parse_rows("\n\nA1|SKU-1|online|2|10.00|0\n\n")
        self.assertEqual(len(rows), 1)

    def test_whitespace_only_lines_are_skipped(self):
        rows = parse_rows("   \nA1|SKU-1|online|2|10.00|0\n\t\n")
        self.assertEqual(len(rows), 1)

    def test_comment_lines_are_skipped(self):
        rows = parse_rows("# hi\nA1|SKU-1|online|2|10.00|0\n")
        self.assertEqual(len(rows), 1)

    def test_indented_comment_is_skipped(self):
        rows = parse_rows("   # hi\nA1|SKU-1|online|2|10.00|0\n")
        self.assertEqual(len(rows), 1)

    def test_comment_only_text_has_no_rows(self):
        self.assertEqual(parse_rows("# a\n# b\n"), [])

    def test_empty_text_has_no_rows(self):
        self.assertEqual(parse_rows(""), [])

    def test_hash_inside_a_field_is_not_a_comment(self):
        with self.assertRaises(ReportError) as caught:
            parse_rows("A1|#F|online|2|10.00|0")
        self.assertEqual(caught.exception.code, "E_BAD_SKU")

    def test_crlf_input(self):
        rows = parse_rows("A1|SKU-1|online|2|10.00|0\r\nA2|SKU-2|retail|1|1.00|0\r\n")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["sku"], "SKU-2")

    def test_line_numbers_follow_the_source(self):
        rows = parse_rows("# c\nA1|SKU-1|online|2|10.00|0\n\nA2|SKU-2|retail|1|1.00|0")
        self.assertEqual([row["line"] for row in rows], [2, 4])

    def test_strict_raises_on_the_first_bad_line(self):
        with self.assertRaises(ReportError) as caught:
            parse_rows("坏行\nA1|SKU-1|online|2|10.00|0")
        self.assertEqual(caught.exception.line, 1)

    def test_lenient_returns_rows_and_problems(self):
        rows, problems = parse_rows(fixtures.MIXED, strict=False)
        self.assertEqual(len(rows), 3)
        self.assertEqual(problems, [("E_FIELDS", "line 4: expected 6 fields, got 1")])

    def test_lenient_skips_the_bad_line_only(self):
        rows, _ = parse_rows("坏行\nA1|SKU-1|online|2|10.00|0\n也坏", strict=False)
        self.assertEqual([row["order_id"] for row in rows], ["A1"])

    def test_lenient_keeps_problems_in_source_order(self):
        _, problems = parse_rows("坏\nA1|SKU-1|online|2|10.00|0\n更坏\n另一坏", strict=False)
        self.assertEqual([message for _, message in problems],
                         ["line 1: expected 6 fields, got 1",
                          "line 3: expected 6 fields, got 1",
                          "line 4: expected 6 fields, got 1"])

    def test_lenient_reports_validation_problems_too(self):
        _, problems = parse_rows("A1|SKU-1|web|2|10.00|0", strict=False)
        self.assertEqual(problems[0][0], "E_UNKNOWN_CHANNEL")

    def test_lenient_missing_the_second_value_is_still_a_tuple(self):
        rows, problems = parse_rows(fixtures.ONE, strict=False)
        self.assertEqual(len(rows), 1)
        self.assertEqual(problems, [])


class ScalarHelpersTest(unittest.TestCase):
    def test_parse_int_accepts_int(self):
        self.assertEqual(parse_int(7, "qty", "E_BAD_QTY", 1), 7)

    def test_parse_int_accepts_string(self):
        self.assertEqual(parse_int("7", "qty", "E_BAD_QTY", 1), 7)

    def test_parse_int_accepts_padded_string(self):
        self.assertEqual(parse_int(" 7 ", "qty", "E_BAD_QTY", 1), 7)

    def test_parse_int_rejects_garbage(self):
        with self.assertRaises(ReportError) as caught:
            parse_int("x", "qty", "E_BAD_QTY", 3)
        self.assertEqual(caught.exception.code, "E_BAD_QTY")
        self.assertEqual(caught.exception.message, "field qty is not an integer: 'x'")
        self.assertEqual(caught.exception.line, 3)

    def test_parse_int_rejects_float_text(self):
        with self.assertRaises(ReportError):
            parse_int("1.5", "qty", "E_BAD_QTY", 1)

    def test_parse_float_accepts_string(self):
        self.assertEqual(parse_float("10.00", "unit_price", "E_BAD_PRICE", 1), 10.0)

    def test_parse_float_accepts_int(self):
        self.assertEqual(parse_float(3, "unit_price", "E_BAD_PRICE", 1), 3.0)

    def test_parse_float_accepts_float(self):
        self.assertEqual(parse_float(2.5, "unit_price", "E_BAD_PRICE", 1), 2.5)

    def test_parse_float_rejects_garbage(self):
        with self.assertRaises(ReportError) as caught:
            parse_float("abc", "unit_price", "E_BAD_PRICE", 2)
        self.assertEqual(caught.exception.message, "field unit_price is not a number: 'abc'")
        self.assertEqual(caught.exception.line, 2)

    def test_parse_float_rejects_empty(self):
        with self.assertRaises(ReportError):
            parse_float("", "unit_price", "E_BAD_PRICE", 1)


class ErrorTextTest(unittest.TestCase):
    def test_str_includes_the_line(self):
        exc = ReportError("E_X", "boom", 5)
        self.assertEqual(str(exc), "line 5: boom")

    def test_str_without_line(self):
        exc = ReportError("E_X", "boom")
        self.assertEqual(str(exc), "boom")

    def test_code_and_line_are_attributes(self):
        exc = ReportError("E_X", "boom", 5)
        self.assertEqual((exc.code, exc.message, exc.line), ("E_X", "boom", 5))


if __name__ == "__main__":
    unittest.main()
