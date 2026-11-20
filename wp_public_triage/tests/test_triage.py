import csv
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import wp_triage as triage


def page(html, status=200, url="https://business.example/"):
    return {"requested_url": url, "final_url": url, "profile": "direct", "fetched_at": "2026-11-20T00:00:00+00:00", "redirects": [], "status": status, "text": html, "content_type": "text/html", "sha256": "fixture", "truncated": False, "compressed": False}


class ClassificationTests(unittest.TestCase):
    def classify(self, html, status=200):
        report, _ = triage.analyze_page(page(html, status))
        return triage.classify([report]), report

    def test_healthy_wordpress(self):
        status, report = self.classify('<meta name="generator" content="WordPress 6.9"><script src="/wp-includes/js/jquery.js"></script><h1>Menuiserie</h1>')
        self.assertEqual(status, "aucun_indice")
        self.assertEqual(len(report["wordpress_signals"]), 2)

    def test_keyword_alone_is_not_priority(self):
        status, report = self.classify('<title>Pharmacie : information Viagra</title><h1>Notice pharmaceutique</h1>')
        self.assertEqual(status, "a_verifier")
        self.assertEqual([o["category"] for o in report["observations"]], ["verification"])

    def test_database_error_is_technical_only(self):
        status, report = self.classify('<h1>Error establishing a database connection</h1>', 500)
        self.assertEqual(status, "incident_technique")
        self.assertEqual({o["category"] for o in report["observations"]}, {"technical"})

    def test_hidden_external_spam_combination(self):
        status, report = self.classify('<h1>Menuiserie</h1><div style="display: none"><a href="https://ads.example/a">casino</a><a href="https://ads.example/b">viagra</a></div>')
        self.assertEqual(status, "a_verifier")
        self.assertEqual(report["observations"][0]["code"], "hidden_external_spam_links")
        self.assertNotIn("text", report)

    def test_hidden_internal_link_not_injection_evidence(self):
        status, _ = self.classify('<nav hidden><a href="/casino">Casino</a><a href="/viagra">Viagra</a></nav>')
        self.assertEqual(status, "aucun_indice")

    def test_remote_wordpress_asset_is_not_local_fingerprint(self):
        _, report = self.classify('<script src="https://other.example/wp-content/a.js"></script>')
        self.assertEqual(report["wordpress_signals"], [])

    def test_defacement_claim_requires_title_or_heading(self):
        self.assertEqual(self.classify('<p>A blog post mentions hacked by somebody.</p>')[0], "aucun_indice")
        self.assertEqual(self.classify('<h1>Hacked by Somebody</h1>')[0], "a_verifier")

    def test_educational_article_and_hidden_menu_are_not_priority(self):
        self.assertEqual(self.classify('<title>Comment supprimer Hacked by sur WordPress</title><p>Guide de réparation.</p>')[0], "a_verifier")
        self.assertEqual(self.classify('<nav hidden><a href="https://casino.example/a">Casino A</a><a href="https://casino.example/b">Casino B</a></nav>')[0], "a_verifier")

    def test_priority_requires_convergence(self):
        html = '<title>Hacked by Somebody</title><div hidden><a href="https://ads.example/a">casino</a><a href="https://ads.example/b">viagra</a></div>'
        self.assertEqual(self.classify(html)[0], "revue_prioritaire")

    def test_actual_challenge_is_inconclusive_but_article_is_not(self):
        self.assertEqual(self.classify('<title>Just a moment...</title><p>Verifying you are human.</p>')[0], "inconclusif")
        self.assertEqual(self.classify('<title>Comment installer un CAPTCHA</title><p>Guide pour votre formulaire.</p>')[0], "aucun_indice")

    def test_challenge_stops_profile_requests(self):
        fake = triage.Fetcher(delay=0)
        with patch.object(fake, "fetch", return_value=page('<title>Just a moment...</title>')) as fetch:
            result = triage.scan_site("https://business.example/", compare_profiles=True, fetcher=fake)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["classification"], "inconclusif")

    def test_profile_redirect_is_not_counted_twice(self):
        baseline = page('<title>Menuiserie</title>')
        mobile = dict(page("", 302), external_redirect="https://ads.example/")
        fake = triage.Fetcher(delay=0)
        with patch.object(fake, "fetch", side_effect=[baseline, mobile, baseline]):
            result = triage.scan_site("https://business.example/", compare_profiles=True, fetcher=fake)
        self.assertEqual(result["classification"], "a_verifier")
        difference = next(o for o in result["pages"][1]["observations"] if o["code"] == "profile_difference")
        self.assertEqual(difference["evidence"]["baseline"]["status"], 200)
        self.assertEqual(difference["evidence"]["observed"]["external_redirect"], "https://ads.example/")

    def test_blocked_or_truncated_is_not_clean(self):
        self.assertEqual(self.classify('<h1>Forbidden</h1>', 403)[0], "inconclusif")
        result = page("<h1>Normal</h1>")
        result["truncated"] = True
        public, _ = triage.analyze_page(result)
        self.assertEqual(triage.classify([public]), "inconclusif")


