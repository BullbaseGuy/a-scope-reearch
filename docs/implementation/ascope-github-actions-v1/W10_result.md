# W10 result

PASS for the deterministic software and provider-smoke scope.

## Verified GitHub Actions runs

| Gate | Run ID | Result |
|---|---:|---|
| Test / repository-full | 30512650839 | PASS |
| Devflow State Consistency | 30512650831 | PASS |
| Devflow Upgrade Compatibility | 30512650840 | PASS |
| A-SCOPE Fixture Regression | 30512650794 | PASS |
| Devflow Secret Audit | 30512650834 | PASS |
| A-SCOPE Live Smoke | 30512650859 | PASS |

## Fixture regression

- securities: 120;
- hard-gate eligible: 115;
- research shortlist: 59;
- mode: `FIXTURE_TEST_ONLY`;
- investment use: `PROHIBITED`;
- LIVE contamination guard: enabled and tested.

The fixture result demonstrates deterministic operation only and is not an A-share recommendation or historical performance result.

## Live bulk discovery smoke

The provider smoke completed using the bounded CNInfo bulk design rather than Eastmoney dynamic pagination:

- security count: 6,143;
- SSE: 2,465;
- SZSE: 3,091;
- BSE: 587;
- SSE Main: 1,847;
- STAR: 618;
- SZSE Main: 1,647;
- ChiNext: 1,444;
- BSE: 587;
- completeness validation: PASS;
- expected network requests: two bulk mappings.

No market prices, financial histories or real candidates were fabricated by the discovery smoke.

## Security and control-plane results

- secret audit: PASS;
- workflow validator: zero automatic model paths and zero automatic paid-probe retries;
- agent/model execution: disabled;
- automatic merge: disabled;
- automatic trading and margin leverage: disabled;
- ST/*ST remain in security master and are blocked by the executable hard gate;
- external requests use bulk/incremental/provider-fallback policy.

## Remaining non-blocking data operation

Real monthly screening remains intentionally blocked until a validated point-in-time bundle supplies:

- `security_master.csv`;
- `market_data.csv` with sufficient history;
- `financial_quarterly.csv`;
- `financial_annual.csv`.

This is recorded as MA-002 and does not invalidate completion of the deterministic software system.
