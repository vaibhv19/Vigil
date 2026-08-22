# Vigil: Manual Setup & Developer Integration Guide

This guide details the manual setup required to configure a local developer environment for Vigil. It lists why each step is necessary, how to perform it, and how to verify success.

---

## 1. Automated vs. Manual Tasks Matrix

| Requirement | Category | Handled By | Action Required |
| :--- | :--- | :--- | :--- |
| **Python Packages** | Automated | Poetry | Run `poetry install` |
| **PostgreSQL DB Instance** | Automated | Docker Compose | Run `docker compose up -d db` |
| **Database Schemas** | Automated | Alembic | Run `poetry run alembic upgrade head` |
| **Workspace Dir Setup** | Automated | Harness Runtime | Checked and created per-task automatically |
| **Docker Engine Installation**| Manual | Developer | Install Docker Desktop (Windows/Mac) or Engine (Linux) |
| **Docker Socket Permissions** | Manual | Developer | Add user to the `docker` group (Linux/Mac) |
| **Environment Variable file** | Manual | Developer | Create `.env` from template |
| **LLM Provider API Keys** | Manual | Developer | Acquire OpenAI/Model key and export to `.env` |

---

## 2. Setup Phase 1: Docker Core & Socket Access

### 2.1 Installing Docker
- **Why Required**: Vigil manages container lifecycles via the Docker SDK. A running local Docker daemon is required.
- **Where to Perform**: Local developer workstation.
- **Action**:
  - **Windows/macOS**: Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
  - **Linux**: Install Docker Engine via the package manager (`sudo apt-get install docker-ce docker-ce-cli containerd.io`).
- **Verification**: Run `docker --version` in your terminal.

### 2.2 Verifying Daemon & Socket Access
- **Why Required**: The Vigil Harness must communicate with `/var/run/docker.sock` to start/stop containers.
- **Action (Linux/macOS)**: Ensure the current user has permission to read the socket:
  ```bash
  sudo usermod -aG docker $USER
  ```
  *(Log out and log back in for changes to apply).*
- **Action (Windows)**: In Docker Desktop settings, ensure "Expose daemon on tcp://localhost:2375 without TLS" is toggled off (Vigil communicates directly through the named pipe `npipe:////./pipe/docker_engine`).
- **Verification**: Run `docker ps`. If it prints a list of running containers without permission errors, access is functional.
- **Common Failure Mode**: `Permission Denied` or `Docker daemon is not running`. Fix by starting the service or running terminal sessions with appropriate user privileges.

---

## 3. Setup Phase 2: Environment Configuration

### 3.1 Creating the `.env` File
- **Why Required**: Vigil loads host path directories, database connection strings, and LLM configuration keys from environment variables.
- **Action**: Copy the example configuration template:
  ```bash
  cp .env.example .env
  ```
- **Edit Details**: Open `.env` and fill out the following properties:
  - `WORKSPACE_BASE_DIR`: Absolute path on the host directory (e.g., `d:/Coding/Projects----For Resume/Vigil/temp_workspaces`). This folder must exist and be writable.
  - `DATABASE_URL`: `postgresql://vigil_user:vigil_secure_pass@localhost:5432/vigil_db`
  - `OPENAI_API_KEY`: *(Acquire your key from platform.openai.com. Never commit this file or paste keys in shared chats).*

---

## 4. Setup Phase 3: PostgreSQL Database & Migrations

### 4.1 Launching the Local Database Container
- **Why Required**: Vigil logs all runs, tasks, and anomalies to PostgreSQL.
- **Action**: Launch the database container service in the background:
  ```bash
  docker compose -f docker-compose.dev.yml up -d db
  ```
- **Verification**: Verify the container state:
  ```bash
  docker ps --filter "name=vigil-postgres"
  ```
  Check database logs: `docker compose -f docker-compose.dev.yml logs db`.

### 4.2 Running Database Migrations
- **Why Required**: Initializes the schemas, tables, index variables, and foreign keys.
- **Action**: Apply schema changes using Alembic:
  ```bash
  poetry run alembic upgrade head
  ```
- **Verification**: Connect using a client (e.g., psql or pgAdmin) to port `5432` with user `vigil_user` and database `vigil_db`. Verify tables (`eval_runs`, `tool_calls`, `anomalies`) exist.

---

## 5. Diagnostic Verification Wizard

Once all phases are complete, run the automated health check wizard to confirm environment readiness:
```bash
poetry run vigil bootstrap
```
This utility validates:
- Python runtime compatibilities (`3.12+`).
- Presence of `.env` configurations.
- Docker daemon connections and named pipe/socket read access.
- Existence of `vigil-sandbox-base:latest` image.
- Database connection pools and migration alignments.
