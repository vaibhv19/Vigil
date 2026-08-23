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
