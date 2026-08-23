import logging
import os
import signal
import sys
import threading
import docker
from docker.errors import NotFound, APIError

from vigil.core.sandbox_config import SandboxConfig
from vigil.core.docker_client import get_docker_client
from vigil.core.exceptions import SandboxProvisionError, SandboxTeardownError
from vigil.core.workspace_factory import WorkspaceFactory

logger = logging.getLogger(__name__)

class ActiveContainerRegistry:
    """
    In-memory registry to track active containers.
    Used for cleaning up containers in case of signal interruption.
    """
    _lock = threading.Lock()
    _containers = set()

    @classmethod
    def register(cls, container_id: str):
        with cls._lock:
            cls._containers.add(container_id)

    @classmethod
    def unregister(cls, container_id: str):
        with cls._lock:
            cls._containers.discard(container_id)

    @classmethod
    def get_all(cls):
        with cls._lock:
            return list(cls._containers)


# Signal handler registration for process interruption scenarios
_signals_registered = False

def _cleanup_active_containers(signum, frame):
    logger.warning(f"Process interrupted by signal {signum}. Performing emergency sandbox cleanup...")
    try:
        client = get_docker_client()
    except Exception:
        client = None

    for cid in ActiveContainerRegistry.get_all():
        try:
            if client:
                container = client.containers.get(cid)
                logger.info(f"Emergency killing container: {cid}")
                container.kill()
                container.remove(v=True, force=True)
        except Exception as e:
            logger.error(f"Failed to emergency clean container {cid}: {e}")
    sys.exit(128 + signum)

def register_signal_handlers():
    global _signals_registered
    if not _signals_registered:
        # Register SIGINT and SIGTERM handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _cleanup_active_containers)
            except ValueError:
                # Can fail if not in the main thread, which is fine
                pass
        _signals_registered = True


class SandboxManager:
    """
    Manages the lifecycle of a single ephemeral Docker sandbox.
    Guarantees isolation by setting security options, resource limits, and capability drops.
    """
    def __init__(self, config: SandboxConfig, host_workspace_base: str):
        self.config = config
        self.host_workspace_base = host_workspace_base
        self._container = None
        self._workspace_path = None
        register_signal_handlers()

    @property
    def workspace_path(self) -> str:
        """
        Returns the host absolute path to the workspace mounted in this sandbox.
        """
        if not self._workspace_path:
            raise ValueError("Sandbox has not been created yet.")
        return self._workspace_path

    @property
    def container_id(self) -> str:
        """
        Returns the container ID of the running sandbox.
        """
        if not self._container:
            raise ValueError("Sandbox has not been created yet.")
        return self._container.id

    def create_sandbox(self, task_id: str) -> str:
        """
        Provisions and launches the ephemeral task container.
        Returns the container ID.
        """
        if self._container:
            raise SandboxProvisionError("Sandbox container is already running.")

        # 1. Provision unique workspace directory on the host
        try:
            self._workspace_path = WorkspaceFactory.create_workspace(task_id)
        except Exception as e:
            raise SandboxProvisionError(f"Workspace directory provisioning failed: {e}")

        # 2. Build Docker container parameters from SandboxConfig
        docker_args = {
            "image": self.config.image,
            # Run tail -f /dev/null as PID 1 to keep container alive indefinitely
            "command": "tail -f /dev/null",
            "detach": True,
            "user": self.config.user,
            "mem_limit": self.config.mem_limit,
            "nano_cpus": self.config.nano_cpus,
            "cap_drop": self.config.cap_drop,
            "read_only": self.config.read_only_root,
            "volumes": {
                self._workspace_path: {"bind": "/workspace", "mode": "rw"}
            },
            "labels": {
                "vigil-sandbox": "true",
                "task-id": task_id
            }
        }

        if self.config.network_disabled:
            docker_args["network_mode"] = "none"

        security_opt = []
        if self.config.no_new_privileges:
            security_opt.append("no-new-privileges:true")
        if security_opt:
            docker_args["security_opt"] = security_opt

        # 3. Spin up the container
        try:
            client = get_docker_client()
            container = client.containers.run(**docker_args)
            self._container = container
            ActiveContainerRegistry.register(container.id)
            logger.info(f"Successfully provisioned sandbox container {container.id} for task {task_id}")
            return container.id
        except Exception as e:
            # Cleanup workspace on startup failure
            WorkspaceFactory.destroy_workspace(self._workspace_path)
            self._workspace_path = None
            raise SandboxProvisionError(f"Docker container run failed: {e}")

    def destroy_sandbox(self) -> None:
        """
        Forcefully stops (SIGKILL) and removes the Docker container, and purges the workspace.
        """
        container_id = None
        if self._container:
            container_id = self._container.id
            try:
                # Forcefully kill the container immediately (timeout=0)
                logger.info(f"Stopping and removing container {container_id}")
                self._container.kill()
                self._container.remove(v=True, force=True)
            except NotFound:
                logger.warning(f"Container {container_id} not found during teardown (already removed).")
            except Exception as e:
                logger.error(f"Error killing/removing container {container_id}: {e}")
            finally:
                ActiveContainerRegistry.unregister(container_id)
                self._container = None

        if self._workspace_path:
            try:
                WorkspaceFactory.destroy_workspace(self._workspace_path)
            except Exception as e:
                logger.error(f"Error purging workspace path {self._workspace_path}: {e}")
            finally:
                self._workspace_path = None


class Sandbox:
    """
    Context manager wrapper around SandboxManager for try/finally lifecycle assurance.
    Usage:
        with Sandbox(config, host_workspace_base, task_id) as manager:
            # execute tool commands
    """
    def __init__(self, config: SandboxConfig, host_workspace_base: str, task_id: str):
        self.manager = SandboxManager(config, host_workspace_base)
        self.task_id = task_id

    def __enter__(self) -> SandboxManager:
        self.manager.create_sandbox(self.task_id)
        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.destroy_sandbox()
