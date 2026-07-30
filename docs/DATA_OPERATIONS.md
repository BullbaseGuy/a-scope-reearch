# Data operations

## External request minimization

- Security identity: two bulk CNInfo requests per weekly or stale refresh.
- Announcements: exchange/date range increments, never per-security polling.
- Market history: local TDX or mootdx first; HTTP per security only for gaps.
- Financials: bulk professional-finance or local F10 bundle; official report extraction only for shortlisted cases.

## Canonical data boundary

Git stores schemas, code, small fixtures and manifests. Large point-in-time datasets are supplied as validated workflow artifacts or immutable releases and are never committed to normal Git history.