class TransportTests(unittest.TestCase):
    def test_reject_unsafe_url_shapes(self):
        for url in ("file:///etc/passwd", "https://user:password@example.org", "http://example.org:8080/", "https://example.org/\r\nX-Test:bad", "https://example.org/?action=delete"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                triage.normalize_url(url)

    def test_reject_private_or_mixed_dns(self):
        for ips in (("127.0.0.1",), ("169.254.169.254",), ("10.1.2.3",), ("93.184.216.34", "192.168.1.1"), ("::1",), ("::ffff:127.0.0.1",)):
            records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in ips]
            with self.subTest(ips=ips), patch.object(socket, "getaddrinfo", return_value=records), self.assertRaises(ValueError):
                triage.public_endpoint("https://business.example/")

    def test_tls_connect_uses_pinned_ip_and_original_sni(self):
        connection = triage.PinnedHTTPS("business.example", port=443, timeout=10)
        connection.public_ip = "93.184.216.34"
        with patch.object(socket, "create_connection") as connect, patch.object(connection._context, "wrap_socket") as wrap:
            connection.connect()
            connect.assert_called_once_with(("93.184.216.34", 443), 10)
            wrap.assert_called_once_with(connect.return_value, server_hostname="business.example")

    def test_external_redirect_is_recorded_without_follow(self):
        fetcher = triage.Fetcher(delay=0)
        with patch.object(fetcher, "robots_allowed", return_value=(True, "ok")), patch.object(fetcher, "_single", return_value=dict(page("", 302), location="http://127.0.0.1/admin")) as request:
            result = fetcher.fetch("https://business.example/")
            self.assertEqual(request.call_count, 1)
            self.assertEqual(result["external_redirect"], "http://127.0.0.1/admin")

    def test_alias_redirect_revalidates_destination_ip(self):
        fetcher = triage.Fetcher(delay=0)
        first = dict(page("", 301), location="https://www.business.example/")
        with patch.object(fetcher, "robots_allowed", return_value=(True, "ok")), patch.object(fetcher, "_single", side_effect=[first, ValueError("Adresse réseau non publique bloquée")]) as request:
            result = fetcher.fetch("https://business.example/")
            self.assertEqual(request.call_count, 2)
            self.assertIn("non publique", result["error"])

    def test_robots_disallow_prevents_page_get(self):
        fetcher = triage.Fetcher(delay=0)
        robots = dict(page("User-agent: *\nDisallow: /\n"), content_type="text/plain", location=None)
        with patch.object(fetcher, "_single", return_value=robots) as request:
            result = fetcher.fetch("https://business.example/")
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[0], "https://business.example/robots.txt")
            self.assertIn("interdit", result["error"])

    def test_robots_unavailable_fails_closed(self):
        fetcher = triage.Fetcher(delay=0)
        with patch.object(fetcher, "_single", return_value=dict(page("", 503), location=None)) as request:
            result = fetcher.fetch("https://business.example/")
            self.assertEqual(request.call_count, 1)
            self.assertIn("robots.txt inaccessible", result["error"])

    def test_robots_html_challenge_is_not_empty_allow_rule(self):
        fetcher = triage.Fetcher(delay=0)
        robots = dict(page('<title>Just a moment...</title><p>Verifying your browser</p>'), location=None)
        with patch.object(fetcher, "_single", return_value=robots) as request:
            result = fetcher.fetch("https://business.example/")
            self.assertEqual(request.call_count, 1)
            self.assertIn("HTML/challenge", result["error"])

    def test_missing_robots_allows_only_requested_page(self):
        fetcher = triage.Fetcher(delay=0)
        with patch.object(fetcher, "_single", side_effect=[dict(page("", 404), location=None), dict(page("<h1>Business</h1>"), location=None)]) as request:
            result = fetcher.fetch("https://business.example/")
            self.assertEqual(request.call_count, 2)
            self.assertEqual(result["status"], 200)


class OutputTests(unittest.TestCase):
    def test_csv_formula_neutralization_and_exact_json(self):
        title = '=HYPERLINK("https://example.invalid","click")'
        report, _ = triage.analyze_page(page("<title>" + title + "</title>"))
        result = {"input_url": "https://business.example/", "checked_at": "2026-11-20", "wordpress": {"confidence": "indeterminee"}, "classification": "aucun_indice", "pages": [report], "requests": 2}
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            triage.write_scan([result], folder)
            with (folder / "report.csv").open(encoding="utf-8-sig") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[1][4], "'" + title)
            stored = json.loads((folder / "report.json").read_text())
            self.assertEqual(stored["results"][0]["pages"][0]["title"], title)
        for value in ("=1+1", "+2", "-2", "@SUM(1)", "   =A1", "\t=1", "\n=1"):
            self.assertTrue(triage.safe_cell(value).startswith("'"))

    def test_discovery_keeps_provenance_without_claiming_relationship(self):
        fixture = page('<a href="https://client.example/service">Client</a><a href="https://www.instagram.com/client">Social</a><a href="/portfolio">Internal</a>', url="https://agency.example/work")
        with tempfile.TemporaryDirectory() as temporary, patch.object(triage.Fetcher, "fetch", return_value=fixture):
            count = triage.discover(["https://agency.example/work"], Path(temporary), 50)
            data = json.loads((Path(temporary) / "sources.json").read_text())
            self.assertEqual(count, 1)
            self.assertEqual(data["candidates"][0]["source_pages"], ["https://agency.example/work"])
            self.assertFalse(data["candidates"][0]["relationship_verified"])


if __name__ == "__main__":
    unittest.main()
