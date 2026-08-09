#!/usr/bin/env python3
"""Validate a day's research JSON against sources.yaml and render it to HTML.

Usage:
    python3 build_report.py daily_report/reports/2026-08-09.json

Design intent: the research step (research_protocol.md) is where judgment
and search happen; this script is deliberately dumb and mechanical so every
report gets the same structure and the same quality gates, regardless of
what a given morning's research turned up.
"""
import html
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

HERE = Path(__file__).parent
SOURCES_PATH = HERE / "sources.yaml"


def load_sources():
    with open(SOURCES_PATH) as f:
        return yaml.safe_load(f)


def domain_of(url):
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def validate(research, config):
    """Return (warnings, section_status) — never raises on bad data.

    A category with issues is flagged, not dropped or silently padded.
    """
    warnings = []
    section_status = {}
    min_themes = config["checks"]["min_themes_per_category"]
    min_sources = config["checks"]["min_sources_per_theme"]
    min_watchlist_pct = config["checks"].get("min_watchlist_coverage_pct", 0)

    sections_by_cat = {s["category"]: s for s in research.get("sections", [])}

    for cat in config["section_order"]:
        cat_cfg = config["categories"][cat]
        allowed_domains = {s["domain"] for s in cat_cfg["sources"]}
        section = sections_by_cat.get(cat)
        issues = []

        if section is None:
            issues.append("category missing from research.json entirely")
            section_status[cat] = {"status": "missing", "issues": issues}
            warnings.append(f"[{cat}] " + issues[0])
            continue

        themes = section.get("themes", [])
        if len(themes) < min_themes:
            issues.append(
                f"only {len(themes)} theme(s), need >= {min_themes}"
            )

        for i, theme in enumerate(themes):
            srcs = theme.get("sources", [])
            if len(srcs) < min_sources:
                issues.append(
                    f"theme {i+1} ({theme.get('headline','?')!r}) has "
                    f"{len(srcs)} source(s), need >= {min_sources}"
                )
            for src in srcs:
                dom = domain_of(src.get("url", ""))
                if dom not in allowed_domains:
                    issues.append(
                        f"theme {i+1}: source domain {dom!r} not on "
                        f"whitelist for {cat} ({sorted(allowed_domains)})"
                    )
                # Freshness is best-effort: only enforced if 'published'
                # looks like an ISO date; otherwise we flag it rather than
                # guess.
                if not src.get("published"):
                    issues.append(
                        f"theme {i+1}: source missing 'published' date"
                    )

        watchlist = cat_cfg.get("watchlist")
        if watchlist:
            reported = {kl.get("metric") for kl in section.get("key_levels", [])}
            missing = [m for m in watchlist if m not in reported]
            coverage_pct = 100 * (len(watchlist) - len(missing)) / len(watchlist)
            if coverage_pct < min_watchlist_pct:
                issues.append(
                    f"key_levels coverage {coverage_pct:.0f}% of watchlist "
                    f"(< {min_watchlist_pct}%), missing: {missing}"
                )
            for kl in section.get("key_levels", []):
                dom = domain_of(kl.get("source", {}).get("url", ""))
                if dom not in allowed_domains:
                    issues.append(
                        f"key_levels entry {kl.get('metric')!r}: source "
                        f"domain {dom!r} not on whitelist for {cat}"
                    )
                returns = kl.get("returns", {})
                missing_periods = [
                    p for p in ("daily", "wtd", "mtd", "ytd") if not returns.get(p)
                ]
                if missing_periods:
                    issues.append(
                        f"key_levels entry {kl.get('metric')!r}: missing "
                        f"returns for {missing_periods}"
                    )

        status = "ok" if not issues else "degraded"
        section_status[cat] = {"status": status, "issues": issues}
        for issue in issues:
            warnings.append(f"[{cat}] {issue}")

    return warnings, section_status


def render_theme(theme):
    levels_html = ""
    if theme.get("levels"):
        rows = "".join(
            f"<tr><td>{html.escape(l.get('metric',''))}</td>"
            f"<td>{html.escape(l.get('value',''))}</td>"
            f"<td>{html.escape(l.get('change',''))}</td></tr>"
            for l in theme["levels"]
        )
        levels_html = f"""
        <table class="levels">
          <thead><tr><th>Metric</th><th>Level</th><th>Chg</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>"""

    sources_html = " &middot; ".join(
        f'<a href="{html.escape(s.get("url",""))}">{html.escape(s.get("name","source"))}</a>'
        for s in theme.get("sources", [])
    )

    return f"""
    <div class="theme">
      <h3>{html.escape(theme.get('headline',''))}</h3>
      <p>{html.escape(theme.get('summary',''))}</p>
      {levels_html}
      <p class="sources">Sources: {sources_html}</p>
    </div>"""


