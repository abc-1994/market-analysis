# Daily Market Report

A systematic (not freeform) daily briefing: prior day's top themes across
rates/macro, equities, credit, private equity/credit, and FX/commodities.

## How it stays reliable, not ad hoc

- **`sources.yaml`** — the only sources ever queried. Adding a source is a
  deliberate, visible edit to this file, not an improvisation at research
  time.
- **A fixed JSON schema** (below) — every day's research lands in the same
  shape, whether or not there was much to report.
- **`build_report.py`** — mechanically validates the day's JSON against
  `sources.yaml` before rendering: every cited source's domain must be on
  the whitelist for its category, every theme needs at least one source,
  every category needs at least one theme. Failures don't get silently
  dropped or padded — the rendered report visibly flags the category as
  "degraded coverage" with the specific reason.
- **Fixed template** — section order and layout never change day to day,
  so scanning is fast and any given day's structure is predictable.

## Pipeline

```
research_protocol.md  →  reports/<date>.json  →  build_report.py  →  reports/<date>.html
   (search each          (structured findings,       (validate +
    whitelisted source     matching schema below)      render)
    per category)
```

## `research.json` schema

```jsonc
{
  "date": "2026-08-09",
  "generated_at": "2026-08-09T08:00:00-04:00",
  "sections": [
    {
      "category": "macro_rates",   // must match a key in sources.yaml
      "themes": [
        {
          "headline": "10Y yield rises 8bp on hot CPI print",
          "summary": "Two to four sentences: what happened, why, and the read for a PM.",
          "levels": [
            {"metric": "10Y UST", "value": "4.28%", "change": "+8bp"}
          ],
          "sources": [
            {"name": "Reuters", "url": "https://www.reuters.com/...", "published": "2026-08-08"}
          ]
        }
      ],
      "watch_today": ["8:30am CPI revisions", "3Y note auction"]
    }
    // ... one object per category in sources.yaml's section_order
  ]
}
```

Category keys currently defined: `macro_rates`, `equities`, `credit`,
`private_markets`, `fx_commodities`.

## Running it manually

```bash
python3 daily_report/build_report.py daily_report/reports/2026-08-09.json
```

Prints validation warnings to stderr (if any) and writes
`reports/2026-08-09.html` next to the input file.

See `research_protocol.md` for the step-by-step research process, and
`example_research.json` for a filled-in sample.
