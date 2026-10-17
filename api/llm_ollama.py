"""Local open-weight model through Ollama. Standard library only."""
import json, os, urllib.request

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")


def system_prompt(q):
    lang = "simple Nigerian Pidgin" if q["language"] == "pidgin" else "simple, polite English"
    return (f"Rewrite this customer quote message in {lang}, ready to send on WhatsApp. "
            "Keep EVERY line item, every number and amount exactly as written, the total, and any "
            "'to be confirmed' wording and safety advice. Do NOT add prices, services, discounts, "
            "promises, links or advice. Maximum 180 words. Plain text only, no markdown.")


def phrase(q):
    body = json.dumps({"model": MODEL, "stream": False, "options": {"temperature": 0.2},
                       "messages": [{"role": "system", "content": system_prompt(q)},
                                    {"role": "user", "content": q["card_text"]}]}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)["message"]["content"].strip()
