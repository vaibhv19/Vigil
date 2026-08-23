class VigilError(Exception):
    """Base exception for all Vigil errors."""
    pass

class SandboxProvisionError(VigilError):
    """Raised when container provisioning fails."""
    pass

class SandboxTeardownError(VigilError):
    """Raised when container teardown fails."""
    pass

class ToolExecutionError(VigilError):
    """Raised when a tool execution fails at the harness/host level."""
    pass

class ToolTimeout(VigilError):
    """Raised when a tool execution exceeds its allotted time limit."""
    pass
