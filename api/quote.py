"""Quote engine: plain code, no model. Standard library only.

The model is never asked to choose a service, a quantity or a price.
Everything a customer reads about money comes from prices.json (owner's list) through this file.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_WORD_RE = re.compile(r"\b(" + "|".join(WORDS) + r")\b")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_services(path=None):
    return _load(path or os.path.join(DATA, "services.json"))


def load_prices(path=None):
    """Owner's prices.json if present (or PRICES_FILE), otherwise the sample file."""
    path = path or os.environ.get("PRICES_FILE") or os.path.join(DATA, "prices.json")
    if not os.path.exists(path):
        path = os.path.join(DATA, "prices.sample.json")
    prices = _load(path)
    prices.setdefault("sample", False)
    return prices


def money(prices, amount):
    s = prices.get("symbol") or prices.get("currency", "")
    if float(amount).is_integer():
        return f"{s}{int(amount):,}"
    return f"{s}{amount:,.2f}"


def _has(patterns, text):
    return any(re.search(p, text) for p in patterns)


def _digits(text):
    return _WORD_RE.sub(lambda m: str(WORDS[m.group(1)]), text)


def _quantity(pattern, text):
    """Return (qty, was_range). Missing quantity defaults to 1."""
    if not pattern:
        return 1, False
    m = re.search(pattern, text)
    if not m:
        return 1, False
    nums = [int(g) for g in m.groups() if g and g.isdigit()]
    if not nums:
        return 1, False
    qty = max(nums)
    if qty < 1 or qty > 200:
        return 1, False
    return qty, len(nums) > 1


def find_services(message, services=None):
    cfg = services or load_services()
    low = message.lower()
    found = [s for s in cfg["services"] if _has(s["keywords"], low)]
    ids = {s["id"] for s in found}
    for rule in cfg.get("remove_when_present", []):
        if rule["keep"] in ids and rule["drop"] in ids:
            found = [s for s in found if s["id"] != rule["drop"]]
            ids.discard(rule["drop"])
    return found[: cfg.get("max_services", 3)]


def _line(prices, price_id, fallback_name, qty, note="", option=False):
    item = prices["items"].get(price_id)
    if item is None:
        return {"price_id": price_id, "name": fallback_name, "qty": qty, "unit_price": None,
                "total": None, "option": option, "note": note}
    unit_price = item.get("price")
    total = unit_price * qty if isinstance(unit_price, (int, float)) else None
    return {"price_id": price_id, "name": item["name"], "qty": qty, "unit_price": unit_price,
            "total": total, "option": option, "note": note}


def build_lines(message, found, prices):
    text = _digits(message.lower())
    lines, notes, seen = [], [], set()
    for svc in found:
        groups = {}
        for it in svc["items"]:
            if it.get("group"):
                groups.setdefault(it["group"], []).append(it)
                continue
            if it["price_id"] in seen:  # e.g. one inspection visit covers two services
                continue
            seen.add(it["price_id"])
            qty, ranged = _quantity(it.get("qty"), text)
            note = ""
            if ranged:
                note = f"quoted for {qty} (upper end of the range you gave)"
                notes.append(note)
            lines.append(_line(prices, it["price_id"], svc["name"], qty, note))
        for members in groups.values():
            chosen = [it for it in members if it.get("when") and re.search(it["when"], text)]
            if len(chosen) == 1:
                qty, _ = _quantity(chosen[0].get("qty"), text)
                lines.append(_line(prices, chosen[0]["price_id"], svc["name"], qty))
            else:  # nothing matched, or the customer asked about several: show them, don't total them
                for it in (chosen or members):
                    lines.append(_line(prices, it["price_id"], svc["name"], 1, option=True))
    return lines, notes


def _fmt_line(prices, ln):
    if ln["total"] is None:
        price = "price to be confirmed by the owner"
    elif ln["qty"] > 1:
        price = f"{ln['qty']} x {money(prices, ln['unit_price'])} = {money(prices, ln['total'])}"
    else:
        price = money(prices, ln["total"])
    if ln["option"]:
        return f"- Option: {ln['name']}: {price}"
    return f"- {ln['name']}: {price}"


def compose_text(prices, business, language, lines, subtotal, unknown, has_options,
                 questions, danger, safety_line, notes=()):
    pidgin = language == "pidgin"
    if not lines:
        return ("Hello, thank you for contacting " + business + ". Abeg tell us wetin you need "
                "make we help you." if pidgin else
                "Hello, thank you for contacting " + business +
                ". Please tell us what you need so we can prepare a quote.")
    out = [("Hello, thank you say you contact " + business + ". Dis na your quote:") if pidgin else
           ("Hello, thank you for contacting " + business + ". Here is your quote:")]
    out += [_fmt_line(prices, ln) for ln in lines]
    if subtotal > 0:
        out.append(("Total for priced items: " if not pidgin else "Total for di priced things: ")
                   + money(prices, subtotal))
    out += [f"Note: {n}." for n in notes]
    if has_options:
        out.append("Pick one option and we will confirm." if not pidgin
                   else "Pick one option make we confirm.")
    if unknown:
        out.append("Items marked 'to be confirmed' will be priced by the owner after seeing the job."
                   if not pidgin else
                   "Di items wey say 'to be confirmed', di owner go confirm di price after e see di job.")
    if questions:
        out.append(("To help you faster, please tell us: " if not pidgin else
                    "To help you quick, abeg tell us: ")
                   + " ".join(f"({i}) {q}" for i, q in enumerate(questions, 1)))
    if danger:
        out.append(safety_line)
    return "\n".join(out)


SAFETY = ("If it is safe to do so, please switch off at the main breaker and keep away "
          "from the area until we reach you.")


def build_quote(message, language="en", prices=None, services=None):
    message = (message or "").strip()
    if not message:
        raise ValueError("Paste the customer's message.")
    if len(message) > 2000:
        raise ValueError("Message is too long (max 2000 characters).")
    language = "pidgin" if language == "pidgin" else "en"
    prices, cfg = prices or load_prices(), services or load_services()
    found = find_services(message, cfg)
    lines, notes = build_lines(message, found, prices)
    low = message.lower()
    danger = _has(cfg["danger_keywords"], low)
    urgency = "EMERGENCY" if danger else "URGENT" if _has(cfg["urgent_keywords"], low) else "NORMAL"
    questions = []
    for s in found:
        questions += [q for q in s["questions"] if q not in questions]
    questions = questions[:4]
    counted = [ln for ln in lines if not ln["option"]]
    subtotal = sum(ln["total"] for ln in counted if ln["total"] is not None)
    unknown = sum(1 for ln in counted if ln["total"] is None)
    has_options = any(ln["option"] for ln in lines)
    business = prices.get("business") or "our team"
    text = compose_text(prices, business, language, lines, subtotal, unknown,
                        has_options, questions, danger, SAFETY, notes)
    return {
        "card_text": text, "language": language, "services": [s["name"] for s in found],
        "lines": lines, "notes": notes, "subtotal": subtotal, "unknown": unknown,
        "has_options": has_options, "currency": prices.get("currency", ""),
        "symbol": prices.get("symbol", ""), "danger": danger, "urgency": urgency,
        "questions": questions, "sample_prices": bool(prices.get("sample")),
        "business": business, "valid_days": prices.get("valid_days"),
        "contact": prices.get("contact", ""),
    }
