# 1. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-18

## Context

We need a lightweight way to record significant technical decisions and the reasons behind them, so future contributors (and our future selves) understand why the system is shaped the way it is.

## Decision

We use Architecture Decision Records (ADRs), one Markdown file per decision in `docs/adr/`, numbered sequentially. Each ADR has: Status, Date, Context, Decision and Consequences. Accepted ADRs are not edited. A new ADR supersedes an old one.

## Consequences

- Decisions are reviewable in pull requests like code.
- Context is preserved even when the people who made the decision are no longer around.
