# Decisions

1. Security identity uses CNInfo bulk mappings; Eastmoney clist pagination is not a primary source.
2. Market history prefers local TDX/mootdx and uses per-security HTTP only for gaps.
3. Full historical datasets remain outside Git; Git contains code, schemas, manifests and bounded fixtures.
4. ST/*ST remain in security master but cannot enter the executable pool.
5. Fixture output is always marked `PROHIBITED` and rejected by LIVE mode.
6. Candidate counts are soft targets and never justify lowering thresholds.
7. Automatic trading, agent execution and automatic merge remain disabled.
