import docker
from functools import lru_cache
from vigil.config import get_settings

from vigil.core.exceptions import SandboxProvisionError, SandboxTeardownError

@lru_cache()
def get_docker_client() -> docker.DockerClient:
    """
    Returns a cached thread-safe DockerClient connection.
    Uses DOCKER_HOST_URL from settings.
    """
    settings = get_settings()
    try:
        # Pydantic settings are loaded, check if we need to fall back to from_env
        # on Windows with Named Pipe or default unix socket.
        client = docker.DockerClient(base_url=settings.DOCKER_HOST_URL)
        client.ping()
        return client
    except Exception as e:
        # Fallback to default from_env in case base_url needs default parsing
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception:
            raise SandboxProvisionError(f"Failed to connect to Docker daemon at {settings.DOCKER_HOST_URL}: {e}")
