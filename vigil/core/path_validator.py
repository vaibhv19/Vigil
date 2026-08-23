import re
from vigil.core.exceptions import AnomalyException

class PathValidationLayer:
    """
    Scans command arguments for path escapes and directory traversal attempts
    before they are executed in the Docker sandbox container.
    """
    @staticmethod
    def validate(arguments: list[str]) -> None:
        """
        Checks command argument arrays for directory traversal elements (..)
        or absolute paths pointing outside /workspace.
        """
        # Allow common system execution prefixes inside sandbox
        allowed_system_prefixes = (
            "/workspace",
            "/bin/",
            "/usr/bin/",
            "/sbin/",
            "/usr/sbin/",
            "/lib",
            "/usr/lib",
            "/dev/null"
        )
        
        for arg in arguments:
            # 1. Directory Traversal Check
            if ".." in arg:
                raise AnomalyException(
                    pattern_type="PATH",
                    severity="CRITICAL",
                    incident_data={"offending_argument": arg, "violation": "directory_traversal"},
                    message=f"Directory traversal attempt detected in argument: {arg}"
                )
            
            # 2. Absolute Path Escape Check
            # Extract absolute paths (starting with /)
            paths = re.findall(r'/[a-zA-Z0-9_\-\.\/]+', arg)
            for p in paths:
                if p == "/":
                    continue
                # If path does not match any of our allowed prefixes, flag it
                if not p.startswith(allowed_system_prefixes):
                    raise AnomalyException(
                        pattern_type="PATH",
                        severity="CRITICAL",
                        incident_data={"offending_argument": arg, "extracted_path": p, "violation": "absolute_path_escape"},
                        message=f"Absolute path escape outside /workspace detected: {p}"
                    )
