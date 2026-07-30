from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".")
TASK_ID = "devflow-bootstrap"
BRANCH = "feature/devflow-bootstrap"
BASE_SHA = "ca8032c5d232dad7ee1293c0872c7b5d1e26246c"
ACTOR = "tyxq" + "428"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


write(
    ROOT / "README.md",
    """# A-SCOPE

A-SCOPE is a full-market A-share candidate discovery and evidence-upgrade system for a satellite investment account.

The repository reuses the reviewed `BullbaseGuy/demo-project` control plane. Canonical task state lives under `docs/implementation/`; GitHub Actions performs deterministic gates; model/agent execution and automatic merge remain disabled.

## Start here

- [`docs/USAGE.md`](docs/USAGE.md)
- [`docs/process/README.md`](docs/process/README.md)
- [`docs/implementation/ACTIVE_TASKS.yaml`](docs/implementation/ACTIVE_TASKS.yaml)

Product implementation begins in a separate governed task after this bootstrap PR is merged.
""",
)

pyproject_path = ROOT / "pyproject.toml"
pyproject = pyproject_path.read_text(encoding="utf-8")
pyproject = pyproject.replace(
    'name = "generic-devflow-scaffold"',
    'name = "a-scope-reearch"',
)
pyproject = pyproject.replace(
    'description = "Repository-neutral ChatGPT Web and GitHub Actions execution scaffold"',
    'description = "A-SCOPE full-market A-share candidate discovery system"',
)
pyproject = pyproject.replace('requires-python = ">=3.11"', 'requires-python = ">=3.12"')
pyproject = pyproject.replace('target-version = "py311"', 'target-version = "py312"')
pyproject_path.write_text(pyproject, encoding="utf-8")

project_path = ROOT / ".devflow/project.json"
project = json.loads(project_path.read_text(encoding="utf-8"))
project["project"].update(
    {
        "default_branch": "main",
        "allowed_actors": [ACTOR],
        "notification_mentions": [ACTOR],
        "python_version": "3.12",
    }
)
project["features"].update(
    {
        "automatic_merge": False,
        "agent_execution": "disabled",
        "relay_paid_probe": False,
        "branch_gc_execute": False,
    }
)
project_path.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")

task_dir = ROOT / "docs/implementation" / TASK_ID
task_dir.mkdir(parents=True, exist_ok=True)

active = {
    "schema_version": 1,
    "tasks": [
        {
            "task_id": TASK_ID,
            "title": "Bootstrap deterministic GitHub Actions Devflow",
            "status": "VERIFYING",
            "branch": BRANCH,
            "task_branch": None,
            "publish_branch": None,
            "pull_request": 2,
            "current_stage": "W02",
            "post_merge_profile": "post-merge",
            "notify_completion": True,
            "state_path": f"docs/implementation/{TASK_ID}/task_state.yaml",
        }
    ],
}
write(
    ROOT / "docs/implementation/ACTIVE_TASKS.yaml",
    json.dumps(active, indent=2) + "\n",
)

state = {
    "schema_version": 2,
    "state_revision": 1,
    "task_id": TASK_ID,
    "title": "Bootstrap deterministic GitHub Actions Devflow",
    "status": "VERIFYING",
    "execution_status": "COMPLETED",
    "acceptance": {
        "domain": "repository-bootstrap",
        "status": "PASS",
        "reason_code": None,
        "details_path": None,
    },
    "security_status": "PASS",
    "working_branch": BRANCH,
    "pull_request": 2,
    "base_sha_at_start": BASE_SHA,
    "last_product_commit_sha": BASE_SHA,
    "last_state_commit_sha": None,
    "current_stage": "W02",
    "last_completed_stage": "W01",
    "last_successful_step": "W01_scaffold_imported",
    "next_action": (
        "Install reviewed workflow files through the GitHub connector and run "
        "deterministic PR checks."
    ),
    "gate_results": {},
    "retry_budget": {
        "infrastructure": 3,
        "agent_sessions": 0,
        "agent_recovery_generations": 0,
        "same_root_cause_limit": 2,
    },
    "human_gate": {
        "required": False,
        "reason": None,
        "minimum_action": None,
        "resume_from": None,
    },
    "post_merge": {
        "status": "PENDING",
        "merge_sha": None,
        "verified_run_ids": [],
    },
    "notification": {
        "generation": 0,
        "last_type": None,
        "acknowledged": True,
        "control_issue_number": 1,
    },
    "updated_at_utc": "2026-07-30T03:25:00Z",
}
write(task_dir / "task_state.yaml", json.dumps(state, indent=2) + "\n")

files = {
    "00_contract.md": """# Contract: devflow-bootstrap

Install the reviewed deterministic control plane before A-SCOPE product implementation.

## In scope

- canonical task state and documentation;
- deterministic state, scope, secret and test gates;
- bounded infrastructure recovery and incident notification;
- exact-merge post-merge closeout.

## Out of scope

- A-SCOPE product implementation;
- automatic merge;
- model/agent execution;
- paid relay probes.
""",
    "01_master_plan.md": """# Master plan

1. W00 freeze scope and safety defaults.
2. W01 import and adapt the reviewed scaffold.
3. W02 install workflows and run deterministic PR checks.
4. W03 merge, verify exact merge and close canonical state.
""",
    "STATUS.md": """# Status

- Status: VERIFYING
- Execution: COMPLETED
- Acceptance: PASS
- Security: PASS
- Current stage: W02
- Post-merge: PENDING
""",
    "HANDOFF.md": """# Handoff

W00 and W01 passed. Resume at W02: install the reviewed workflow files through the GitHub connector, then inspect and repair deterministic PR checks. Do not repeat completed stages.
""",
    "DECISIONS.md": """# Decisions

1. Reuse `BullbaseGuy/demo-project@ff6619b1f0ef6797ad1ca09fffa5db9475dc2482`.
2. Keep bootstrap and product implementation in separate PRs.
3. Disable automatic merge and all model/agent execution.
4. Record non-blocking repository settings without pausing implementation.
""",
    "W00_plan.md": "# W00 plan\n\nFreeze scope, task identity and safety defaults.\n",
    "W00_result.md": "# W00 result\n\nPASS. Scope and safety defaults are persisted.\n",
    "W01_plan.md": "# W01 plan\n\nImport and adapt the reviewed non-workflow scaffold files.\n",
    "W01_result.md": """# W01 result

PASS. Non-workflow scaffold files are imported at the fixed reviewed commit. Workflow files are installed separately because GitHub Actions tokens cannot modify workflow definitions.
""",
    "W02_plan.md": """# W02 plan

Install reviewed workflow files, run deterministic PR checks, diagnose demonstrated failures and reach a verifiable pre-merge state.
""",
}
for name, content in files.items():
    write(task_dir / name, content)

manual = {
    "schema_version": 1,
    "actions": [
        {
            "id": "MA-001",
            "stage": "post-bootstrap",
            "blocking": False,
            "owner": "repository-admin",
            "reason": "Configure main required checks only after stable check names appear.",
            "minimum_action": (
                "Require Test, State Consistency and Upgrade Compatibility."
            ),
            "workaround": "Use reviewed manual merges until configured.",
            "status": "OPEN",
            "resume_point": "No pause required.",
        }
    ],
}
write(task_dir / "MANUAL_ACTIONS.yaml", json.dumps(manual, indent=2) + "\n")
