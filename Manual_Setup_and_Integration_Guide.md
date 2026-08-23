# Vigil: Manual Setup & Developer Integration Guide

This guide details the steps required to configure, initialize, and verify a local developer workstation for the Vigil Evaluation Harness.

---

## 1. Developer Prerequisites

Before installing Vigil, ensure your workstation meets the following runtime requirements:

### 1.1 Python Environment
- **Python version**: `3.12` or higher (including Python `3.14` support).
- **Poetry version**: `1.8.0` or higher.

### 1.2 Docker Desktop
- **Docker Engine**: Installed and running locally.
- **Context Config**: Set to `default` (to connect via the standard Windows Named Pipe or Unix Socket).
- **WSL2 Backend**: Recommended on Windows to support proper CPU/memory resource boundaries.

### 1.3 PostgreSQL
- **PostgreSQL**: Version `16.0` or higher.
- A local instance can be spun up using the included `docker-compose.dev.yml` file.

---

## 2. Step-by-Step Installation

Follow these steps to initialize your local developer workspace:

### Step 2.1: Install Dependencies
Install all package dependencies inside the virtual environment:
```bash
poetry install
```

### Step 2.2: Environment Configuration
Copy the sample environment file to create your local configurations:
```bash
cp .env.example .env
```
Open the `.env` file and review the following configurations:
```env
ENV=development
LOG_LEVEL=INFO
WORKSPACE_BASE_DIR=./workspaces
DATABASE_URL=postgresql://vigil_user:vigil_pass@localhost:5432/vigil_db
DOCKER_HOST_URL=npipe:////./pipe/docker_engine
```
On Linux or macOS, replace the `DOCKER_HOST_URL` with the Unix socket URI:
```env
DOCKER_HOST_URL=unix:///var/run/docker.sock
```

### Step 2.3: Spin up PostgreSQL Service
Start the local developer database container:
```bash
docker compose -f docker-compose.dev.yml up -d
```

### Step 2.4: Run Database Migrations
Initialize schemas by upgrading database tables to the latest revision:
```bash
poetry run alembic upgrade head
```

---

## 3. Running System Diagnostics

Vigil includes a command-line bootstrap wizard to verify that your developer environment is configured correctly.

### 3.1 Bootstrap Wizard
Run the bootstrap check command to probe configuration parameters, Docker socket readability, database connectivity, and base image availability:
```bash
poetry run vigil bootstrap
```

### 3.2 Framework Status
To check basic configuration diagnostics and connectivity logs at any time, run:
```bash
poetry run vigil status
```

---

## 4. Verification Checklists

### 4.1 Running Test Suites
To verify that all unit and integration tests run successfully, execute:
```bash
poetry run pytest
```

### 4.2 Manual vs Automated Tasks
| Task | Execution Mode | Responsibility |
| :--- | :--- | :--- |
| Docker daemon installation | **Manual** | Developer workstation prerequisite |
| `.env` credential parameters | **Manual** | Developer environment configuration |
| Postgres Dev Container launch | **Manual** | Running `docker compose` service |
| DB Migrations execution | **Automated** | `alembic upgrade head` |
| Sandbox workspace mount generation | **Automated** | `WorkspaceFactory` temporary path creation |
| Resource limits allocation | **Automated** | Docker SDK capability and limits mapping |
| Container/workspace cleanup | **Automated** | Context managers and emergency signal handlers |

---

## 5. Developer Troubleshooting

### 5.1 Docker Connection Failure
If `vigil bootstrap` reports that it cannot connect to the Docker daemon:
1. Confirm Docker Desktop is running.
2. Verify your active context points to `default`:
   ```bash
   docker context use default
   ```
3. Check socket file permissions on Linux or WSL2 (ensure your user has access to `/var/run/docker.sock`).

### 5.2 Pending Migrations Check
If the database connection succeeds but bootstrap warns of pending migrations, run `poetry run alembic upgrade head` to apply updates before executing evaluations.
