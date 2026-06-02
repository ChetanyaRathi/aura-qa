"""reporter.py - turn run results into an HTML report and JSON.

The HTML is the "proof the magic worked": counts, a table of every selector the
AI healed (old -> new), and the genuine failures with their errors.
"""

from __future__ import annotations

import json
import os

from .models import RunResult

REPORTS_DIR = os.path.join(os.getcwd(), "reports")

_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>AuraQA report - {suite}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 40px; color: #1a1a1a;
          background: #0e0e12; }}
  h1 {{ color: #f5f5f7; font-weight: 600; }}
  .cards {{ display: flex; gap: 16px; margin: 24px 0; }}
  .card {{ flex: 1; padding: 20px; border-radius: 12px; background: #1a1a22;
           border: 1px solid #2a2a35; }}
  .card .n {{ font-size: 34px; font-weight: 700; }}
  .card .l {{ color: #9a9aa8; font-size: 13px; text-transform: uppercase;
              letter-spacing: .05em; }}
  .pass .n {{ color: #4ade80; }} .heal .n {{ color: #fbbf24; }}
  .fail .n {{ color: #f87171; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px;
           background: #1a1a22; border-radius: 12px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid #2a2a35;
            color: #d4d4dc; font-size: 14px; }}
  th {{ color: #9a9aa8; font-size: 12px; text-transform: uppercase; }}
  code {{ background: #2a2a35; padding: 2px 6px; border-radius: 4px;
          color: #fbbf24; font-size: 12px; }}
  .arrow {{ color: #4ade80; }}
</style></head><body>
<h1>AuraQA report &mdash; {suite}</h1>
<div class="cards">
  <div class="card pass"><div class="n">{passed}</div><div class="l">Passed</div></div>
  <div class="card heal"><div class="n">{healed}</div><div class="l">Healed</div></div>
  <div class="card fail"><div class="n">{failed}</div><div class="l">Failed</div></div>
</div>
<h2 style="color:#f5f5f7;font-weight:500;">Healed selectors</h2>
<table><tr><th>Intent</th><th>Old selector</th><th></th><th>New selector</th></tr>
{healed_rows}
</table>
<h2 style="color:#f5f5f7;font-weight:500;">Failures</h2>
<table><tr><th>Intent</th><th>Action</th><th>Error</th></tr>
{failed_rows}
</table>
</body></html>"""


def build_report(run: RunResult) -> str:
    """Write report.html + report.json into reports/. Returns the html path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    healed_rows = "".join(
        f"<tr><td>{r.intent}</td><td><code>{r.old_selector}</code></td>"
        f"<td class='arrow'>&rarr;</td><td><code>{r.new_selector}</code></td></tr>"
        for r in run.results if r.status == "healed"
    ) or "<tr><td colspan='4' style='color:#6a6a78'>None</td></tr>"

    failed_rows = "".join(
        f"<tr><td>{r.intent}</td><td>{r.action}</td>"
        f"<td style='color:#f87171'>{r.error[:120]}</td></tr>"
        for r in run.results if r.status == "failed"
    ) or "<tr><td colspan='3' style='color:#6a6a78'>None</td></tr>"

    html = _HTML.format(
        suite=run.suite_name, passed=run.passed, healed=run.healed,
        failed=run.failed, healed_rows=healed_rows, failed_rows=failed_rows
    )

    html_path = os.path.join(REPORTS_DIR, "report.html")
    json_path = os.path.join(REPORTS_DIR, "report.json")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(run.to_dict(), f, indent=2)

    return html_path
