# Phase 01: Project Foundation & Development Environment

## 1. Package / Folder Structure
```text
vigil/                          # Root Python Package
├── __init__.py
├── config.py                   # Central Configuration Loader (Pydantic Settings)
├── cli/                        # Typer CLI Command Interface
│   ├── __init__.py
│   └── main.py                 # CLI Entry Point
├── core/                       # Core Sandbox Orchestration
│   └── __init__.py
├── eval/                       # Pytest Harness & Assertions
│   └── __init__.py
├── db/                         # Database Engine & Schema
│   └── __init__.py
├── api/                        # FastAPI App & Endpoints
│   └── __init__.py
└── tests/                      # Unit & Integration Tests
    ├── __init__.py
    ├── conftest.py             # Test Fixtures & Configurations
    └── test_config.py          # Configuration Unit Tests
pyproject.toml                  # Poetry Dependency Specification
docker-compose.dev.yml          # Local PostgreSQL Dev Service
.env.example                    # Environment Variables Template
.env                            # Local Environment (Git-ignored)
README.md                       # High-level Setup Instructions
```

---

## 2. Purpose
This phase establishes the developer-facing foundation. It sets up the repository structure, specifies exact dependencies via Poetry, implements the configuration loader, spins up local PostgreSQL via Docker Compose, and bootstraps Pytest. The goal is to reach a stable state where unit tests can run successfully and configurations are validated.

---

## 3. Dependencies
### 3.1 External Libraries
- **python**: `^3.12`
- **pydantic**: `^2.7.0` (Data validation)
- **pydantic-settings**: `^2.2.1` (Environment settings loading)
- **pyyaml**: `^6.0.1` (YAML parsing)
- **typer**: `^0.12.0` (CLI engine)
- **rich**: `^13.7.1` (Console logging and tables)
- **docker**: `7.1.0` (Docker SDK)
- **pytest**: `8.2.0` (Testing framework)

### 3.2 Runtime & Services
- **Docker Daemon**: Must be installed and running on the host system, with the current developer user having access to `docker.sock`.
- **PostgreSQL 16.0**: Handled locally via Docker Compose.

---

## 4. Inputs
- `.env` file containing database credentials, local folder paths, and logging configuration.
- Terminal commands parsed by Typer CLI.

---

## 5. Outputs
- Parsed and validated configuration DTOs.
- Structured CLI console messages (via Rich).
- Successful exit code from the test suite.

---

## 6. Public Interfaces
### 6.1 Configuration Schema (`vigil/config.py`)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Environment
    ENV: str = Field(default="development", description="Application environment (development/production/test)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        ...,
        description="Connection URL for the PostgreSQL database"
    )
    
    # Docker/Sandbox defaults
    DOCKER_HOST_URL: str = Field(default="unix:///var/run/docker.sock", description="Docker daemon connection path")
    WORKSPACE_BASE_DIR: str = Field(..., description="Absolute path on the host for mounting temp workspaces")
```

### 6.2 CLI Entrypoint (`vigil/cli/main.py`)
- CLI root application: `app = typer.Typer(name="vigil", help="Vigil Eval Harness CLI")`
- Base Command: `vigil status` (verifies configuration and reports environment states).

---

## 7. Internal Components
- **`Settings`**: Pydantic Settings class loading variables from environment and `.env`.
- **`cli.main`**: Setup command registering base CLI commands.
- **`tests.test_config`**: Asserts correct env file parsing and defaults verification.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
Before implementing or running tests in this phase, the developer must perform the following manual tasks:
- [ ] **Docker Engine**: Verify Docker is installed and running on the host. Run `docker ps` to verify permission access to the socket.
- [ ] **Poetry**: Verify Poetry is installed on the host.
- [ ] **Local Environment File**: Copy `.env.example` to `.env` in the project root.
- [ ] **Database Setup**: Start the database container via `docker compose -f docker-compose.dev.yml up -d db`. Verify connectivity via a Postgres client on port `5432`.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-1.1** | Initialize `pyproject.toml` using Poetry and add required dependencies. | S | Low | Poetry installed | None | Verified `pyproject.toml` file with accurate libraries. | `poetry check` | Validated configuration without dependency conflicts. |
| **TS-1.2** | Write `docker-compose.dev.yml` provisioning a local PostgreSQL 16 container. | S | Low | Docker installed | None | DB container spins up on port `5432`. | Run `docker compose up -d db` and query db version. | Container runs healthy and accepts connections. |
| **TS-1.3** | Implement `.env.example` and create local `.env` with required parameters. | S | Low | TS-1.2 | None | `.env` containing DB credentials and WORKSPACE_BASE_DIR. | Check file existence. | File has correct structure and no secrets are committed. |
| **TS-1.4** | Implement `vigil/config.py` configuration loader via `pydantic-settings`. | M | Low | TS-1.1, TS-1.3 | None | Validated settings loaded into Python variables. | Run `pytest tests/test_config.py`. | Settings class correctly parses invalid strings and throws validation errors. |
| **TS-1.5** | Implement `vigil/cli/main.py` Typer CLI skeleton. | S | Low | TS-1.1 | None | Runnable CLI tool with `vigil status` command. | Run `poetry run vigil status` from command line. | CLI outputs current config status using `rich` styling. |
| **TS-1.6** | Implement base test suite configuration under `tests/` with `conftest.py`. | S | Low | TS-1.1 | None | Pytest config loading settings fixture. | Run `poetry run pytest`. | Suite completes successfully with all baseline tests passing. |

---

## 10. Definition of Done (DoD)
- All packages defined under Folder Structure exist.
- Poetry environment installs cleanly on a fresh workstation.
- Docker-compose starts the local PostgreSQL 16 service correctly.
- Pytest suite executes, executing the configuration loading test successfully.
- CLI executes `poetry run vigil status` and displays status diagnostics.
- No production code is implemented yet.
