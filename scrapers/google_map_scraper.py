from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import re

_PHONE_RE = re.compile(r'(\+?\d[\d\-\s\(\)]{6,}\d)')

def extract_number_from_text(text):
    print("Input text:", text)
    if not text:
        print("Number is not found")
        return None
    m = _PHONE_RE.search(text)
    print("Show what the regex match object:", m)
    if m:
        print("Matched group(1):", m.group(1))
        return m.group(1)
    else:
        print("No match found")
        return None