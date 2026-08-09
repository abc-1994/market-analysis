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
      "key_levels": [
        // One entry per instrument in sources.yaml's watchlist for this
        // category, best-effort (coverage is validated, not required 100%).
        // "returns" is Daily/WTD/MTD/YTD change — for yields, express as
        // bp change in the yield level over each period; for
        // indices/FX/commodities, express as % change over each period.
        {"metric": "US 10Y Treasury", "value": "4.28%",
         "returns": {"daily": "+8bp", "wtd": "+11bp", "mtd": "-4bp", "ytd": "+22bp"},
         "source": {"name": "Reuters", "url": "https://www.reuters.com/..."}},
        {"metric": "Germany 10Y Bund", "value": "2.51%",
         "returns": {"daily": "+3bp", "wtd": "+6bp", "mtd": "-9bp", "ytd": "+14bp"},
         "source": {"name": "Reuters", "url": "https://www.reuters.com/..."}}
      ],
      // equities key_levels additionally require "currency" and "hedged"
      // (see sources.yaml's equities.watchlist for the canonical value per
      // instrument — build_report.py rejects a mismatch):
      // {"metric": "MSCI Emerging Markets", "value": "1,142.7", "currency": "USD",
      //  "hedged": false, "returns": {...}, "source": {...}}
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

`key_levels` is the systematic daily levels board (drawn from each
category's `watchlist` in `sources.yaml`) — always attempted regardless of
whether that instrument is part of the day's narrative, and reported as
Daily/WTD/MTD/YTD returns rather than a single day-change. `themes[].levels`
is for numbers specific to a story. Coverage of the watchlist, and
completeness of the four return periods per entry, are both validated
(`checks.min_watchlist_coverage_pct`); thin coverage flags the section as
degraded rather than failing silently.

**Currency and hedging (equities only).** MSCI's global/regional aggregates
(ACWI IMI, World, EM) are canonically USD, unhedged — that's the standard
cross-country comparison series and what's reported unless a specific
hedged mandate calls for otherwise. Single-market indices (STOXX 600, FTSE
100, Nikkei 225, Hang Seng, CSI 300) are reported in local currency, as
conventionally quoted by the exchange/press — they are never silently
converted to USD. Every equities `key_levels` entry must carry `currency`
and `hedged` matching the canonical value defined in `sources.yaml`'s
`equities.watchlist`; a mismatch (e.g. reporting MSCI EM in EUR, or a local
index with `hedged: true`) fails validation rather than rendering
ambiguous, mixed-currency numbers side by side.

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
