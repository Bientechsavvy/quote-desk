#!/usr/bin/env python3
"""Quote Desk server: standard library only. Serves web/index.html and POST /api/quote.

LLM_BACKEND = none      rules only (default)
              ollama    local open-weight model through Ollama (offline, private)
              backboard hosted model through Backboard (needs BACKBOARD_API_KEY)
"""
import json, os, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quote, guard  # noqa: E402

INDEX = os.path.join(os.path.dirname(HERE), "web", "index.html")
BACKEND = os.environ.get("LLM_BACKEND", "none").lower()
MAX_CALLS_PER_HOUR = int(os.environ.get("MODEL_MAX_PER_HOUR", "60"))
CACHE_MAX = 200

_LOCK = threading.Lock()
_CALLS = []
_CACHE = {}  # (backend, language, card_text) -> (text, label)


def _allow_call():
    now = time.time()
    with _LOCK:
        while _CALLS and now - _CALLS[0] > 3600:
            _CALLS.pop(0)
        if len(_CALLS) >= MAX_CALLS_PER_HOUR:
            return False
        _CALLS.append(now)
        return True


def _call_model(q):
    if BACKEND == "ollama":
        import llm_ollama
        return llm_ollama.phrase(q), f"open model on this computer ({llm_ollama.MODEL})"
    if BACKEND == "backboard":
        import llm_backboard
        return llm_backboard.phrase(q), f"hosted model via Backboard ({llm_backboard.MODEL})"
    raise RuntimeError("no model backend")


def build_response(req):
    q = quote.build_quote(req.get("message"), req.get("language", "en"))
    q["rules_text"] = q["card_text"]
    q["phrased_by"] = "rules"
    if BACKEND not in ("ollama", "backboard") or not q["lines"]:
        return q
    key = (BACKEND, q["language"], q["card_text"])
    with _LOCK:
        hit = _CACHE.get(key)
    if hit:
        q["card_text"], q["phrased_by"] = hit[0], hit[1] + " (cached)"
        return q
    if BACKEND == "backboard" and not _allow_call():
        q["phrased_by"] = "rules (hourly model limit reached)"
        return q
    try:
        text, label = _call_model(q)
        if guard.check(text, q):
            with _LOCK:
                if len(_CACHE) >= CACHE_MAX:
                    _CACHE.clear()
                _CACHE[key] = (text, label)
            q["card_text"], q["phrased_by"] = text, label
        else:
            q["phrased_by"] = "rules (guard rejected the model text)"
    except Exception as e:  # the app must keep working when the model is down
        print(f"model error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        q["phrased_by"] = f"rules (model unavailable: {type(e).__name__})"
    return q


def status_info():
    """Safe diagnostics: never includes the API key or any price."""
    info = {"backend": BACKEND, "hourly_model_limit": MAX_CALLS_PER_HOUR,
            "prices": "sample" if quote.load_prices().get("sample") else "owner",
            "business": quote.load_prices().get("business", "")}
    if BACKEND == "backboard":
        import llm_backboard
        info.update(provider=llm_backboard.PROVIDER, model=llm_backboard.MODEL,
                    key_set=bool(os.environ.get("BACKBOARD_API_KEY")))
    elif BACKEND == "ollama":
        import llm_ollama
        info.update(model=llm_ollama.MODEL)
    return info


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/api/status":
            return self._send(200, status_info())
        if self.path in ("/", "/index.html"):
            with open(INDEX, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/quote":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > 10000:
            return self._send(413, {"error": "request too large"})
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(req, dict):
                raise ValueError("Send a JSON object.")
            self._send(200, build_response(req))
        except (ValueError, TypeError, AttributeError) as e:
            self._send(400, {"error": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Quote Desk on http://localhost:{port}  (LLM_BACKEND={BACKEND})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
