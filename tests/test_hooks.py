import unittest

import reportkit.core as core
from reportkit import apply_hooks, parse_rows, plugins, run_pipeline

from tests import fixtures


class HookListGuard(unittest.TestCase):
    """挂钩是模块级状态，每个用例跑完要还原，不然会串到别的用例上。"""

    def setUp(self):
        self.hooks = list(core._HOOKS)
        self.registered = list(plugins._REGISTERED)

    def tearDown(self):
        core._HOOKS[:] = self.hooks
        plugins._REGISTERED[:] = self.registered


class DefaultHooksTest(HookListGuard):
    def test_two_default_hooks(self):
        self.assertEqual(len(plugins.install_default_hooks()), 2)

    def test_default_hooks_are_installed_at_import_time(self):
        self.assertEqual(core._HOOKS, list(plugins.install_default_hooks()))

    def test_no_extra_hooks_registered(self):
        self.assertEqual(plugins.registered_hooks(), [])

    def test_big_order_is_flagged(self):
        rows = parse_rows("A1|SKU-1|online|1|1000.00|0")
        self.assertEqual(plugins.flag_big_orders(rows, {}), "contains an order of 1000.00 or more")

    def test_exactly_one_thousand_counts_as_big(self):
        rows = parse_rows("A1|SKU-1|online|2|500.00|0")
        self.assertEqual(plugins.flag_big_orders(rows, {}), "contains an order of 1000.00 or more")

    def test_just_below_the_threshold_is_not_flagged(self):
        rows = parse_rows("A1|SKU-1|online|1|999.99|0")
        self.assertIsNone(plugins.flag_big_orders(rows, {}))

    def test_empty_rows_are_flagged(self):
        self.assertEqual(plugins.flag_empty_report([], {}), "no rows parsed")

    def test_rows_are_not_flagged_as_empty(self):
        self.assertIsNone(plugins.flag_empty_report(parse_rows(fixtures.ONE), {}))


class RegisterHookTest(HookListGuard):
    def test_register_returns_the_new_count(self):
        self.assertEqual(plugins.register_hook(lambda rows, buckets: None), 3)

    def test_registered_hook_shows_up_in_the_registry(self):
        hook = lambda rows, buckets: None  # noqa: E731
        plugins.register_hook(hook)
        self.assertEqual(plugins.registered_hooks(), [hook])

    def test_non_callable_is_rejected(self):
        with self.assertRaises(TypeError):
            plugins.register_hook("not a hook")

    def test_registered_hook_contributes_a_note(self):
        plugins.register_hook(lambda rows, buckets: "custom hook ran")
        text = run_pipeline(fixtures.ONE, title="Daily")
        self.assertIn("note: custom hook ran", text)

    def test_header_hook_count_is_frozen_at_import_time(self):
        plugins.register_hook(lambda rows, buckets: None)
        self.assertIn("hooks=2", run_pipeline(fixtures.ONE, title="Daily"))

    def test_apply_hooks_returns_only_non_empty_outcomes(self):
        plugins.register_hook(lambda rows, buckets: None)
        plugins.register_hook(lambda rows, buckets: "second")
        self.assertEqual(apply_hooks(parse_rows(fixtures.ONE), {}), ["second"])


class PipelineHooksTest(HookListGuard):
    def test_pipeline_notes_big_orders(self):
        text = run_pipeline("A1|SKU-1|online|1|1200.00|0", title="Daily")
        self.assertIn("note: contains an order of 1000.00 or more", text)

    def test_pipeline_notes_empty_reports(self):
        self.assertIn("note: no rows parsed", run_pipeline("", title="Daily"))

    def test_small_orders_get_no_note(self):
        self.assertNotIn("note:", run_pipeline(fixtures.ONE, title="Daily"))


if __name__ == "__main__":
    unittest.main()
