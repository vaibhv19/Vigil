# Phase 09: Manual Setup & Developer Integration Guide

## 1. Package / Folder Structure
```text
Manual_Setup_and_Integration_Guide.md  # Consolidated setup and verify guide
vigil/
└── cli/
    └── commands/
        ├── __init__.py
        └── bootstrap.py                # Setup checklist CLI wizard (vigil bootstrap)
```

---

## 2. Purpose
This phase formalizes the manual installation and configuration tasks required to initialize a local developer workstation. It consolidates setup instructions scattered across early phases (such as installing Docker, starting the daemon, setting socket permissions, copying env parameters, creating local directories, generating DB credentials, running migrations, and verifying network states) into one authoritative developer-facing document, and builds a CLI check tool to verify configurations.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.config` (For verifying environment configs)
- `vigil.db.connection` (For testing database connectivity)
- `vigil.core.docker_client` (For testing Docker socket connectivity)

### 3.2 External Libraries
- `typer` (CLI runner)
- `rich` (Visual diagnostic layout)

### 3.3 Runtime / OS Dependencies
- Native host terminal access (PowerShell/Bash)
- Docker daemon binary installation.
- PostgreSQL database engine availability.

---

## 4. Inputs
- Real manual environment requirements gathered during Phases 1–8.
- `.env` values filled out by the developer.

---

## 5. Outputs
- Consolidated [Manual_Setup_and_Integration_Guide.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Manual_Setup_and_Integration_Guide.md) file.
- CLI diagnosis wizard (`vigil bootstrap`) returning success status only when all infrastructure layers are verified.

---

## 6. Public Interfaces
### 6.1 CLI Check Commands
- `vigil bootstrap`: Evaluates system diagnostics sequentially:
  1. Checks Python version compatibility.
  2. Verifies environment files exist.
  3. Probes the Docker daemon socket and tests API permissions.
  4. Resolves database host connection pools and verifies migrated status.
  5. Scans for the local existence of `vigil-sandbox-base:latest`.

---

## 7. Internal Components
- **`DiagnosticSuite`**: Collection of health-check methods validating Docker, DB, and folder system constraints.
- **`InteractiveSetupAssistant`**: Console-based helper guiding database creation and credential exports.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Phase 8 verified**: Confirm core integrations are stable and functional.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-9.1** | Create [Manual_Setup_and_Integration_Guide.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Manual_Setup_and_Integration_Guide.md) file. | M | Low | TS-8.7 | None | Authoritative setup guide separating manual vs automated steps. | Proofread links, verify CLI commands listed run on host systems. | Document is structured, clear, and doesn't request secrets. |
| **TS-9.2** | Implement `vigil bootstrap` CLI verification suite. | M | Med | TS-1.5, TS-2.3, TS-7.4 | None | Interactive Typer command performing diagnostic checks. | Run `poetry run vigil bootstrap` with missing configs, check outputs. | Wizard prints pass/fail diagnostics for environment, Docker, and DB. |
| **TS-9.3** | Add Docker permissions and socket connectivity tests to bootstrap. | S | Low | TS-9.2 | None | CLI checks socket readability and lists running containers. | Run command; verify socket issues are caught. | Socket issues are clearly explained with resolution commands. |
| **TS-9.4** | Add Database connectivity and migration checks to bootstrap. | S | Low | TS-9.2 | None | CLI tests DB connectivity and verifies schema is current. | Run command with database stopped, check error messages. | Database issues and pending migrations are clearly flagged. |
| **TS-9.5** | Write documentation audit script verifying installation checklist. | S | Low | TS-9.1 | None | Verifies setup guide commands are correct and up to date. | Execute setup guide instructions on a fresh test directory. | Workspace prepares successfully when instructions are followed. |

---

## 10. Definition of Done (DoD)
- The [Manual_Setup_and_Integration_Guide.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Manual_Setup_and_Integration_Guide.md) file is generated in the artifacts directory.
- The guide clearly separates manual tasks (installing Docker, env values, secrets) from automated ones (migrations, sandbox limits).
- The `vigil bootstrap` CLI command is implemented, running health check diagnostics on the Docker daemon, PostgreSQL pool, and migrations.
- The setup steps are verified to successfully prepare a clean developer environment from scratch.
