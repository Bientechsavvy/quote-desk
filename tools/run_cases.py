#!/usr/bin/env python3
"""Run sample customer messages through the quote engine (no model) and print the results.
Save the output with:  python tools/run_cases.py > tests/results-vN.txt"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import quote

CASES = [
    ("Pls my building get damage, I need to replace the wiring, light just burnt", "en"),
    ("my pump coil don burn, abeg how much to rewind am", "pidgin"),
    ("The switch in my parlour no dey work, and two sockets dey spark", "en"),
    ("I need wiring for a 2-3 bedroom flat", "en"),
    ("I want solar and 4 CCTV cameras for my shop", "en"),
    ("urgent! my pressing iron and grinding machine stopped working", "en"),
    ("How much is an ATS 100A premium and the regular one?", "en"),
    ("I need 3 contactors and a relay, what is the price", "en"),
    ("hello good morning", "en"),
]
for msg, lang in CASES:
    q = quote.build_quote(msg, lang)
    print(f"MESSAGE ({lang}): {msg}")
    print(f"SERVICES: {', '.join(q['services']) or '-'} | URGENCY: {q['urgency']} | "
          f"SUBTOTAL: {q['subtotal']} | UNPRICED: {q['unknown']}")
    print(q["card_text"])
    print("-" * 60)
