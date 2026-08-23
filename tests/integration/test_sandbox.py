import os
import pytest
import docker
from vigil.core.sandbox_config import SandboxConfig
from vigil.core.sandbox_manager import SandboxManager, Sandbox
from vigil.config import get_settings

def test_sandbox_lifecycle():
    config = SandboxConfig()
    settings = get_settings()
    
    task_id = "test-lifecycle-task"
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, task_id) as manager:
        host_path = manager.workspace_path
        assert os.path.exists(host_path)
        
        # Connect to container via Docker client
        client = docker.DockerClient(base_url=settings.DOCKER_HOST_URL)
        container = client.containers.get(manager.container_id)
        assert container.status == "running"
        
        # Verify container attributes match SandboxConfig
        # Memory limit: 512m = 512 * 1024 * 1024 = 536870912 bytes
        assert container.attrs["HostConfig"]["Memory"] == 536870912
        assert container.attrs["HostConfig"]["NanoCpus"] == 500000000
        assert container.attrs["HostConfig"]["NetworkMode"] == "none"
        assert container.attrs["HostConfig"]["ReadonlyRootfs"] is True
        
        # Verify non-root user UID 1000 execution
        exit_code, output = container.exec_run("id")
        assert exit_code == 0
        assert b"uid=1000(vigil-user)" in output
        
        # Verify writing to root is read-only
        exit_code, output = container.exec_run("touch /root_test")
        assert exit_code != 0
        
        # Verify writing to workspace is writable
        exit_code, output = container.exec_run("touch /workspace/test_file.txt")
        assert exit_code == 0
        
        # Verify file is visible on the host
        host_file_path = os.path.join(host_path, "test_file.txt")
        assert os.path.exists(host_file_path)
        
    # Verify post-teardown cleanup
    with pytest.raises(docker.errors.NotFound):
        client.containers.get(container.id)
        
    assert not os.path.exists(host_path)

def test_sandbox_exception_cleanup():
    config = SandboxConfig()
    settings = get_settings()
    host_path = None
    container_id = None
    client = docker.DockerClient(base_url=settings.DOCKER_HOST_URL)
    
    try:
        with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-exception-task") as manager:
            host_path = manager.workspace_path
            container_id = manager.container_id
            
            # Verify container is running
            container = client.containers.get(container_id)
            assert container.status == "running"
            
            # Raise an exception inside the block
            raise ValueError("Forced error inside context manager")
    except ValueError:
        pass  # expected
        
    # Verify cleanup occurred despite the exception
    with pytest.raises(docker.errors.NotFound):
        client.containers.get(container_id)
        
    assert not os.path.exists(host_path)
