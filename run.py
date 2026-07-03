#!/usr/bin/env python3
"""Runs the unittest suite and writes report/junit.xml + report/index.html.

Dependency-free: uses only the Python standard library, so the BWI Test
Hub can run it via DIRECT_PROCESS (no pip install, no container).
"""
import os
import sys
import time
import unittest
import xml.sax.saxutils as sax

REPORT_DIR = "report"


def flatten(suite):
    cases = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            cases.extend(flatten(item))
        elif item is not None:
            cases.append(item)
    return cases


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    suite = unittest.TestLoader().discover("tests", pattern="test_*.py")
    cases = flatten(suite)

    result = unittest.TestResult()
    started = time.time()
    unittest.TestSuite(cases).run(result)
    elapsed = time.time() - started

    failures = {}
    for case, tb in result.failures + result.errors:
        failures[case.id()] = tb.strip().splitlines()[-1] if tb.strip() else "failed"

    total = len(cases)
    failed = len(failures)
    passed = total - failed

    # --- JUnit XML ---
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<testsuite name="python-unittest" tests="{total}" '
           f'failures="{failed}" time="{elapsed:.3f}">']
    for case in cases:
        cid = case.id()
        name = cid.split(".")[-1]
        classname = ".".join(cid.split(".")[:-1])
        if cid in failures:
            out.append(f'  <testcase classname="{classname}" name="{name}">')
            out.append(f'    <failure message="{sax.escape(failures[cid])}"/>')
            out.append("  </testcase>")
        else:
            out.append(f'  <testcase classname="{classname}" name="{name}"/>')
    out.append("</testsuite>")
    with open(os.path.join(REPORT_DIR, "junit.xml"), "w") as fh:
        fh.write("\n".join(out))

    # --- HTML ---
    status = "PASSED" if failed == 0 else "FAILED"
    color = "#16a34a" if failed == 0 else "#dc2626"
    rows = ""
    for case in cases:
        cid = case.id()
        ok = cid not in failures
        rows += (f'<tr><td>{sax.escape(cid)}</td>'
                 f'<td class="{"ok" if ok else "no"}">'
                 f'{"passed" if ok else "failed"}</td></tr>\n')
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>python-unittest report</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;background:#0f172a;color:#e2e8f0}}
.badge{{display:inline-block;padding:.2rem .8rem;border-radius:999px;color:#fff;font-weight:700}}
table{{border-collapse:collapse;margin-top:1rem;width:100%}}td,th{{padding:.5rem .8rem;border-bottom:1px solid #334155;text-align:left}}
.ok{{color:#4ade80}}.no{{color:#f87171}}</style></head><body>
<h1>python-unittest</h1>
<p>Status: <span class="badge" style="background:{color}">{status}</span> &middot; {passed}/{total} passed</p>
<table><tr><th>Test</th><th>Result</th></tr>{rows}</table></body></html>"""
    with open(os.path.join(REPORT_DIR, "index.html"), "w") as fh:
        fh.write(html)

    print(f"python-unittest: {passed}/{total} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
