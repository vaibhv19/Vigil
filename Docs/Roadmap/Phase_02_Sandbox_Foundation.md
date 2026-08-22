# Phase 02: Sandbox Foundation

## 1. Package / Folder Structure
```text
vigil/
├── core/
│   ├── __init__.py
│   ├── sandbox_config.py       # Pydantic Settings/Models for Sandbox restrictions
│   ├── docker_client.py        # Docker SDK connection factory
│   └── sandbox_manager.py      # Core Sandbox Lifecycle Manager
└── tests/
    ├── integration/
    │   ├── __init__.py
    │   └── test_sandbox.py     # Sandbox lifecycle integration tests
    └── unit/
        ├── __init__.py
        └── test_sandbox_cfg.py # Sandbox Config unit tests
```

---

## 2. Purpose
This phase builds the isolated runtime layer. It integrates with the Docker SDK to configure, provision, and clean up the unprivileged container sandboxes. The sandbox is created at the start of a task, maintains state across multiple sequential tool executions within that task, and is forcefully terminated and deleted upon task completion, timeout, or failure.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.config` (For reading default directories and daemon socket locations)

### 3.2 External Libraries
- `docker` (Python Docker SDK)
- `pydantic` (For `SandboxConfig` definition)

### 3.3 Runtime / OS Dependencies
- **Docker Sandbox Base Image**: A minimal image (e.g. Alpine-based `vigil-sandbox-base:latest`) must be built or pulled on the host prior to execution.
- **Docker permissions**: The host process running the harness must have permission to write to `/var/run/docker.sock`.

---

## 4. Inputs
- `SandboxConfig` instances specifying:
  - Docker base image name.
  - Resource limits (CPU, Memory).
  - Network toggle (disabled by default).
  - Task timeout boundary.
  - Host workspace root directory.

---

## 5. Outputs
- Provisioned running Docker container object managed by the harness.
- Mounted temporary workspace folder on the host filesystem.
- Safe teardown results (reclaimed resources, deleted temporary volumes).
- `SandboxProvisionError` or `SandboxTeardownError` on execution failures.

---

## 6. Public Interfaces
### 6.1 Sandbox Configuration (`vigil/core/sandbox_config.py`)
```python
from pydantic import BaseModel, Field

class SandboxConfig(BaseModel):
    image: str = Field(default="vigil-sandbox-base:latest", description="Sandbox Docker image")
    mem_limit: str = Field(default="512m", description="Memory limit (e.g. 512m)")
    nano_cpus: int = Field(default=500000000, description="CPU allotment in nano-CPUs (500000000 = 0.5 CPU)")
    network_disabled: bool = Field(default=True, description="Disable network access inside the container")
    read_only_root: bool = Field(default=True, description="Mount container root filesystem as read-only")
    user: str = Field(default="1000:1000", description="User UID:GID to execute as (vigil-user)")
    cap_drop: list[str] = Field(default_factory=lambda: ["ALL"], description="Linux capabilities to drop")
    no_new_privileges: bool = Field(default=True, description="Prevent child processes from gaining privileges")
    task_timeout_seconds: int = Field(default=180, description="Maximum total task execution time")
```

### 6.2 Sandbox Manager Interface (`vigil/core/sandbox_manager.py`)
```python
class SandboxManager:
    def __init__(self, config: SandboxConfig, host_workspace_base: str): ...
    def create_sandbox(self, task_id: str) -> str: ... # Returns container ID, sets up workspace
    def destroy_sandbox(self) -> None: ... # Stops container (SIGKILL) & purges temp directory
    @property
    def workspace_path(self) -> str: ... # Returns local host absolute path to mount
```

---

## 7. Internal Components
- **`DockerClientFactory`**: A utility layer caching the `docker.from_env()` or custom client reference.
- **`WorkspaceFactory`**: Handles creation of temporary host directories (`/tmp/vigil-workspaces/<task_id>-<uuid>/`) and guarantees their permissions are writable by UID 1000.
- **`ActiveContainerRegistry`**: (In-memory) Tracks currently active container IDs to ensure signal handlers can intercept process exits and prune leftovers.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Sandbox Base Image**: Build the sandbox base image locally. Create a minimal `Dockerfile` under `dockerfiles/sandbox/` containing a non-root user `vigil-user` (UID 1000) and essential packages (Python, bash). Build it as `vigil-sandbox-base:latest`.
- [ ] **Docker Engine Connection**: Run the baseline integration test to verify the harness communicates with the Docker socket.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-2.1** | Create `dockerfiles/sandbox/Dockerfile` for the Alpine-based `vigil-sandbox-base:latest`. | S | Low | TS-1.1 | None | Dockerfile with UID 1000 user. | Build image via command line: `docker build -t vigil-sandbox-base:latest .` | Image built successfully and verified with non-root user. |
| **TS-2.2** | Implement `vigil/core/sandbox_config.py` Pydantic model. | S | Low | TS-1.4 | None | Model capturing all security constraints. | Unit test verifying invalid configurations are rejected. | Schema validation covers CPU, memory, and capability arrays. |
| **TS-2.3** | Implement `vigil/core/docker_client.py` client factory. | S | Low | TS-1.4 | None | Thread-safe, cached connection object. | Integration test pinging the Docker daemon. | Docker connection is verified and exceptions are caught. |
| **TS-2.4** | Implement `WorkspaceFactory` creating temporary, host-bound workspaces. | M | Med | TS-1.4 | None | Writable host folder, mapped to unique sub-dirs. | Test verifying filesystem folder creation and correct permission mask. | Temporary folder is created, mapped, and cleaned up correctly. |
| **TS-2.5** | Implement container configuration generator mapping `SandboxConfig` to Docker SDK arguments. | M | Med | TS-2.2 | None | Python dictionary containing SDK arguments. | Test mapping config model properties to API schema fields. | Maps `cap_drop`, `network_disabled`, `read_only`, CPU limits, and memory. |
| **TS-2.6** | Implement `SandboxManager.create_sandbox` launching the task container. | M | High | TS-2.3, TS-2.4, TS-2.5 | None | Active Docker container with mounted host directory at `/workspace`. | Test verifying container startup, checks non-root user and CPU limits. | Container runs with strict resource caps and permissions. |
| **TS-2.7** | Implement `SandboxManager.destroy_sandbox` stopping and removing the container. | M | Med | TS-2.6 | None | Container is stopped and deleted; workspace is purged. | Integration test ensuring container and workspace folder no longer exist. | Cleanup is robust to missing containers or deleted files. |
| **TS-2.8** | Implement Context Manager wrapper around `SandboxManager` for `try/finally` lifecycle assurance. | S | Low | TS-2.7 | None | Safe context wrapper (`with Sandbox(...) as s:`). | Test ensuring cleanup is invoked if inner block raises an exception. | Container is destroyed in the presence of raised python exceptions. |

---

## 10. Definition of Done (DoD)
- Sandbox configurations validate successfully.
- An Alpine sandbox base image is built.
- Harness can start an unprivileged Docker container with `mem_limit="512m"`, `0.5 CPU`, `network_disabled=True`, dropped capabilities, and a read-only root directory.
- Container mounts a host folder to `/workspace` writable by user UID 1000.
- Safe teardown context managers execute, ensuring 100% reclamation of containers and host folders.
- Testing includes verification of container limits.
