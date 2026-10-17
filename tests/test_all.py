import json, os, sys, threading, unittest, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import quote, guard, server  # noqa: E402

PRICES = {"sample": True, "business": "Test Co", "currency": "NGN", "symbol": "N",
          "items": {
              "ats_100a_regular": {"name": "ATS regular", "unit": "each", "price": 100},
              "ats_100a_premium": {"name": "ATS premium", "unit": "each", "price": 200},
              "contactor": {"name": "Contactor", "unit": "each", "price": 10},
              "inspection": {"name": "Inspection", "unit": "visit", "price": 5},
              "rewind_job": {"name": "Rewind", "unit": "job", "price": None},
              "site_survey": {"name": "Survey", "unit": "visit", "price": None},
              "cctv_camera": {"name": "Camera", "unit": "each", "price": 30},
              "switch_socket_point": {"name": "Socket", "unit": "each", "price": 3},
              "wiring_per_bedroom": {"name": "Wiring per bedroom", "unit": "bedroom", "price": 1000}}}


def Q(msg, lang="en"):
    return quote.build_quote(msg, lang, prices=PRICES)


class QuoteTests(unittest.TestCase):
    def test_quantity_and_total(self):
        q = Q("I need 3 contactors")
        self.assertEqual(q["subtotal"], 30)
        self.assertEqual(q["lines"][0]["qty"], 3)

    def test_word_numbers(self):
        self.assertEqual(Q("I want four cameras")["subtotal"], 120)

    def test_missing_price_is_not_invented(self):
        q = Q("my pump coil needs rewinding")
        self.assertEqual(q["unknown"], 1)
        self.assertIn("to be confirmed", q["card_text"])
        self.assertEqual(q["subtotal"], 5)  # only the inspection visit

    def test_range_uses_upper_end_and_says_so(self):
        q = Q("wiring for a 2-3 bedroom flat")
        self.assertEqual(q["subtotal"], 3000)
        self.assertIn("upper end", q["card_text"])

    def test_ats_unspecified_shows_options_not_total(self):
        q = Q("price of ATS 100A?")
        self.assertEqual(q["subtotal"], 0)
        self.assertTrue(q["has_options"])
        self.assertIn("ATS regular", q["card_text"])
        self.assertIn("ATS premium", q["card_text"])

    def test_ats_premium_only(self):
        q = Q("I want a premium ATS")
        self.assertEqual(q["subtotal"], 200)
        self.assertNotIn("ATS regular", q["card_text"])

    def test_ats_both_asked_are_options(self):
        q = Q("how much is the premium ATS and the regular one")
        self.assertEqual(q["subtotal"], 0)
        self.assertTrue(q["has_options"])

    def test_danger_flag_and_safety_line_come_from_code(self):
        q = Q("my socket is sparking and smells burnt")
        self.assertTrue(q["danger"])
        self.assertEqual(q["urgency"], "EMERGENCY")
        self.assertIn("main breaker", q["card_text"])

    def test_pump_burn_does_not_add_wiring_questions(self):
        q = Q("my pump coil don burn", "pidgin")
        self.assertEqual(q["services"], ["Pump or motor rewinding"])

    def test_empty_and_long_messages(self):
        with self.assertRaises(ValueError):
            quote.build_quote("   ")
        with self.assertRaises(ValueError):
            quote.build_quote("x" * 2001)

    def test_greeting_makes_no_quote(self):
        q = Q("hello good morning")
        self.assertEqual(q["lines"], [])
        self.assertEqual(q["subtotal"], 0)

    def test_sample_prices_flagged(self):
        self.assertTrue(quote.load_prices().get("sample"))

    def test_shipped_services_reference_existing_prices(self):
        prices, cfg = quote.load_prices(), quote.load_services()
        for s in cfg["services"]:
            for it in s["items"]:
                self.assertIn(it["price_id"], prices["items"], it["price_id"])


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.q = Q("I need 3 contactors")

    def test_accepts_faithful_rewrite(self):
        t = ("Hi! Thanks for contacting Test Co. Your quote: Contactor, 3 x N10 = N30. "
             "Total for priced items: N30.")
        self.assertTrue(guard.check(t, self.q))

    def test_rejects_changed_number(self):
        self.assertFalse(guard.check("Contactor 3 x N10. Total N25.", self.q))

    def test_rejects_missing_total(self):
        self.assertFalse(guard.check("Hi! We can supply your contactors.", self.q))

    def test_rejects_invented_discount_and_link(self):
        self.assertFalse(guard.check("Total N30 with a discount.", self.q))
        self.assertFalse(guard.check("Total N30. Pay at http://x.example", self.q))

    def test_rejects_new_currency_word(self):
        q = quote.build_quote("I need 3 contactors", "en", prices=dict(PRICES, symbol="N"))
        self.assertFalse(guard.check("Contactors 3 x 10 = 30 dollars. Total 30.", q))

    def test_comma_formatted_numbers_still_match(self):
        q = quote.build_quote("wiring for 2 bedroom", "en", prices=PRICES)
        self.assertTrue(guard.check("Wiring: 2 x N1,000 = N2,000. Total for priced items: N2000.", q))

    def test_requires_confirm_when_unpriced(self):
        q = Q("my pump coil needs rewinding")
        base = q["card_text"]
        self.assertTrue(guard.check(base, q))
        self.assertFalse(guard.check(base.replace("confirm", "ask").replace("confirmed", "asked"), q))

    def test_requires_safety_line_when_danger(self):
        q = Q("socket sparking")
        self.assertFalse(guard.check(q["card_text"].replace("breaker", "box"), q))
        self.assertTrue(guard.check(q["card_text"], q))


