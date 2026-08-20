# Deck Cost Calculator — with monthly live lumber pricing

## What updates automatically vs. what doesn't

**Automatic (monthly, free):** pressure-treated and cedar decking prices
scale with the FRED Softwood Lumber Producer Price Index (series WPU0811).
A scheduled job fetches it once a month and the page picks up the change
automatically — no manual work needed once it's set up.

**Manual (no live source exists):** composite/PVC material prices, labor
rates, footing costs, permit fees. Nothing public tracks these as
structured data. Recommend reviewing and updating these numbers directly
in `index.html` every 3-6 months — search "data-low" and "data-high" in
the file to find every price input in one pass.

## One-time setup

1. **Get a free FRED API key**
   Go to https://fred.stlouisfed.org/docs/api/api_key.html, sign up, copy
   your key. No cost, no card required.

2. **Push this folder to a GitHub repository**
   (public or private both work — GitHub Actions is free either way for
   this light a workload)

3. **Add your FRED key as a repo secret**
   In your GitHub repo: Settings → Secrets and variables → Actions →
   "New repository secret". Name it `FRED_API_KEY`, paste your key, save.

4. **Run the pricing job once manually to establish a baseline**
   Go to the "Actions" tab in your repo → "Update lumber pricing" →
   "Run workflow". This creates `pricing.json` for the first time —
   whatever the lumber index is at that moment becomes your fixed
   reference point, and every future month is compared against it.

5. **Deploy the site**
   If using GitHub Pages: Settings → Pages → set source to your main
   branch. Your `pricing.json` file lives in the same folder as
   `index.html`, so the page's fetch('./pricing.json') call finds it
   automatically — no config needed.

## How the monthly update works, unattended

`.github/workflows/update-pricing.yml` runs automatically on the 2nd of
every month (FRED usually posts new monthly data a day or two into the
month, so the 2nd avoids grabbing a stale read on the 1st). It:

1. Fetches the latest WPU0811 value from FRED
2. Compares it to your fixed baseline (set in step 4 above)
3. Writes the resulting multiplier to `pricing.json`
4. Commits that file back to your repo automatically

Nothing needs to run on your own computer — this all happens on GitHub's
servers on their schedule, whether your PC is on or not.

## Checking it's working

Visit your live site and look at the bottom footer line — it'll say
either "Lumber pricing: using baseline estimates" (before the first run)
or something like "Lumber pricing updated 2026-08-01 · +3.2% vs.
baseline (source: FRED WPU0811)" once the monthly job has run at least
once.
