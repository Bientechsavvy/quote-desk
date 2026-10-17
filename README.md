# Quote Desk

## LIVE URL - https://quote-desk-3lp0.onrender.com


A quote and WhatsApp-reply desk for a small trades business (built first for a small electrical services business).
The owner pastes a messy customer message (English or Pidgin) and gets:

- the services it recognised and the questions to ask the customer (owner view),
- a quote built **only from the owner's own price list**,
- a polite message ready to send on WhatsApp, and a print view.

**Rules decide, the model phrases, a guard checks.** Services, quantities, prices and totals are plain code.
An open-weight model only rewrites the finished text. The guard throws the model's text away if it changes a
number, adds a price, discount, link or service, drops the total or the safety advice. Then the app shows the rules text.
Python standard library only. No packages.

## Features

**Quote engine (plain code, tested)**
- Recognises 9 services from English or Pidgin keywords, reads quantities ("4 cameras", "three contactors") and ranges ("2-3 bedroom", quoted at the upper end and the quote says so).
- Prices come only from the owner's `prices.json`. Unpriced items say "to be confirmed". Alternatives (premium vs regular ATS) show as options and are not added to the total.
- Fire and shock words raise a SAFETY FLAG and add the "switch off at the main breaker" line from code, not from the model.
- Optional `valid_days` and `contact` in `prices.json` appear on the quote.

**AI layer (open-weight, swappable)**
- Local model through Ollama (offline, private) or a hosted model through Backboard. One environment variable.
- A guard rejects model text that changes a number, adds a price, discount, link or service, drops the total, "to be confirmed" or the safety line. The app then shows the rules text. If the model is down, the quote still works.
- Hosted calls are cached and capped per hour. `/api/status` shows the backend and never the key.

**Dashboard**
- Two-panel layout: new quote on the left, owner view and printable quote on the right. Works on a phone, supports dark mode.
- One-tap example messages, Ctrl+Enter to submit.
- Owner view: services, urgency badge, the questions to ask, safety alert.
- Quote document with business name, quote number, date, validity, line items, total and a SAMPLE PRICES notice when sample prices are loaded.
- Send on WhatsApp (optionally to the customer's number), copy text, download .txt, print.
- Optional customer name, added to the greeting in the browser only.
- Recent quotes (last 10) with Export CSV and Clear. Stored only in this browser (localStorage), never on the server.
- Status pills: business, sample or owner prices, rules only or which model.

**Privacy**
- The server keeps no quote history and no customer data. The customer's name and number never leave the browser. The model only sees the finished quote text.
- The owner's real `prices.json` is git-ignored.

## Run it on your computer (Windows Git Bash, Mac or Linux)

```bash
cd quote-desk
python api/server.py            # if 'command not found': py api/server.py  or  python3 api/server.py
                                # then open http://localhost:8000
```

With a local open-weight model (offline, customer data stays on this computer):

```bash
ollama pull qwen2.5:1.5b
export LLM_BACKEND=ollama
python api/server.py
```

With a hosted model through Backboard (what the public demo uses):

```bash
export LLM_BACKEND=backboard
export BACKBOARD_API_KEY="paste-your-key-here"   # never put the key in a file or in git
python tools/check_backboard.py                  # one real test call
python api/server.py
```

Check that it is working: `curl localhost:8000/api/status`

## Use your real prices

1. `cp api/data/prices.sample.json api/data/prices.json`
2. Edit `prices.json`: set `business`, `currency`, `symbol`, `valid_days`, `contact`, and every `price`. Use `null` for anything you price after seeing the job.
3. `prices.json` is in `.gitignore`, so your real prices are never published.
Until you do this the page shows a **sample prices** warning and the quote title says SAMPLE PRICES.

## Re-open the project later

```bash
cd path/to/quote-desk          # the folder that contains api/ and web/
py -m unittest discover -s tests   # 30 tests should pass
py api/server.py               # http://localhost:8000, stop with Ctrl+C
```
Use `python` or `python3` instead of `py` if that is what your machine has.

## Tests

```bash
python -m unittest discover -s tests -v
python tools/run_cases.py        # prints sample customer messages and the quotes
```
`tests/results-v1.txt` is the output before three bugs were fixed, `results-v2.txt` after.

## Deploy on Render

Public Git Repository, Python web service, start command `python api/server.py`, health check `/healthz`.
Environment variables: `LLM_BACKEND=backboard`, `BACKBOARD_API_KEY` (secret), `BACKBOARD_PROVIDER=openrouter`,
`BACKBOARD_MODEL`, `MODEL_MAX_PER_HOUR=60`. See `render.yaml`.
The hosted demo uses sample prices. Only the generated quote text is sent to the hosted model, never the customer's raw message.

## Why open

- Runs on a laptop with no internet (Ollama), so customer names and numbers never leave the owner's computer.
- No per-quote cost on the local path; a hosted API would bill every message.
- The model is one environment variable. Swap it without touching the rules.

## Limits (honest)

- Matching is keyword based. Unusual wording may not match a service. Then no quote is made and the owner is told.
- Prices in this repo are made-up samples. The owner must confirm every real price.
- It does not take payments, keep accounts, read photos or fine-tune a model.
- Small models are weak at Pidgin; the guard and the rules text are the safety net.

MIT license.
