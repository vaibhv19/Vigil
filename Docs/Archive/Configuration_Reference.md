# Vigil: Configuration Reference

This document catalogs all configuration properties, environment variables, and configurable settings in Vigil.

---

## 1. Environment Configurations (`.env`)

These settings are loaded using `pydantic-settings` from environment variables or a local `.env` file located in the project root.

| Variable Name | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `ENV` | `str` | `development` | The runtime environment. Values: `development`, `test`, `production`. |
| `LOG_LEVEL` | `str` | `INFO` | Standard library logging level. Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `DATABASE_URL` | `PostgresDsn` | *(Required)* | PostgreSQL connection string. Format: `postgresql://[user]:[password]@[host]:[port]/[db]` |
| `DOCKER_HOST_URL` | `str` | `unix:///var/run/docker.sock`| Connection path to the Docker daemon. On Windows, uses: `npipe:////./pipe/docker_engine`. |
| `WORKSPACE_BASE_DIR` | `str` | *(Required)* | Absolute path on the host filesystem where temporary directories are created. |

---

## 2. Sandbox Constraints Configuration (`SandboxConfig`)

These settings define the isolation boundaries applied by the `SandboxManager` during container provisioning.

| Field Name | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `image` | `str` | `vigil-sandbox-base:latest`| Docker sandbox image to run. |
| `mem_limit` | `str` | `512m` | RAM memory cap. |
| `nano_cpus` | `int` | `500000000` | CPU execution cap (0.5 cores). |
| `network_disabled` | `bool` | `True` | Network isolation toggle. If True, blocks networking (`network_mode="none"`). |
| `read_only_root` | `bool` | `True` | Mounts root filesystem as read-only. Only `/workspace` remains writable. |
| `user` | `str` | `1000:1000` | Executes commands inside the sandbox under this UID:GID (`vigil-user`). |
| `cap_drop` | `list[str]` | `["ALL"]` | Drops Linux capabilities. |
| `no_new_privileges`| `bool` | `True` | Sets the security options flag to prevent subprocess privilege escalation. |
| `task_timeout_seconds`| `int` | `180` | Maximum total duration allowed for an evaluation task before execution is aborted. |

---

## 3. Configuration Loading Verification

To verify that local configurations are correct and load successfully, run:
```bash
poetry run pytest tests/unit/test_sandbox_cfg.py
```
This test asserts:
- Missing required fields (like `DATABASE_URL` or `WORKSPACE_BASE_DIR`) raise validation errors.
- Default variables fall back to secure limits.
- Environment type casting functions correctly.
