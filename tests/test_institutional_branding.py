"""Source/asset contract tests for institutional and CB-PFR branding."""
from __future__ import annotations

import base64
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
ASSETS = WEB / "assets"


class InstitutionalBrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.css = (WEB / "styles.css").read_text(encoding="utf-8")
        cls.server = (ROOT / "web_server.py").read_text(encoding="utf-8")

    def test_three_brand_assets_are_present_and_embedded_payloads_are_valid(self):
        for filename in ("cb-pfr-wordmark.svg", "sman1-karawang.svg", "eureka-itb-2026.svg"):
            with self.subTest(filename=filename):
                path = ASSETS / filename
                self.assertTrue(path.is_file(), f"Missing brand asset: {path}")
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                image = root.find("{http://www.w3.org/2000/svg}image")
                self.assertIsNotNone(image)
                href = image.attrib.get("href", "")
                match = re.fullmatch(r"data:image/webp;base64,([A-Za-z0-9+/=]+)", href)
                self.assertIsNotNone(match, f"Unexpected image payload in {filename}")
                payload = base64.b64decode(match.group(1), validate=True)
                self.assertTrue(payload.startswith(b"RIFF") and payload[8:12] == b"WEBP")
                self.assertGreater(len(payload), 1000)

    def test_institutional_logos_are_prominent_above_the_main_workbench(self):
        branding = self.html.index('class="institutional-branding"')
        topbar = self.html.index('<header class="topbar">')
        self.assertLess(branding, topbar)
        self.assertIn('src="/assets/sman1-karawang.svg"', self.html)
        self.assertIn('alt="Logo SMAN 1 Karawang"', self.html)
        self.assertIn('src="/assets/eureka-itb-2026.svg"', self.html)
        self.assertIn('alt="Logo EUREKA!"', self.html)
        self.assertIn("SMAN 1 KARAWANG", self.html)
        self.assertIn("EUREKA! ITB 2026", self.html)

    def test_cbpfr_wordmark_replaces_the_generic_sidebar_mark(self):
        self.assertIn('src="/assets/cb-pfr-wordmark.svg"', self.html)
        self.assertIn('alt="CB-PFR"', self.html)
        self.assertIn('aria-label="CB-PFR Scientific Workstation home"', self.html)
        self.assertNotIn('<span class="brand-mark">C</span>', self.html)

    def test_server_routes_assets_and_mobile_styles_keep_the_branding_visible(self):
        for filename in ("cb-pfr-wordmark.svg", "sman1-karawang.svg", "eureka-itb-2026.svg"):
            route = f'"/assets/{filename}": WEB_ROOT / "assets" / "{filename}"'
            self.assertIn(route, self.server)
        for selector in (".institutional-branding", ".institutional-brand-card", ".institutional-logo", ".brand-wordmark"):
            self.assertIn(selector, self.css)
        self.assertIn("@media(max-width:680px)", self.css)
        self.assertIn("@media(max-width:390px)", self.css)


if __name__ == "__main__":
    unittest.main()