class FakeBackboard(BaseHTTPRequestHandler):
    reply = None
    seen = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n))
        FakeBackboard.seen.append((self.path, self.headers.get("X-API-Key"), body))
        out = json.dumps({"status": "COMPLETED", "content": FakeBackboard.reply(body)}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

    def log_message(self, *a):
        pass


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeBackboard)
        threading.Thread(target=cls.fake.serve_forever, daemon=True).start()
        import llm_backboard
        cls.bb = llm_backboard
        cls.bb.BASE = f"http://127.0.0.1:{cls.fake.server_port}"
        os.environ["BACKBOARD_API_KEY"] = "test-key-123"
        server.BACKEND = "backboard"

    @classmethod
    def tearDownClass(cls):
        cls.fake.shutdown(); server.BACKEND = "none"; os.environ.pop("BACKBOARD_API_KEY", None)

    def setUp(self):
        server._CACHE.clear(); server._CALLS.clear(); FakeBackboard.seen.clear()
        server.MAX_CALLS_PER_HOUR = 60

    def test_good_model_text_is_used(self):
        FakeBackboard.reply = lambda body: "Hi! " + body["content"]
        r = server.build_response({"message": "I need 3 contactors"})
        self.assertIn("Backboard", r["phrased_by"])
        path, key, body = FakeBackboard.seen[0]
        self.assertEqual((path, key), ("/threads/messages", "test-key-123"))
        self.assertNotIn("3 contactors", body["content"].replace("3 x", ""))  # raw message not sent
        self.assertEqual(body["content"], r["rules_text"])

    def test_bad_model_text_falls_back_to_rules(self):
        FakeBackboard.reply = lambda body: "Total is 999 with a discount!"
        r = server.build_response({"message": "I need 3 contactors"})
        self.assertIn("guard rejected", r["phrased_by"])
        self.assertEqual(r["card_text"], r["rules_text"])

    def test_cache_avoids_second_call(self):
        FakeBackboard.reply = lambda body: body["content"]
        server.build_response({"message": "I need 3 contactors"})
        r = server.build_response({"message": "I need 3 contactors"})
        self.assertEqual(len(FakeBackboard.seen), 1)
        self.assertIn("cached", r["phrased_by"])

    def test_hourly_cap(self):
        FakeBackboard.reply = lambda body: body["content"]
        server.MAX_CALLS_PER_HOUR = 1
        server.build_response({"message": "I need 3 contactors"})
        r = server.build_response({"message": "I need 4 contactors"})
        self.assertIn("hourly", r["phrased_by"])

    def test_model_down_still_returns_quote(self):
        self.bb.BASE = "http://127.0.0.1:1"
        try:
            r = server.build_response({"message": "I need 3 contactors"})
        finally:
            self.bb.BASE = f"http://127.0.0.1:{self.fake.server_port}"
        self.assertIn("model unavailable", r["phrased_by"])
        self.assertTrue(r["subtotal"] > 0)

    def test_status_never_leaks_key(self):
        self.assertNotIn("test-key-123", json.dumps(server.status_info()))
        self.assertTrue(server.status_info()["key_set"])

    def test_tls_verification_stays_on(self):
        import ssl
        self.assertEqual(self.bb._ssl_context().verify_mode, ssl.CERT_REQUIRED)

    def test_http_endpoint_and_bad_input(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{srv.server_port}"
            server.BACKEND = "none"
            req = urllib.request.Request(base + "/api/quote", json.dumps({"message": "3 cameras"}).encode(),
                                         {"Content-Type": "application/json"})
            data = json.load(urllib.request.urlopen(req))
            self.assertEqual(data["phrased_by"], "rules")
            bad = urllib.request.Request(base + "/api/quote", b'{"message": ""}',
                                         {"Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(bad)
            self.assertEqual(cm.exception.code, 400)
            self.assertEqual(json.load(urllib.request.urlopen(base + "/healthz")), {"ok": True})
            self.assertIn(b"Quote Desk", urllib.request.urlopen(base + "/").read())
        finally:
            server.BACKEND = "backboard"; srv.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=1)
