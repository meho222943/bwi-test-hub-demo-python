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
    write_html_report(
        os.path.join(REPORT_DIR, "index.html"),
        project="python-unittest",
        subtitle="Python 3 &middot; unittest &middot; BWI Test Hub demo",
        runtime="python-3 (container)",
        total=total, passed=passed, failed=failed, duration=elapsed,
        rows=[(case.id(), case.id() not in failures, failures.get(case.id(), ""))
              for case in cases],
    )

    print(f"python-unittest: {passed}/{total} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


def write_html_report(path, project, subtitle, runtime, total, passed, failed,
                      duration, rows):
    """Render a polished, self-contained HTML report.

    rows is a list of (name, ok, message) tuples. No external assets, so the
    hub can render it directly in a sandboxed iframe.
    """
    import datetime

    status, scls = ("PASSED", "ok") if failed == 0 else ("FAILED", "no")
    pct = int(passed * 100 / total) if total else 0
    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body_rows = []
    for name, ok, message in rows:
        if ok:
            chip = '<span class="chip ok">&#10003; passed</span>'
        else:
            chip = '<span class="chip no">&#10007; failed</span>'
            if message:
                chip += f'<div class="msg">{sax.escape(message)}</div>'
        body_rows.append(
            f'<tr><td class="name">{sax.escape(name)}</td><td>{chip}</td></tr>')

    html = REPORT_TEMPLATE.format(
        project=project, subtitle=subtitle, runtime=runtime,
        status=status, scls=scls, total=total, passed=passed, failed=failed,
        duration=f"{duration:.2f}", pct=pct, generated=generated,
        rows="".join(body_rows),
    )
    with open(path, "w") as fh:
        fh.write(html)


REPORT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{project} &mdash; Test Report</title>
<style>
:root{{--bg:#0b1120;--panel:#111a2e;--panel2:#0f1728;--border:#1e2a44;--text:#e6ecf7;--muted:#8ea0c0;--ok:#22c55e;--no:#ef4444}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:radial-gradient(1200px 600px at 20% -10%,#16223f 0%,var(--bg) 55%);color:var(--text);padding:2.5rem 1.25rem;min-height:100vh}}
.wrap{{max-width:920px;margin:0 auto}}
.head{{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;justify-content:space-between;margin-bottom:1.75rem}}
.title h1{{margin:0;font-size:1.6rem;letter-spacing:-.02em}}
.title p{{margin:.35rem 0 0;color:var(--muted);font-size:.95rem}}
.pill{{display:inline-flex;align-items:center;gap:.5rem;padding:.5rem 1rem;border-radius:999px;font-weight:700;font-size:.95rem;color:#fff}}
.pill.ok{{background:linear-gradient(135deg,#16a34a,#22c55e);box-shadow:0 6px 20px -6px rgba(34,197,94,.55)}}
.pill.no{{background:linear-gradient(135deg,#dc2626,#ef4444);box-shadow:0 6px 20px -6px rgba(239,68,68,.55)}}
.dot{{width:.6rem;height:.6rem;border-radius:50%;background:#fff}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:.9rem;margin-bottom:1.5rem}}
.card{{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--border);border-radius:14px;padding:1rem 1.1rem}}
.card .k{{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em}}
.card .v{{font-size:1.7rem;font-weight:700;margin-top:.25rem}}
.card.ok .v{{color:var(--ok)}}.card.no .v{{color:var(--no)}}
.bar{{height:.5rem;border-radius:999px;background:#1e2a44;overflow:hidden;margin-bottom:1.75rem}}
.bar>i{{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#4ade80)}}
table{{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--border);border-radius:14px;overflow:hidden}}
th,td{{padding:.8rem 1rem;text-align:left;font-size:.92rem;vertical-align:top}}
thead th{{background:#0e1626;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.06em;font-size:.72rem}}
tbody tr{{border-top:1px solid var(--border)}}
tbody tr:hover{{background:#0e1830}}
td.name{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
.chip{{display:inline-flex;align-items:center;gap:.4rem;padding:.2rem .6rem;border-radius:999px;font-size:.78rem;font-weight:600}}
.chip.ok{{color:#bbf7d0;background:#14351f;border:1px solid #1f5133}}
.chip.no{{color:#fecaca;background:#3a1618;border:1px solid #5b2327}}
.msg{{color:#fca5a5;font-family:ui-monospace,monospace;font-size:.82rem;margin-top:.35rem}}
.foot{{color:var(--muted);font-size:.82rem;margin-top:1.25rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem}}
</style>
</head>
<body>
<div class="wrap">
  <div class="head">
    <div class="title"><h1>{project}</h1><p>{subtitle}</p></div>
    <span class="pill {scls}"><span class="dot"></span>{status}</span>
  </div>
  <div class="cards">
    <div class="card"><div class="k">Total</div><div class="v">{total}</div></div>
    <div class="card ok"><div class="k">Passed</div><div class="v">{passed}</div></div>
    <div class="card no"><div class="k">Failed</div><div class="v">{failed}</div></div>
    <div class="card"><div class="k">Duration</div><div class="v">{duration}s</div></div>
  </div>
  <div class="bar"><i style="width:{pct}%"></i></div>
  <table>
    <thead><tr><th>Test</th><th>Result</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="foot"><span>Runtime: {runtime}</span><span>Generated {generated}</span></div>
</div>
</body>
</html>"""


if __name__ == "__main__":
    main()
