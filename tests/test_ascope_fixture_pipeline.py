import json
from pathlib import Path

from ascope.fixtures import generate
from ascope.pipeline import run
from ascope.qa import validate_output


def test_fixture_pipeline(tmp_path: Path):
    generate(tmp_path, count=120)
    manifest = run(tmp_path, tmp_path, '2026-07-29', mode='fixture')
    assert manifest['status'] == 'PASS_FIXTURE_TEST_ONLY'
    assert manifest['security_count'] == 120
    assert validate_output(tmp_path, 'fixture')['status'] == 'PASS'
    bridge = tmp_path / 'reos_bridge/ascope_to_reos_candidates.csv'
    assert bridge.exists()
    saved = json.loads((tmp_path / 'run_manifest.json').read_text())
    assert saved['investment_use'] == 'PROHIBITED'
