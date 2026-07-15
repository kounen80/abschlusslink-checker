from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

from checker.check_funnel import FunnelRunner
from checker.common import LinkInfo, load_config, prepare_context


class FunnelSafetyIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        await prepare_context(self.context, load_config())
        self.tmp = tempfile.TemporaryDirectory()

    async def asyncTearDown(self):
        await self.context.close()
        await self.browser.close()
        await self.pw.stop()
        self.tmp.cleanup()

    async def test_final_button_is_detected_but_never_clicked(self):
        html = """<html><body><input value='bereit'>
        <button onclick="document.body.innerHTML='VERBOTENER KLICK'">Jetzt abschließen</button>
        </body></html>"""
        config = load_config()
        config["funnel"]["max_steps"] = 1
        runner = FunnelRunner(config, Path(self.tmp.name))
        result = await runner.run(self.context, LinkInfo("data:text/html;charset=utf-8," + quote(html)))
        self.assertEqual("OK", result.status, result.details)
        self.assertEqual("Jetzt abschließen", result.stop_button)
        self.assertTrue(any("NICHT geklickt" in detail for detail in result.details))

    async def test_captcha_stops_before_any_interaction(self):
        html = """<html><body><h1>Verify you are human – reCAPTCHA</h1>
        <button>Weiter</button></body></html>"""
        runner = FunnelRunner(load_config(), Path(self.tmp.name))
        result = await runner.run(self.context, LinkInfo("data:text/html;charset=utf-8," + quote(html)))
        self.assertEqual("MANUELL_PRÜFEN", result.status)
        self.assertEqual(0, result.steps_done)
        self.assertTrue(any("keine weitere Interaktion" in detail for detail in result.details))


if __name__ == "__main__":
    unittest.main()
