import re
from vigil.core.exceptions import AnomalyException

class SubprocessAllowListScanner:
    """
    Scans command arguments for forbidden binaries or shell control metacharacters
    that bypass sandboxing or run unauthorized network utilities.
    """
    @staticmethod
    def scan(arguments: list[str]) -> None:
        """
        Scans command arguments for forbidden binaries or shell control metacharacters.
        Raises AnomalyException if a violation is detected.
        """
        forbidden_binaries = ["curl", "nc", "ssh", "wget", "netcat", "nmap"]
        metacharacters = ["|", ";", "&", "$", "`"]
        
        for arg in arguments:
            # 1. Metacharacter Scan
            for char in metacharacters:
                if char in arg:
                    raise AnomalyException(
                        pattern_type="PROCESS",
                        severity="CRITICAL",
                        incident_data={"offending_argument": arg, "forbidden_character": char},
                        message=f"Forbidden shell control metacharacter '{char}' detected in command: {arg}"
                    )
            
            # 2. Forbidden Binaries Scan
            for binary in forbidden_binaries:
                # Use word boundary search to prevent false positives on normal strings
                pattern = rf"\b{binary}\b"
                if re.search(pattern, arg):
                    raise AnomalyException(
                        pattern_type="PROCESS",
                        severity="CRITICAL",
                        incident_data={"offending_argument": arg, "forbidden_binary": binary},
                        message=f"Forbidden subprocess execution attempt detected for binary '{binary}'"
                    )
