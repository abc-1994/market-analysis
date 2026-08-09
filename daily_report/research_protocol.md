# Daily Research Protocol

Followed every morning (by the Routine that fires this workflow) to turn
yesterday's market activity into the structured `research.json` file that
`build_report.py` validates and renders. The point of this protocol is that
the research step is systematic and repeatable — not a fresh freeform search
each day.

## Steps

1. **Load `sources.yaml`.** This is the only allowed source list. Do not
   substitute or add ad hoc sources during research — if a needed source is
   missing, add it to `sources.yaml` first (a deliberate, visible change),
   then re-run.

2. **For each category in `section_order`**, query each of that category's
   sources with a site-scoped search for the prior trading day, e.g.:
   - `site:reuters.com <category topic> <today's date>`
   - `site:federalreserve.gov FOMC OR speech <date range>`

   Only use results actually published within `max_source_age_hours` (see
   `sources.yaml`) of the report's run time. Discard anything older or
   undated.

3. **Identify the top 2-4 genuinely material themes** per category — not
   every headline. A theme belongs in the report if it plausibly affects
   portfolio positioning (rates moves, spread widening/tightening, major
   index moves and why, PE/PC fundraising or valuation marks, dollar/oil/gold
   moves with a driver attached). Skip noise.

4. **For each theme, capture (matching the JSON schema below):**
   - `headline` — one line, plain statement of what happened
   - `summary` — 2-4 sentences: what happened, why, and the read for a
     portfolio manager
   - `levels` — any concrete numbers (yield, index level, spread, price)
     with the day's change, where available
   - `sources` — every source cited, each as `{name, url, published}`.
     `name` and the URL's domain **must** match an entry in `sources.yaml`
     for that category, or the build script rejects it.

5. **`watch_today`** per category — 1-3 short bullets on what to watch during
   the current session (data releases, auctions, earnings, Fed speakers).

6. **Write the result to `daily_report/reports/<YYYY-MM-DD>.json`** matching
   the schema in `README.md`. Do not hand-write HTML — the build script
   owns formatting.

7. **Run the build/validate step:**
   ```
   python3 daily_report/build_report.py daily_report/reports/<YYYY-MM-DD>.json
   ```
   This checks, per category: at least `min_themes_per_category` themes,
   every source domain on the whitelist, every source within
   `max_source_age_hours`. Categories that fail are rendered with a visible
   "degraded coverage" flag rather than silently dropped or padded with
   stale/off-list content — never invent a theme to fill a quota.

8. **Publish** the rendered HTML (`daily_report/reports/<YYYY-MM-DD>.html`)
   as the artifact for the day.
