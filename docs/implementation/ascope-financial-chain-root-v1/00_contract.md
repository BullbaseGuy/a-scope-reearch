# Contract: ascope-financial-chain-root-v1

Ensure the automatic financial-request workflow always consumes the reconciled current-status security master from the trusted discovery artifact.

## In scope

- resolve the artifact root through `status_reconciliation_manifest.json`;
- reject missing, failed or undersized status reconciliation;
- reject mismatched identity/status dates;
- prohibit arbitrary first-match selection of nested `security_master.csv` files;
- verify the status-aware artifact is generated after merge.

## Out of scope

- producing the actual F10 financial exports;
- using identity-only or historical status snapshots as current listed data;
- automatic trading, model execution or automatic merge.
