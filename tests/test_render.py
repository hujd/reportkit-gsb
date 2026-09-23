import os
import tempfile
import unittest

from reportkit import (
    ReportError,
    aggregate_by_channel,
    aggregate_orders,
    parse_rows,
    render_report,
    report_meta,
    write_report,
)
from reportkit.core import E_TITLE

from tests import fixtures


def render(text, **kwargs):
    rows = parse_rows(text)
    group_by = kwargs.pop("group_by", "sku")
    title = kwargs.pop("title", "Daily")
    buckets = aggregate_orders(rows, group_by=group_by)
    return render_report(buckets, title=title, **kwargs)


class HeaderTest(unittest.TestCase):
    def test_the_three_header_lines(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertEqual(lines[0], "REPORT: Daily")
        self.assertEqual(lines[1], "profile: bankers  scale=2  hooks=2")
        self.assertEqual(lines[2], "version: reportkit 1.3.0")

    def test_rule_width(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertEqual(lines[3], "-" * 38)
        self.assertEqual(len(lines[3]), 38)

    def test_two_rules(self):
        text = render(fixtures.ONE)
        self.assertEqual(text.count("-" * 38), 2)

    def test_meta_reports_the_bankers_profile(self):
        meta = report_meta()
        self.assertEqual(meta["profile"], "bankers")
        self.assertEqual(meta["scale"], 2)
        self.assertEqual(meta["hooks"], 2)

    def test_meta_is_a_copy(self):
        meta = report_meta()
        meta["profile"] = "changed"
        self.assertEqual(report_meta()["profile"], "bankers")


class LayoutTest(unittest.TestCase):
    def test_group_line_width(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertEqual(len(lines[4]), 38)

    def test_group_name_is_left_aligned(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertTrue(lines[4].startswith("SKU-1 "))

    def test_count_is_right_aligned_in_six(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertEqual(lines[4][20:26], "     2")

    def test_money_is_right_aligned_in_twelve(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertEqual(lines[4][26:38], "       20.00")

    def test_total_line(self):
        lines = render(fixtures.ONE).splitlines()
        self.assertEqual(lines[6][:20], "TOTAL" + " " * 15)
        self.assertEqual(lines[6][20:], "     2       20.00")

    def test_trailing_newline(self):
        self.assertTrue(render(fixtures.ONE).endswith("\n"))

    def test_group_order_is_first_seen(self):
        lines = render(fixtures.UNSORTED).splitlines()
        self.assertEqual([line[:5].strip() for line in lines[4:7]], ["SKU-2", "SKU-1", "SKU-3"])

    def test_empty_input_has_no_group_lines(self):
        lines = render("").splitlines()
        self.assertEqual(lines[3], "-" * 38)
        self.assertEqual(lines[4], "-" * 38)
        self.assertEqual(lines[5][:20], "TOTAL" + " " * 15)

    def test_total_sums_the_buckets(self):
        lines = render(fixtures.FOUR).splitlines()
        self.assertEqual(lines[-1][20:], "     7       96.70")

    def test_tax_column_adds_another_twelve_characters(self):
        rows = parse_rows(fixtures.TWO_CHANNELS)
        text = render_report(aggregate_by_channel(rows), title="Taxed", include_tax=True)
        lines = text.splitlines()
        self.assertEqual(len(lines[4]), 50)
        self.assertEqual(lines[4][38:50], "        1.20")
        self.assertEqual(lines[-1][38:50], "        1.84")

    def test_title_is_echoed_verbatim(self):
        self.assertEqual(render(fixtures.ONE, title="周结 / 华东").splitlines()[0], "REPORT: 周结 / 华东")


class ProblemsAndNotesTest(unittest.TestCase):
    def test_skipped_line(self):
        rows = parse_rows(fixtures.MIXED, strict=False)
        buckets = aggregate_orders(rows[0], group_by="sku")
        text = render_report(buckets, title="Weekly", problems=rows[1])
        self.assertIn("skipped: 1 line(s)\n", text)

    def test_no_skipped_line_without_problems(self):
        self.assertNotIn("skipped:", render(fixtures.ONE))

    def test_notes_are_one_per_line(self):
        rows = parse_rows(fixtures.ONE)
        text = render_report(aggregate_orders(rows, group_by="sku"), title="Daily",
                             notes=["first", "second"])
        self.assertIn("note: first\nnote: second\n", text)

    def test_no_notes_by_default(self):
        self.assertNotIn("note:", render(fixtures.ONE))

    def test_problems_come_before_notes(self):
        rows = parse_rows(fixtures.ONE)
        text = render_report(aggregate_orders(rows, group_by="sku"), title="Daily",
                             problems=[("E_X", "line 1: boom")], notes=["later"])
        self.assertLess(text.index("skipped:"), text.index("note:"))

    def test_empty_problems_list_adds_nothing(self):
        rows = parse_rows(fixtures.ONE)
        text = render_report(aggregate_orders(rows, group_by="sku"), title="Daily", problems=[])
        self.assertNotIn("skipped:", text)


class TitleValidationTest(unittest.TestCase):
    def test_non_string_title(self):
        with self.assertRaises(ReportError) as caught:
            render(fixtures.ONE, title=123)
        self.assertEqual(caught.exception.code, E_TITLE)

    def test_empty_title(self):
        with self.assertRaises(ReportError):
            render(fixtures.ONE, title="")

    def test_whitespace_title(self):
        with self.assertRaises(ReportError):
            render(fixtures.ONE, title="   ")

    def test_title_with_newline(self):
        with self.assertRaises(ReportError) as caught:
            render(fixtures.ONE, title="a\nb")
        self.assertEqual(caught.exception.message, "title must not contain a newline")

    def test_title_may_contain_pipes(self):
        self.assertIn("REPORT: a|b", render(fixtures.ONE, title="a|b"))


class WriteReportTest(unittest.TestCase):
    def test_returns_the_byte_count(self):
        rows = parse_rows(fixtures.ONE)
        buckets = aggregate_orders(rows, group_by="sku")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.txt")
            written = write_report(buckets, path, title="Daily")
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertEqual(written, len(content.encode("utf-8")))
            self.assertEqual(content, render_report(buckets, title="Daily"))

    def test_creates_missing_directories(self):
        rows = parse_rows(fixtures.ONE)
        buckets = aggregate_orders(rows, group_by="sku")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "deep", "nested", "out.txt")
            write_report(buckets, path, title="Daily")
            self.assertTrue(os.path.isfile(path))

    def test_files_are_written_with_unix_newlines(self):
        rows = parse_rows(fixtures.ONE)
        buckets = aggregate_orders(rows, group_by="sku")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.txt")
            write_report(buckets, path, title="Daily")
            with open(path, "rb") as handle:
                self.assertNotIn(b"\r\n", handle.read())

    def test_problems_and_notes_are_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.txt")
            write_report({}, path, title="Empty", problems=[("E_X", "line 1: boom")], notes=["hi"])
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("skipped: 1 line(s)", content)
            self.assertIn("note: hi", content)


if __name__ == "__main__":
    unittest.main()
