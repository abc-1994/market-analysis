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

3. **Fill the `key_levels` watchlist for the category first**, before
   themes. `sources.yaml` lists the specific instruments each category
   always reports a level for (e.g. macro_rates: US 2Y/10Y/30Y, Bund, Gilt,
   JGB, China 10Y CGB; equities: MSCI ACWI IMI, MSCI World, MSCI EM, S&P
   500, Nasdaq 100, STOXX 600, FTSE 100, Nikkei 225, Hang Seng, CSI 300;
   fx_commodities: DXY, EUR/USD, USD/JPY, GBP/USD, USD/CNY, USD/CHF,
   AUD/USD, gold, WTI, Brent). For each, get the latest level plus **Daily,
   WTD (week-to-date), MTD (month-to-date), and YTD (year-to-date) returns**
   from whitelisted sources — for yields express each period as a bp change
   in the yield level; for indices/FX/commodities express each as a %
   change. Missing entries or periods are fine (coverage is validated, not
   required at 100%) but don't skip the pass — thin coverage gets flagged
   in the report so it's visible, not silent.

   **Equities specifically:** use the `currency` and `hedged` value defined
   for each instrument in `sources.yaml`'s `equities.watchlist` — don't
   pick whatever currency the first source you find happens to quote. MSCI
   ACWI IMI/World/EM are USD, unhedged. STOXX 600/FTSE 100/Nikkei
   225/Hang Seng/CSI 300 are local currency (EUR/GBP/JPY/HKD/CNY
   respectively) with `hedged: null`. Pulling, say, an MSCI EM figure from
   a source quoting local-currency or hedged terms without converting (or
   flagging it) is exactly the kind of silent inconsistency the validator
   is there to catch — don't work around it, get the right series.

   **Every entry also needs `as_of`** — the ISO date (`YYYY-MM-DD`) the
   level itself reflects (typically the prior trading day's close), not
   the date of the article you found it in. This is what lets a stale or
   wrong-day figure be caught mechanically instead of trusted blindly.

   **Every entry also needs a `cross_check`: look the same figure up on a
   second, different whitelisted source** (different domain than the
   primary one) and record what it shows. Don't reuse the same article or
   the same outlet's data desk twice — the build script rejects a
   same-domain "cross-check" as not independent. If the two sources
   disagree beyond tolerance (`cross_check_tolerance_pct`/`_pp` in
   `sources.yaml`), don't just average them or pick one arbitrarily:
   check a third source, check whether one is stale/intraday vs.
   close-of-day, or whether they're quoting a different series (price vs.
   total return, spot vs. futures) — then use the figure you can actually
   justify and, ideally, leave a `"note"` in the theme text if it's a
   theme-relevant discrepancy. A disagreement that goes unresolved will
   render as a visible "degraded coverage" flag, which is the intended
   fallback, not a bug to suppress by fabricating agreement.

4. **Identify the top 2-4 genuinely material themes** per category — not
   every headline. A theme belongs in the report if it plausibly affects
   portfolio positioning (rates moves, spread widening/tightening, major
   index moves and why, PE/PC fundraising or valuation marks, dollar/oil/gold
   moves with a driver attached). Skip noise.

5. **For each theme, capture (matching the JSON schema below):**
   - `headline` — one line, plain statement of what happened
   - `summary` — 2-4 sentences: what happened, why, and the read for a
     portfolio manager
   - `levels` — any concrete numbers (yield, index level, spread, price)
     with the day's change, where available
   - `sources` — every source cited, each as `{name, url, published}`.
     `name` and the URL's domain **must** match an entry in `sources.yaml`
     for that category, or the build script rejects it.

6. **`watch_today`** per category — 1-3 short bullets on what to watch during
   the current session (data releases, auctions, earnings, Fed speakers).

7. **Write the result to `daily_report/reports/<YYYY-MM-DD>.json`** matching
   the schema in `README.md`. Do not hand-write HTML — the build script
   owns formatting.

8. **Run the build/validate step:**
   ```
   python3 daily_report/build_report.py daily_report/reports/<YYYY-MM-DD>.json
   ```
   This checks, per category: at least `min_themes_per_category` themes,
   every source domain on the whitelist, every source within
   `max_source_age_hours`, and `key_levels` watchlist coverage above
   `min_watchlist_coverage_pct`. Categories that fail are rendered with a
   visible "degraded coverage" flag rather than silently dropped or padded
   with stale/off-list content — never invent a theme or a level to fill a
   quota.

9. **Publish** the rendered HTML (`daily_report/reports/<YYYY-MM-DD>.html`)
   as the artifact for the day.
