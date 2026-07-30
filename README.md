# A-SCOPE

A-SCOPE is a full-market A-share candidate discovery and evidence-upgrade system for a satellite account. It separates full-market candidate discovery from REOS-S deep research and never treats a shortlist as a trading instruction.

## Core safety boundaries

- Test NAV: CNY 5,000,000.
- ST/*ST stay in security master but are blocked from the executable pool.
- Automatic trading, margin leverage, agent execution and automatic merge are disabled.
- Fixture output is marked `PROHIBITED` and rejected in LIVE mode.
- CNInfo bulk mappings are used for security identity; Eastmoney dynamic pagination is not the primary discovery source.
- Historical market and financial datasets remain outside normal Git history.

## Local deterministic validation

```bash
python -m pip install -e ".[dev]"
python scripts/devflow/run_gate_profile.py repository-full
python -m ascope fixture --output-dir 09_OUTPUTS/fixture
python -m ascope validate-output --output-dir 09_OUTPUTS/fixture --mode fixture
```

## GitHub Actions

- `A-SCOPE Fixture Regression`: deterministic PR regression.
- `A-SCOPE Live Smoke`: two-request bulk provider health and universe completeness.
- `A-SCOPE Weekly Reconciliation`: weekly security identity refresh.
- `A-SCOPE Financial Request Manifest`: creates batched F10 tasks from a validated universe.
- `A-SCOPE Monthly Screening`: requires an explicit validated live bundle artifact.
- `A-SCOPE Publish Research Artifact`: rejects fixture content before release.

See [`docs/USAGE.md`](docs/USAGE.md) and the canonical task state under `docs/implementation/`.
