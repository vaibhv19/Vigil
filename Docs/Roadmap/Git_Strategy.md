# Vigil: Git Strategy & Workflow Guidelines

This document outlines the version control workflows for Vigil development. It is optimized for a single developer working sequentially, ensuring stable checkpoints and clean histories.

---

## 1. Branch Hierarchy

```text
main (Production/Stable Checkpoints)
  ▲
  │ (Merge at Milestones)
  │
develop (Integration Branch)
  ▲
  ├─► feature/01-project-foundation
  ├─► feature/02-sandbox-core
  ├─► feature/03-tool-execution
  ├─► ...
  └─► feature/13-portfolio-readiness
```

### 1.1 Branch Definitions
- **`main`**: Represents production-ready, fully tested, and stable milestones. Direct commits are forbidden.
- **`develop`**: The primary integration branch where features are consolidated.
- **`feature/`**: Temporary branches created off `develop` to implement specific roadmap phases or atomic tasks.

---

## 2. Feature Branch Boundaries

Each major phase must execute within its own feature branch:

| Branch Name | Phase Target | Prerequisite |
| :--- | :--- | :--- |
| `feature/01-project-foundation` | Phase 01 | None |
| `feature/02-sandbox-core` | Phase 02 | Phase 01 merged to `develop` |
| `feature/03-tool-execution` | Phase 03 | Phase 02 merged to `develop` |
| `feature/04-eval-definitions` | Phase 04 | Phase 03 merged to `develop` |
| `feature/05-agent-adapters` | Phase 05 | Phase 04 merged to `develop` |
| `feature/06-pytest-harness` | Phase 06 | Phase 05 merged to `develop` |
| `feature/07-db-persistence` | Phase 07 | Phase 06 merged to `develop` |
| `feature/08-mvp-stabilization` | Phase 08 | Phase 07 merged to `develop` |
| `feature/09-bootstrap-wizard` | Phase 09 | Phase 08 merged to `develop` |
| `feature/10-anomaly-monitors` | Phase 10 | Phase 08 merged to `develop` |
| `feature/11-metrics-math` | Phase 11 | Phase 10 merged to `develop` |
| `feature/12-api-dashboard` | Phase 12 | Phase 11 merged to `develop` |
| `feature/13-portfolio-readiness` | Phase 13 | Phase 12 merged to `develop` |

---

## 3. Commit Conventions

Vigil uses structured commit messages. Every commit must clearly state the component changed.

### 3.1 Format
`<type>(<scope>): <short description>`

- **`feat`**: A new feature (e.g. `feat(sandbox): add memory limit constraints`)
- **`fix`**: A bug fix (e.g. `fix(persistence): resolve timezone offset on tool duration`)
- **`test`**: Writing or updating tests (e.g. `test(scoring): add json schema test cases`)
- **`docs`**: Documentation updates (e.g. `docs(setup): compile database setup instructions`)
- **`chore`**: Maintenance, package dependencies, or configurations (e.g. `chore(poetry): add asyncpg driver`)

### 3.2 Commit Boundaries
Avoid massive "end-of-phase" commits. Commit at atomic task completions:
1. Write Pydantic model -> Commit `feat(config): implement SandboxConfig validation schema`
2. Implement create logic -> Commit `feat(sandbox): implement container startup logic`
3. Add cleanup tests -> Commit `test(sandbox): verify container cleanup on crash`

---

## 4. Merge Checkpoints & Gates

Before merging any feature branch into `develop` or merging `develop` into `main`, the following checklist must pass:

### 4.1 Feature -> `develop` Gate
- All tests in the branch pass (`poetry run pytest`).
- Linter and formatter checks pass (if configured).
- No temporary/scratch files are committed.
- Configuration variables are documented in `.env.example`.

### 4.2 `develop` -> `main` Milestone Gate
- Verified Milestone status is reached (corresponding to the checkpoint in [Milestones.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Milestones.md)).
- Full database migrations ran and passed successfully.
- Manual setup documentation is updated.
- Tag the milestone release: `git tag -a v1.0.0-m1 -m "Milestone 1: Ephemeral Sandbox Isolation"`
