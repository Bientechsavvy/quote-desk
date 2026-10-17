"""Reject model text that contains facts the rules did not produce."""
import re

LINK = re.compile(r"https?://|www\.", re.I)
# Words a small model likes to invent. Rejected unless the rules text already used them.
INVENTED = ["discount", "warranty", "guarantee", "deposit", "account number", "bank transfer",
            "refund", "%", "for free", "free of charge", "percent", "solar", "cctv", "inverter",
            "generator", "camera", "contactor", "pump", "motor", "wiring"]
CURRENCY = ["naira", "cedi", "usd", "ghs", "ngn", "dollar", "₦", "₵", "$", "£", "€"]


def _norm(text):
    return re.sub(r"(?<=\d),(?=\d{3})", "", text)


def _nums(text):
    return set(re.findall(r"\d+(?:\.\d+)?", _norm(text)))


def check(model_text, q):
    """True only if the model text keeps the quote intact and adds nothing new."""
    t = (model_text or "").strip()
    if not t or len(t) > 1800:
        return False
    if LINK.search(t):
        return False
    low, base = t.lower(), q["card_text"].lower()
    if any(w in low and w not in base for w in INVENTED + CURRENCY):
        return False
    if not _nums(t) <= _nums(q["card_text"]):
        return False
    sub = q.get("subtotal") or 0
    if sub > 0 and (str(int(sub)) if float(sub).is_integer() else f"{sub:.2f}") not in _nums(t):
        return False
    if q.get("unknown") and "confirm" not in low:
        return False
    if q.get("danger") and "breaker" not in low:
        return False
    return True
