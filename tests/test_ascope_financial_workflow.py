from pathlib import Path


def test_financial_workflow_selects_reconciled_master() -> None:
    text = Path('.github/workflows/ascope-financials.yml').read_text(encoding='utf-8')
    assert 'status_reconciliation_manifest.json' in text
    assert 'RECONCILED_ROOT="$(dirname "$STATUS_MANIFEST")"' in text
    assert 'MASTER="$RECONCILED_ROOT/security_master.csv"' in text
    assert "find incoming -name security_master.csv" not in text
    assert "status reconciliation is not PASS" in text
    assert "financial-manifest" in text
