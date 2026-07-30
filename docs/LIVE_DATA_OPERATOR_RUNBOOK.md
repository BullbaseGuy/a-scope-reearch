# A-SCOPE live data operator runbook

This runbook is the manual bridge between the deterministic GitHub Actions software and the first real full-market screening. Large market and financial datasets stay outside normal Git history.

The operational checklist is also tracked in issue `#9`.

## Current verified universe boundary

The latest reconciled current-status smoke produced:

- CNInfo identity rows: 6,143;
- current listed rows: 5,538;
- current listed non-ST standard path: 5,329;
- listed ST/*ST high-risk path: 209;
- delisted/archive rows: 339;
- unresolved REVIEW rows: 266;
- standard financial batches at size 200: approximately 27.

Always trust the actual `financial_request_manifest.json` from the latest successful run instead of a hard-coded count.

## What is automatic

1. A successful non-PR `A-SCOPE Live Smoke` or `A-SCOPE Weekly Reconciliation` run automatically launches `A-SCOPE Financial Request Manifest`.
2. Publishing a release whose tag starts with `ascope-live-bundle-` automatically launches `A-SCOPE Live Bundle Intake`.
3. A successful bundle intake automatically launches `A-SCOPE Monthly Screening`.
4. Fixture content is rejected at every LIVE boundary.
5. The financial workflow derives its input root from `status_reconciliation_manifest.json`; it does not use the nested identity-only security master.

## What remains manual

- produce annual and quarterly financial CSV files from the generated F10 batches;
- produce at least 120 trading days of market history for at least 80% of the reconciled security master;
- package and publish one validated input bundle release;
- review monthly output before manually publishing a research release.

## Step 1 — Download the status-aware financial request artifact

Open **Actions → A-SCOPE Financial Request Manifest → latest successful run → Artifacts** and download:

```text
ascope-financial-requests-<run-id>
```

Confirm the artifact contains:

```text
financial_request_manifest.csv
financial_request_manifest.json
source_selection.json
high_risk_st_manifest.csv
archive_or_review_manifest.csv
financial_batches/B001.csv ...
```

`source_selection.json` must state that selection came from the status-reconciliation manifest parent. The standard request count should be close to 5,329 and the batch count close to 27, subject to the latest status snapshot.

CLI alternative:

```powershell
gh run download <RUN_ID> `
  --repo BullbaseGuy/a-scope-reearch `
  --name ascope-financial-requests-<RUN_ID> `
  --dir D:\ASCOPE\financial_requests
```

## Step 2 — Run the existing F10 process by batch

For each `financial_batches\Bxxx.csv`, write these exact table names below one common root:

```text
D:\ASCOPE\financial_exports\B001\financial_annual.csv
D:\ASCOPE\financial_exports\B001\financial_quarterly.csv
...
```

Preserve completed batches and rerun only failed batches.

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

Point-in-time rule: rows used in a bundle must have `available_at <= as_of_date`. Do not relabel the report period as the availability date.

## Step 3 — Prepare market history

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

Coverage gate:

- at least 120 unique trading days;
- at least 80% of the reconciled security master reaches that depth;
- no future trade date beyond the bundle `as_of_date`;
- no one-day snapshot substituted for history.

## Step 4 — Obtain the matching reconciled security master

Download `security_master.csv` from the same successful Live Smoke or Weekly artifact that produced the financial request manifest.

Confirm it includes:

```text
status,status_reason,is_st,status_as_of_date,status_snapshot_type
```

Do not use the nested `identity/security_master.csv`; that file is an archive/identity map and intentionally uses conservative `REVIEW` status.

Suggested path:

```text
D:\ASCOPE\security_master.csv
```

## Step 5 — Build and validate the immutable live bundle

Clone or update the repository and install it:

```powershell
git clone https://github.com/BullbaseGuy/a-scope-reearch.git D:\ASCOPE\a-scope-reearch
Set-Location D:\ASCOPE\a-scope-reearch
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run:

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

The command stops on insufficient security coverage, orphan IDs, future availability, insufficient market history or fixture contamination. Read `live_bundle_validation.json` and fix the specific failing input rather than lowering thresholds blindly.

## Step 6 — Publish the validated input release

```powershell
gh release create ascope-live-bundle-2026-07-29 `
  D:\ASCOPE\bundle_output\ascope-live-bundle-2026-07-29.zip `
  --repo BullbaseGuy/a-scope-reearch `
  --title "A-SCOPE live bundle 2026-07-29" `
  --notes "Validated point-in-time input bundle for research screening."
```

Web alternative:

1. Repository → Releases → Draft a new release.
2. Use tag `ascope-live-bundle-2026-07-29`.
3. Upload exactly one `ascope-live-bundle-*.zip` asset.
4. Publish.

Release publication automatically starts bundle intake and monthly screening. Corrected inputs must use a new versioned tag; do not silently mutate an immutable input release.

## Step 7 — Review the automatic monthly screening

Open **Actions → A-SCOPE Monthly Screening → latest successful run** and download:

```text
ascope-monthly-<run-id>
```

Review:

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
- ST/*ST is absent from the standard executable pool;
- archive and REVIEW securities are absent from standard requests and shortlist;
- shortlist count is treated as a soft outcome, not a quota;
- `open_p0_count` and `next_data_request` are populated.

## Step 8 — Publish only after human review

Run **A-SCOPE Publish Research Artifact** manually with:

```text
source_run_id = <monthly screening run ID>
release_tag   = ascope-research-2026-07-29-v1
```

Publication remains manual by design. A shortlist is a research queue, not a trading instruction; selected names must still pass REOS-S evidence, valuation, premortem and position-budget gates.

## Failure recovery

- Financial manifest failure: rerun the latest successful Live Smoke; do not recollect per-security identity data.
- One F10 batch failure: rerun only that batch and retain completed batch outputs.
- Market gap: fill only missing securities or dates from a fallback source.
- Bundle validation failure: fix the reported table or coverage problem.
- Intake failure: publish a corrected versioned input release.
- Monthly failure after intake PASS: retain the validated bundle and repair screening code without recollecting data.
