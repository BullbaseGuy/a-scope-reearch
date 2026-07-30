# Decisions

1. CNInfo is an identity and disclosure mapping source, not a current listing-status authority.
2. Unmatched securities remain `REVIEW`; they are never promoted to `LISTED` by absence of evidence.
3. BaoStock current basics provides SSE/SZSE listed/delisted status in one authenticated session.
4. BSE uses a code-sorted bounded current-market fallback with at most ten pages and no full-market dynamic ranking.
5. ST/*ST remains listed in the master but is separated from standard financial requests.
6. Current status snapshots are prohibited for historical point-in-time backtests.
