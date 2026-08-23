import os
import pytest
from vigil.config import Settings, get_settings

@pytest.fixture
def clean_env():
    """
    Fixture to backup and restore environment variables after a test runs.
    """
    old_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(old_env)
    get_settings.cache_clear()

@pytest.fixture
def test_settings(clean_env):
    """
    Helper fixture to generate configuration instances with test overrides.
    """
    os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5432/test_db"
    os.environ["WORKSPACE_BASE_DIR"] = "/tmp/vigil-test-workspaces"
    os.environ["ENV"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["DOCKER_HOST_URL"] = "npipe:////./pipe/docker_engine"
    
    return Settings(_env_file=None)

@pytest.fixture
def sandbox(test_settings):
    """
    Fixture providing an isolated SandboxManager instance for testing.
    Guarantees container removal and temporary directory cleanup.
    """
    from vigil.core.sandbox_config import SandboxConfig
    from vigil.core.sandbox_manager import Sandbox
    
    config = SandboxConfig()
    settings = get_settings()
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "pytest-fixture") as manager:
        yield manager
