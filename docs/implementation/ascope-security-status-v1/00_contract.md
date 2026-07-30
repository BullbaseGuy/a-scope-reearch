# Contract: ascope-security-status-v1

Repair the demonstrated mismatch between CNInfo's identity archive and the current listed/tradable security universe.

## In scope

- identity discovery no longer implies `LISTED`;
- low-request current status reconciliation for SSE/SZSE and BSE;
- explicit archive, review, listed and ST partitions;
- financial request batches include only reconciled active non-ST securities;
- live smoke proves current status counts and rejects archive-name false positives.

## Out of scope

- reconstructing historical point-in-time status from a current snapshot;
- deleting archive securities from the master identity history;
- automatic trading or selection from unreconciled securities.
