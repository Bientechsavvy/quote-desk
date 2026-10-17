---
title: Quote Desk: an open-weight quote and WhatsApp reply desk for small trades businesses
published: false
tags: devchallenge, hf26challenge, opensource, ai
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built
Quote Desk helps a small trades business answer customers faster. The owner pastes a messy customer message (English or Pidgin) and gets a quote built only from his own price list, the questions to ask the customer, and a polite message ready for WhatsApp. It flags fire and shock risks and never invents a price: anything the owner has not priced says "to be confirmed".

Who would pay: small shops and tradespeople who lose time typing quotes by hand and sometimes quote the wrong price. [ADD what your first user said about paying, or delete this sentence.]

## Demo
- Live (sample prices): [ADD RENDER LINK]
- Screenshots: [ADD: the quote, the owner view with the safety flag, /api/status]

## Code
{% embed https://github.com/[YOUR-USERNAME]/[YOUR-REPO] %}

## How I Built It
- **Rules decide, the model phrases.** `quote.py` matches services, reads quantities (including "two", and ranges like "2-3 bedroom"), looks prices up in the owner's `prices.json` and adds up the total. The model never chooses a service, a quantity or a price.
- **Open-weight model for the wording.** Locally, `qwen2.5:1.5b` through Ollama (works offline). On the public demo, a hosted model ([MODEL NAME AND LICENSE: CONFIRM ON ITS MODEL PAGE]) through one Backboard API key. Switching is one environment variable.
- **A guard checks the model.** It rejects text that changes a number, adds a price, discount, link or service, drops the total, forgets "to be confirmed", or drops the breaker safety advice. Then the app shows the rules text.
- **Privacy by design.** The model only sees the finished quote text, never the customer's raw message, name or number.
- Python standard library only, deployed on Render, [N] automated tests.

### What my own tests caught
I ran nine sample customer messages and read the output like a customer. Three bugs: a pump that "burnt" also got house-wiring questions; "2-3 bedroom" was quoted for 3 bedrooms without saying so; and when a customer asked for both the premium and the regular ATS, only one price was shown. I fixed all three, added tests, and kept both outputs in `tests/results-v1.txt` and `results-v2.txt`.

## Why Does Open Innovation Matter?
- Customer names, numbers and addresses can stay on the owner's laptop with a local model. A closed API would receive every message.
- No cost per quote on the local path, so the tool still makes sense for a business that quotes many small jobs.
- I can read and change every part, including the guard that stops a small model from inventing prices, and I can swap the model with one setting.
- Honest limits: matching is keyword based, the demo uses sample prices, Pidgin from a 1.5B model is rough, and I did not build payments, accounts, photo reading or fine-tuning.

## My Agent Session
[Add your DevRelay link, or delete this section.]

## My First User
[Write what really happened using docs/first-user.md. If nobody has tried it yet, delete this whole section.]

## Prize Categories
- Best Use of Render: the demo is hosted on Render. [keep only if true]
- Best Use of Backboard: the live demo calls a hosted model through one Backboard API key. [keep only if /api/status and a screenshot prove it]
