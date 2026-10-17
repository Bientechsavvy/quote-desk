# Week 2 "Side Hustle": Project Structure (read this first, then build)

Owner: Bien Bien (Bienvenu Gbeti), Ghana. Challenge: Hacktoberfest Open-Source AI, Week 2 "Side Hustle".
Rule from the challenge: build something with open-weight / open-source AI at its core that someone would actually pay for. Bonus points for a real first user.
Handoff note: any AI agent can continue from this file. Do not restart from scratch.

## 1. The idea (working name: Quote Desk)

A local-first quote and invoice desk for a small trades business (first user: JosphTech, a small electrical services business run by the owner's colleague's friend).

The owner pastes a messy customer request (English or Pidgin). Quote Desk returns:
1. the services it recognised,
2. a priced quote built ONLY from the owner's own price list,
3. a short, polite WhatsApp message to send to the customer,
4. a printable quote page.

Who would pay: a small shop or tradesperson who loses time and money typing quotes by hand and sometimes quotes the wrong price. Realistic price to test with the first user: a small monthly fee or a one-time setup fee (the owner decides; record the user's honest reaction, do not invent numbers).

## 2. Why this is a good fit for the challenge
- Runs on the owner's laptop with no internet (Ollama + a small open-weight model). Customer names, numbers and addresses never leave the machine.
- Costs nothing per quote. A closed API would charge per message and send customer data to a third party.
- Model is swappable with one environment variable (Ollama locally, Backboard hosted model for the public demo).
- Reuses the proven pattern from Week 1 and the Weekend Challenge: RULES DECIDE, MODEL PHRASES, GUARD CHECKS.

## 3. Architecture (same pattern as Plot Buddy, so it is low-risk)
- Rules and math in plain Python: service matching from keywords, line items, quantities, subtotal, total. The model never calculates and never chooses a price.
- Price list is a JSON file the OWNER fills in (`prices.json`). Prices in the repo are clearly marked sample data. If an item has no price, the quote says "price to be confirmed by the owner". No invented prices, ever.
- Model's only job: (a) extract quantity/details from the messy message into a small JSON schema, (b) rewrite the final message politely in English or Pidgin.
- Guard: reject any model text that adds a number, currency amount, or service that is not in the computed quote; or drops the total. On rejection, fall back to the template message from the rules.
- Safety rule carried over from the electrical project: keywords like burnt, smoke, spark, shock, fire flag EMERGENCY and add a "switch off at the main breaker, keep away" line in code, not from the model.
- Backends: `LLM_BACKEND=none | ollama | backboard`. Default local Ollama `qwen2.5:1.5b`. Public demo may use Backboard (only claim it if `/api/status` proves it).
- Stdlib only (http.server, urllib, unittest), same as Plot Buddy. Render web service for the demo.
- Cost protection on any hosted model: cache plus hourly cap, as in Plot Buddy.

## 4. File structure
```
quote-desk/
  README.md
  LICENSE (MIT)
  render.yaml
  .env.example
  .gitignore
  PROJECT_BRIEF.md            (this file, copied in)
  api/
    server.py                 routes: GET /healthz, /api/status, /; POST /api/quote
    quote.py                  matching + line items + totals (pure code)
    guard.py                  checks model text against the computed quote
    llm_ollama.py             local adapter
    llm_backboard.py          hosted adapter (copy the TLS-safe pattern from Plot Buddy)
    data/
      prices.sample.json      SAMPLE prices, marked as sample; owner copies to prices.json
      services.json           service names + keywords + follow-up questions
  web/
    index.html                mobile-first: paste message -> quote card -> WhatsApp / Print
  tests/
    test_quote.py             totals, missing price, emergency flag, Pidgin input
    test_guard.py             rejects invented numbers/prices/services
    results-v1.txt / v2.txt   saved outputs before/after bug fixes (good for the post)
  docs/
    DEV_POST.md
    first-user.md             notes from the first user session
```

## 5. MVP scope (what ships) vs later
Ships this week:
- Paste message, get quote + WhatsApp text, print view.
- Price list in JSON, missing prices handled honestly.
- Local Ollama path works offline; rules-only fallback always works.
- Tests and saved results.
- Live demo on Render, plus a short demo video or screenshots.

Does NOT ship (say so in the post, do not pretend): payments, user accounts, a database, fine-tuning, photo/PDF reading, Tinker usage.

## 6. First-user plan (bonus points)
1. Ask the friend (JosphTech's owner) for his real price list, or at least 5 to 8 real items. Put them ONLY in his private `prices.json`, never in the public repo.
2. Run 5 to 10 of his real past customer messages through the tool. Save the outputs.
3. Ask him: Would you use this? What did it get wrong? Would you pay, and how much? What do you want next?
4. Write his answers honestly in the post under "My First User". If he declines or doesn't try it, remove the section; do not invent a user.
Get his permission before naming him or his business in the post.

## 7. DEV post outline (Week 2 template, tags: devchallenge, hf26challenge, opensource, ai)
- What I Built: who pays and what problem it solves.
- Demo: Render link plus screenshots.
- Code: GitHub embed.
- How I Built It: rules decide / model phrases / guard; Ollama local; optional Backboard; tests that caught bugs.
- Why Does Open Innovation Matter: privacy, zero per-quote cost, swappable model, runs offline; honest limits.
- My Agent Session: DevRelay link (optional).
- My First User: honest notes.
- Prize Categories: Render only if deployed there; Backboard only if proven live; NOT Tinker.

## 8. Day plan (assumes the week ends around Oct 18; cutoff not verified, check the challenge page)
- Oct 13: scaffold, quote.py, services.json, prices.sample.json, tests pass.
- Oct 14: Ollama adapter, guard, UI, saved results-v1, fix bugs, results-v2.
- Oct 15: push to GitHub, deploy on Render, optional Backboard, check `/api/status`.
- Oct 16: first-user session, notes in docs/first-user.md.
- Oct 17: write and publish the post. Oct 18: buffer only.

## 9. Rules for any AI continuing this
- Never invent prices, services, addresses or numbers. Never claim features that were not built or tested.
- Do not store or print the API key. Keys live only in Render environment variables.
- Give the owner explicit step-by-step commands (Windows Git Bash UCRT64, `python` or `py`, `export VAR=...`).
- Do not change the working Plot Buddy or electric-showcase projects.
- Verify the open-weights status and license of any hosted model before naming it as open.

## 10. Status board
- [x] Brief approved by owner
- [x] Scaffold + quote.py + tests (29 tests pass)
- [x] Ollama + Backboard adapters + guard (Ollama and real Backboard NOT yet run by owner)
- [x] UI
- [ ] GitHub + Render
- [ ] First-user session
- [ ] DEV post published
