# Decisions

1. The reconciled artifact root is the parent of `status_reconciliation_manifest.json`.
2. The workflow never uses `find ... security_master.csv | head -n1`.
3. Status and discovery dates must match.
4. Status reconciliation must PASS with at least 5,000 listed securities.
5. The generated artifact records its source workflow run and status counts.
