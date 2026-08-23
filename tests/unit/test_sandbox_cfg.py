import pytest
from pydantic import ValidationError
from vigil.core.sandbox_config import SandboxConfig

def test_sandbox_config_defaults():
    config = SandboxConfig()
    assert config.image == "vigil-sandbox-base:latest"
    assert config.mem_limit == "512m"
    assert config.nano_cpus == 500000000
    assert config.network_disabled is True
    assert config.read_only_root is True
    assert config.user == "1000:1000"
    assert config.cap_drop == ["ALL"]
    assert config.no_new_privileges is True
    assert config.task_timeout_seconds == 180

def test_sandbox_config_custom_values():
    config = SandboxConfig(
        image="custom-image:v1",
        mem_limit="1g",
        nano_cpus=1000000000,
        network_disabled=False,
        read_only_root=False,
        user="0:0",
        cap_drop=["SYS_ADMIN", "NET_ADMIN"],
        no_new_privileges=False,
        task_timeout_seconds=60
    )
    assert config.image == "custom-image:v1"
    assert config.mem_limit == "1g"
    assert config.nano_cpus == 1000000000
    assert config.network_disabled is False
    assert config.read_only_root is False
    assert config.user == "0:0"
    assert config.cap_drop == ["SYS_ADMIN", "NET_ADMIN"]
    assert config.no_new_privileges is False
    assert config.task_timeout_seconds == 60

def test_sandbox_config_validation():
    # nano_cpus must be an integer
    with pytest.raises(ValidationError):
        SandboxConfig(nano_cpus="not-an-int")
        
    # network_disabled must be a boolean
    with pytest.raises(ValidationError):
        SandboxConfig(network_disabled="not-a-bool")
