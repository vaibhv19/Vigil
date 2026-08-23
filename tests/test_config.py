import os
import pytest
from pydantic import ValidationError
from vigil.config import Settings

def test_successful_config_load(test_settings):
    """
    Test that config loads successfully when all required fields are set in env.
    """
    assert test_settings.ENV == "test"
    assert test_settings.LOG_LEVEL == "DEBUG"
    assert str(test_settings.DATABASE_URL) == "postgresql://test_user:test_pass@localhost:5432/test_db"
    assert test_settings.DOCKER_HOST_URL == "npipe:////./pipe/docker_engine"
    assert test_settings.WORKSPACE_BASE_DIR == "/tmp/vigil-test-workspaces"

def test_missing_database_url_raises_error(clean_env):
    """
    Test that a validation error is raised if DATABASE_URL is missing.
    """
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    os.environ["WORKSPACE_BASE_DIR"] = "/tmp/vigil-test-workspaces"
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
        
    assert "DATABASE_URL" in str(exc_info.value)

def test_missing_workspace_base_dir_raises_error(clean_env):
    """
    Test that a validation error is raised if WORKSPACE_BASE_DIR is missing.
    """
    os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5432/test_db"
    if "WORKSPACE_BASE_DIR" in os.environ:
        del os.environ["WORKSPACE_BASE_DIR"]
        
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
        
    assert "WORKSPACE_BASE_DIR" in str(exc_info.value)

def test_default_values(clean_env):
    """
    Test that default values are set correctly for non-required fields.
    """
    os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5432/test_db"
    os.environ["WORKSPACE_BASE_DIR"] = "/tmp/vigil-test-workspaces"
    
    if "ENV" in os.environ:
        del os.environ["ENV"]
    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]
    if "DOCKER_HOST_URL" in os.environ:
        del os.environ["DOCKER_HOST_URL"]
        
    settings = Settings(_env_file=None)
    
    assert settings.ENV == "development"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.DOCKER_HOST_URL == "unix:///var/run/docker.sock"

def test_invalid_database_url(clean_env):
    """
    Test that an invalid DATABASE_URL raises a validation error.
    """
    os.environ["DATABASE_URL"] = "not-a-valid-url"
    os.environ["WORKSPACE_BASE_DIR"] = "/tmp/vigil-test-workspaces"
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
        
    assert "DATABASE_URL" in str(exc_info.value)
