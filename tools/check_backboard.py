#!/usr/bin/env python3
"""One real test call to Backboard. Run from the quote-desk folder:
    export BACKBOARD_API_KEY="your-new-key"
    python tools/check_backboard.py
Prints the rules text, the model reply and whether the guard accepts it."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import quote, guard, llm_backboard

q = quote.build_quote("I need wiring for a 2 bedroom flat and 4 CCTV cameras", "en")
print("RULES TEXT:\n" + q["card_text"] + "\n")
try:
    out = llm_backboard.phrase(q)
except Exception as e:
    sys.exit(f"Backboard call failed: {type(e).__name__}: {e}")
print(f"MODEL REPLY ({llm_backboard.MODEL}):\n{out}\n")
print("GUARD:", "accepted" if guard.check(out, q) else "REJECTED (app would show the rules text)")
