from __future__ import annotations

import unittest
from pathlib import Path

from checker.check_funnel import CAPTCHA_PATTERN, select_funnel_targets
from checker.check_links import check_link
from checker.check_uebersicht import is_tariff_page, reconcile
from checker.common import LinkInfo, load_config, load_linkliste, matches_any, compile_patterns
from tools.import_uebergabe import DEFAULT_SOURCE, parse_markdown


class _FailingClient:
    async def get(self, url):
        raise OSError("simulierter DNS-Fehler")


class SafetyTests(unittest.IsolatedAsyncioTestCase):
    def test_import_is_exact_and_deduplicated(self):
        data = parse_markdown(DEFAULT_SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(61, len(data))
        self.assertEqual(61, len({e["abschluss_url"] for e in data}))
        self.assertEqual(172, sum(len(e["tarife"]) for e in data))

    def test_checked_in_linklist_is_exact(self):
        links = load_linkliste()
        self.assertEqual(61, len(links))
        self.assertGreaterEqual(sum(len(link.tarife) for link in links), 172)
        self.assertEqual(61, len({link.url for link in links}))

    def test_critical_stop_patterns_are_active(self):
        patterns = compile_patterns(load_config()["stop_patterns"])
        for text in (
            "Jetzt abschließen", "Kostenpflichtig bestellen", "Zahlungspflichtig bestellen",
            "Verbindlich beantragen", "Antrag senden", "Antrag abschicken", "Jetzt kaufen",
        ):
            self.assertTrue(matches_any(text, patterns), text)

    def test_captcha_markers_are_manual_triggers(self):
        for text in ("reCAPTCHA", "hCaptcha", "Verify you are human", "Ich bin kein Roboter"):
            self.assertRegex(text, CAPTCHA_PATTERN)

    async def test_network_error_is_never_success(self):
        result = await check_link(_FailingClient(), LinkInfo("https://example.invalid"))
        self.assertEqual("DEFEKT", result.status)

    def test_tracking_links_are_http_only(self):
        links = load_linkliste()
        tracking = [link for link in links if link.typ == "tracking"]
        self.assertEqual(3, len(tracking))
        targets = select_funnel_targets(links, load_config())
        self.assertFalse({l.url for l in tracking} & {l.url for l in targets})
        self.assertEqual(58, len(targets))

    def test_overview_path_rules_include_aok_special_case(self):
        self.assertTrue(is_tariff_page("https://x/anbieter/allianz/tarif/"))
        self.assertTrue(is_tariff_page("https://x/anbieter/aok/aok-hessen/tarif/"))
        self.assertFalse(is_tariff_page("https://x/anbieter/allianz/"))
        self.assertFalse(is_tariff_page("https://x/anbieter/aok/aok-hessen/"))

    def test_reconcile_keeps_one_entry_per_identical_url(self):
        scanned = {
            "https://x/anbieter/a/t1/": LinkInfo("https://target", tarif="T1"),
            "https://x/anbieter/a/t2/": LinkInfo("https://target", tarif="T2"),
        }
        data, _ = reconcile([], scanned)
        self.assertEqual(1, len(data))
        self.assertEqual(2, len(data[0]["tarife"]))


if __name__ == "__main__":
    unittest.main()