def render_key_levels(key_levels):
    if not key_levels:
        return ""
    rows = "".join(
        f"<tr><td>{html.escape(kl.get('metric',''))}</td>"
        f"<td>{html.escape(kl.get('value',''))}</td>"
        f"<td>{html.escape(kl.get('returns', {}).get('daily',''))}</td>"
        f"<td>{html.escape(kl.get('returns', {}).get('wtd',''))}</td>"
        f"<td>{html.escape(kl.get('returns', {}).get('mtd',''))}</td>"
        f"<td>{html.escape(kl.get('returns', {}).get('ytd',''))}</td></tr>"
        for kl in key_levels
    )
    return f"""
    <div class="table-scroll">
    <table class="levels key-levels">
      <thead><tr><th>Metric</th><th>Level</th><th>Daily</th><th>WTD</th><th>MTD</th><th>YTD</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def render_section(cat, cat_cfg, section, status):
    label = cat_cfg["label"]
    badge = ""
    if status["status"] != "ok":
        issues_list = "".join(f"<li>{html.escape(i)}</li>" for i in status["issues"])
        badge = f"""
        <div class="degraded-badge">
          &#9888; Degraded coverage
          <ul>{issues_list}</ul>
        </div>"""

    if section is None:
        return f"""
        <section>
          <h2>{html.escape(label)}</h2>
          {badge}
          <p class="empty">No data available for this category today.</p>
        </section>"""

    key_levels_html = render_key_levels(section.get("key_levels", []))
    themes_html = "".join(render_theme(t) for t in section.get("themes", []))
    watch = section.get("watch_today", [])
    watch_html = ""
    if watch:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in watch)
        watch_html = f'<div class="watch"><strong>Watch today:</strong><ul>{items}</ul></div>'

    return f"""
    <section>
      <h2>{html.escape(label)}</h2>
      {badge}
      {key_levels_html}
      {themes_html}
      {watch_html}
    </section>"""


TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Market Report — {date}</title>
<style>
  :root {{
    --bg: #ffffff; --fg: #1a1a1a; --muted: #6b6b6b; --border: #e2e2e2;
    --accent: #0b5cab; --warn-bg: #fff8e6; --warn-border: #e8b93a;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #16181c; --fg: #eaeaea; --muted: #9a9a9a; --border: #2c2f36;
      --accent: #6cb2f4; --warn-bg: #2a2410; --warn-border: #b8922e;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #16181c; --fg: #eaeaea; --muted: #9a9a9a; --border: #2c2f36;
    --accent: #6cb2f4; --warn-bg: #2a2410; --warn-border: #b8922e;
  }}
  body {{ background: var(--bg); color: var(--fg); font-family: Georgia, 'Times New Roman', serif;
          max-width: 760px; margin: 0 auto; padding: 2rem 1.25rem 4rem; line-height: 1.5; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.1rem; }}
  .meta {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 2rem; font-family: -apple-system, sans-serif; }}
  h2 {{ font-size: 1.15rem; border-bottom: 1px solid var(--border); padding-bottom: 0.35rem; margin-top: 2.5rem; }}
  h3 {{ font-size: 1rem; margin-bottom: 0.25rem; }}
  .theme {{ margin: 1.1rem 0; }}
  .theme p {{ margin: 0.35rem 0; }}
  .sources {{ font-size: 0.8rem; color: var(--muted); font-family: -apple-system, sans-serif; }}
  .sources a {{ color: var(--accent); text-decoration: none; }}
  table.levels {{ border-collapse: collapse; font-size: 0.85rem; margin: 0.5rem 0; font-family: -apple-system, sans-serif; }}
  table.levels th, table.levels td {{ border: 1px solid var(--border); padding: 0.25rem 0.6rem; text-align: left; }}
  .table-scroll {{ overflow-x: auto; }}
  .watch {{ margin-top: 0.8rem; font-size: 0.9rem; background: color-mix(in srgb, var(--accent) 8%, transparent);
            border-left: 3px solid var(--accent); padding: 0.5rem 0.8rem; }}
  .degraded-badge {{ background: var(--warn-bg); border: 1px solid var(--warn-border); border-radius: 4px;
                      padding: 0.5rem 0.8rem; font-size: 0.8rem; font-family: -apple-system, sans-serif; margin: 0.5rem 0; }}
  .degraded-badge ul {{ margin: 0.3rem 0 0; padding-left: 1.2rem; }}
  .empty {{ color: var(--muted); font-style: italic; }}
  footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border);
            font-size: 0.75rem; color: var(--muted); font-family: -apple-system, sans-serif; }}
</style>
</head>
<body>
  <h1>Market Report</h1>
  <div class="meta">{date} &middot; generated {generated_at}</div>
  {sections}
  <footer>
    Sources restricted to the whitelist in sources.yaml. Sections marked
    "Degraded coverage" did not fully pass validation — treat with extra
    scrutiny rather than as a clean top-of-day read.
  </footer>
</body>
</html>
"""


def render(research, config, section_status):
    sections = "".join(
        render_section(
            cat,
            config["categories"][cat],
            next((s for s in research["sections"] if s["category"] == cat), None),
            section_status[cat],
        )
        for cat in config["section_order"]
    )
    return TEMPLATE.format(
        date=html.escape(research.get("date", "")),
        generated_at=html.escape(research.get("generated_at", "")),
        sections=sections,
    )


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <research.json>", file=sys.stderr)
        sys.exit(1)

    research_path = Path(sys.argv[1])
    with open(research_path) as f:
        research = json.load(f)

    config = load_sources()
    warnings, section_status = validate(research, config)

    if warnings:
        print("Validation warnings:", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
    else:
        print("Validation passed with no warnings.", file=sys.stderr)

    html_out = render(research, config, section_status)
    out_path = research_path.with_suffix(".html")
    out_path.write_text(html_out)
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
