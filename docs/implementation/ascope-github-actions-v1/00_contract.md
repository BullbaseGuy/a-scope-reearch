# Contract: ascope-github-actions-v1

## Objective

Implement the A-SCOPE full-market A-share discovery, evidence-upgrade, screening and REOS-S handoff system with deterministic GitHub Actions execution.

## In scope

- provider-agnostic bulk and incremental data adapters;
- point-in-time data contracts and fail-closed QA;
- ten-archetype routing, hard gates, dual scoring and shortlist generation;
- fixture regression, live smoke, weekly reconciliation, financial request, monthly screening and publish workflows;
- REOS-S handoff and research-only artifacts.

## Out of scope

- automatic trading;
- margin leverage;
- paid data as a mandatory dependency;
- fabricated live candidate lists;
- model/agent execution or automatic merge.

## Acceptance

All deterministic tests pass; fixture data is barred from LIVE mode; external API calls are bulk, cached and bounded; P0 and hard gates cannot be overridden by scores.
