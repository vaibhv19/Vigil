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

class TaskDefinitionValidationError(VigilError):
    """Raised when a task or suite configuration is invalid."""
    pass

class AgentExecutionError(VigilError):
    """Raised when the agent reasoning loop fails or crashes."""
    pass

class DatabasePersistenceError(VigilError):
    """Raised when database connection, query execution, or persistence transactions fail."""
    pass

class TaskTimeout(VigilError):
    """Raised when a task execution exceeds its maximum duration limits."""
    pass
