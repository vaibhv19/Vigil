# Safety Scope & Boundary Definition: Vigil Phase 2

This document defines the explicit operational boundaries for Vigil’s **Anomaly Detection (Phase 2)**. It serves to align engineering expectations and prevent "scope creep" toward general-purpose cybersecurity, focusing instead on agent-specific failure modes.

---

## 1. Explicitly Detected Anomalies

Vigil Phase 2 implements detection for a strictly enumerated set of risky patterns. Any behavior outside this list is considered "undetected" by design.

### 1.1 Excessive Tool Execution Loops
*   **Threshold Logic:** A task is flagged if the agent exceeds a `max_tool_calls` limit (defined in the Task YAML) or a global `calls_per_minute` burst limit.
*   **Purpose:** Prevents infinite reasoning loops that drain API tokens or saturate host CPU.

### 1.2 Filesystem Path Violations
*   **Boundary Enforcement Strategy:**
    1.  **Non-root execution:** Containers execute as the unprivileged `vigil-user` (UID 1000) to restrict permissions.
    2.  **Sole writable mount:** The root filesystem is mounted read-only, ensuring that `/workspace` is the only writable directory.
    3.  **Path validation:** Prior to execution, command arguments are scanned to block paths outside `/workspace`.
*   **Enforcement vs. Detection:** This is **enforcement + logged detection**. All write attempts to unauthorized directories are blocked by container-level read-only denial. Additionally, the pre-execution path validation layer intercepts and logs these blocked events as `PATH` anomalies in the `anomalies` table with `incident_data` containing the offending command and target paths.
*   **Purpose:** Prevents agents from attempting to persist across runs by modifying the container's base image.

### 1.3 Unexpected Process Spawning
*   **Threshold Logic:** A "Process Allow-list" is defined per tool. If a `PythonTool` attempts to spawn a non-python subprocess (e.g., `nc`, `curl`, `ssh`), the execution is halted.
*   **Purpose:** Prevents agents from using code execution tools to initiate unauthorized network connections or shell-level reconnaissance.

---

## 2. Explicit Non-Claims (Honest Boundaries)

Vigil is an **Evaluation Harness**, not a production-grade Web Application Firewall (WAF) or Intrusion Detection System (IDS).

*   **No Sandbox Escape Detection:** Vigil does not monitor for kernel-level exploits, 0-days, or side-channel attacks designed to break out of Docker isolation to the host OS.
*   **No Intent Analysis:** Vigil detects *patterns*, not *malice*. It cannot determine if an agent is "lying" or "stealing" data if that data is sent through an authorized channel (e.g., an allowed Slack tool).
*   **No General Malicious Behavior Protection:** Vigil does not claim to prevent prompt injection, social engineering, or the generation of harmful content.

---

## 3. Rationale: The "Honest Scope" Philosophy

Vigil adopts a "Local-First / Pattern-Specific" boundary for the same reason a developer-focused tool prioritizes reliability over broadness:

1.  **Deterministic Evals Require Boundaries:** To provide a "Hard Pass/Fail," the failure criteria must be objective. "Detecting all malicious behavior" is a subjective moving target; "Detecting writes to /etc/" is a binary engineering fact.
2.  **Reducing False Positives:** By focusing on three known risky patterns, Vigil ensures that when a "Safety Alert" is triggered, it is actionable and legitimate, rather than a hallucination of a complex security model.
3.  **Engineering Integrity:** Claiming "total safety" in the LLM space is a marketing fallacy. Vigil provides **infrastructure-level guardrails** that allow engineers to iterate safely, acknowledging that absolute security is a separate, multi-layered discipline.

---

## 4. Framing for Portfolio & README

In all documentation and presentations, Vigil’s safety features should be described using the following terminology:

*   **Primary Descriptor:** "Anomaly detection for known agentic failure modes."
*   **Avoid:** "Secure against all AI threats," "Malware detection," "Hack-proof."
*   **Key Value Proposition:** "Vigil ensures your agent stays within its sandbox and doesn't enter an infinite token-burning loop, providing a safe environment for aggressive prompt engineering."

**Analogue:** If a production sandbox is a high-security prison, Vigil is a **crash-test lab**. It isn't meant to hold a master criminal; it's meant to ensure that when the "car" (the agent) hits the wall, the "driver" (the host system) stays safe and the data is recorded.