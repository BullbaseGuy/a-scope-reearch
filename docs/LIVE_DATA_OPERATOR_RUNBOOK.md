# A-SCOPE live data operator runbook

This runbook is the only manual bridge between the deterministic GitHub Actions software and the first real full-market screening. It keeps large datasets out of normal Git history.

## What is automatic

1. A successful non-PR `A-SCOPE Live Smoke` or `A-SCOPE Weekly Reconciliation` run automatically launches `A-SCOPE Financial Request Manifest`.
2. Publishing a release whose tag starts with `ascope-live-bundle-` automatically launches `A-SCOPE Live Bundle Intake`.
3. A successful bundle intake automatically launches `A-SCOPE Monthly Screening`.
4. Fixture content is rejected at every LIVE boundary.

## What remains manual

- produce full-market annual and quarterly financial CSV files from the financial request batches;
- produce at least 120 trading days of market history for at least 80% of the security master;
- package and publish one validated live bundle release;
- review the monthly shortlist before manually publishing a research release.

## Step 1: download the financial request artifact

Open **Actions → A-SCOPE Financial Request Manifest → latest successful run → Artifacts** and download:

```text
ascope-financial-requests-<run-id>
```

The artifact contains:

```text
financial_request_manifest.csv
financial_request_manifest.json
financial_batches/B001.csv ...
```

For about 6,143 securities and batch size 200, expect approximately 31 batches.

CLI alternative:

```powershell
gh run download <RUN_ID> `
  --repo BullbaseGuy/a-scope-reearch `
  --name ascope-financial-requests-<RUN_ID> `
  --dir D:\ASCOPE\financial_requests
```

## Step 2: run the existing F10 pipeline by batch

For each `financial_batches/Bxxx.csv`, ask the F10 process to export these exact table names somewhere under one common root:

```text
D:\ASCOPE\financial_exports\B001\financial_annual.csv
D:\ASCOPE\financial_exports\B001\financial_quarterly.csv
...
```

Quarterly minimum fields:

```text
security_id,report_period,available_at,revenue,gross_profit,
deducted_net_profit,operating_cash_flow,accounts_receivable,inventory,
contract_liabilities,capex,interest_bearing_debt,total_equity,total_assets,cash
```

Annual minimum fields:

```text
security_id,report_period,available_at,audit_opinion,internal_control_opinion
```

Critical point-in-time rule: a row with `available_at` later than the screening date must remain in the source export if desired, but A-SCOPE will reject a bundle containing such future rows. Build the bundle for a specific as-of date using only information available by that date.

## Step 3: prepare market history

Create:

```text
D:\ASCOPE\market_data.csv
```

Minimum fields:

```text
security_id,trade_date,close,amount_cny
```

Recommended source order:

1. local TDX `vipdoc` files or mootdx;
2. an existing local market database;
3. a bulk source with a persistent local cache;
4. per-security HTTP only for missing gaps.

Coverage gate: at least 120 unique trading days for at least 80% of the security master. Do not generate one-day market snapshots as a substitute.

## Step 4: obtain `security_master.csv`

Download it from the same successful live-smoke artifact used to create the financial request manifest. Do not use a stale or manually edited code list.

Suggested path:

```text
D:\ASCOPE\security_master.csv
```

## Step 5: create the validated release asset locally

Clone the repository and install it once:

```powershell
git clone https://github.com/BullbaseGuy/a-scope-reearch.git D:\ASCOPE\a-scope-reearch
Set-Location D:\ASCOPE\a-scope-reearch
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run the supplied wrapper:

```powershell
.\scripts\windows\prepare_live_bundle.ps1 `
  -SecurityMaster D:\ASCOPE\security_master.csv `
  -FinancialExports D:\ASCOPE\financial_exports `
  -MarketData D:\ASCOPE\market_data.csv `
  -AsOfDate 2026-07-29 `
  -OutputRoot D:\ASCOPE\bundle_output
```

Expected output:

```text
D:\ASCOPE\bundle_output\ascope-live-bundle-2026-07-29.zip
```

The command stops if the bundle fails security-count, orphan-ID, future-availability, market-history or fixture-contamination checks.

## Step 6: publish the input release

Use a distinct input tag namespace:

```powershell
gh release create ascope-live-bundle-2026-07-29 `
  D:\ASCOPE\bundle_output\ascope-live-bundle-2026-07-29.zip `
  --repo BullbaseGuy/a-scope-reearch `
  --title "A-SCOPE live bundle 2026-07-29" `
  --notes "Validated point-in-time input bundle for research screening."
```

Web UI alternative:

1. Repository → Releases → Draft a new release.
2. Tag: `ascope-live-bundle-2026-07-29`.
3. Upload exactly one `ascope-live-bundle-*.zip` asset.
4. Publish the release.

The release publication automatically starts bundle intake and then monthly screening. Do not upload financial or market CSV files directly into normal Git history.

## Step 7: review the automatic monthly screening

Open **Actions → A-SCOPE Monthly Screening → latest successful run** and download:

```text
ascope-monthly-<run-id>
```

Review at least:

```text
run_manifest.json
screening_scores.csv
shortlist.csv
reos_bridge/ascope_to_reos_candidates.csv
```

Confirm:

- `mode = LIVE`;
- `investment_use = RESEARCH_ONLY`;
- no fixture markers;
- ST/*ST is not in the standard executable pool;
- shortlist count is a soft result, not a quota;
- `open_p0_count` and `next_data_request` are populated.

## Step 8: manually publish only after review

After reviewing the monthly artifact, run **A-SCOPE Publish Research Artifact** with:

```text
source_run_id = <monthly screening run ID>
release_tag   = ascope-research-2026-07-29-v1
```

Publishing remains manual by design. A shortlist is a research queue, not a trading instruction.

## Failure recovery

- If financial manifest generation fails, rerun the latest successful Live Smoke; do not repeatedly call per-security discovery APIs.
- If one F10 batch fails, rerun only that batch and keep completed batch outputs.
- If bundle validation fails, read `live_bundle_validation.json`; fix only the failing table or coverage issue.
- If bundle intake fails, replace the release asset by creating a new versioned tag; do not silently mutate an immutable research input.
- If monthly screening fails after intake passed, retain the validated bundle artifact and repair the screening code without recollecting data.
