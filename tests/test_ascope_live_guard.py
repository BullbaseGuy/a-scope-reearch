from pathlib import Path

import pytest

from ascope.fixtures import generate
from ascope.pipeline import run


def test_fixture_cannot_run_as_live(tmp_path: Path):
    generate(tmp_path, count=20)
    with pytest.raises(ValueError, match='fixture contamination'):
        run(tmp_path, tmp_path / 'out', '2026-07-29', mode='live')
