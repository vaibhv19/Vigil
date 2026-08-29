import os
import json
from datetime import datetime, timezone
from typing import Any
from rich.console import Console
from rich.table import Table

class VigilEvalReporter:

    """
    Handles compiling, rendering, and saving evaluation suite outcomes.
    Generates console-friendly tables and saves structured JSON reports.
    """
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.console = Console()

    def generate_report(self, suite_id: str, results: list[dict[str, Any]]) -> str:
        """
        Compiles execution results, renders a rich-text command-line table,
        and persists the raw payload into a timestamped JSON file.
        Returns the path to the written JSON report.
        """
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        errored = sum(1 for r in results if r["status"] == "ERROR")
        
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0
        
        # Construct JSON report dict
        report_payload = {
            "suite_id": suite_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errored": errored,
                "pass_rate": round(pass_rate, 2)
            },
            "results": [
                {
                    "task_id": r["task_id"],
                    "status": r["status"],
                    "failure_reason": r["failure_reason"],
                    "duration_ms": r["duration_ms"],
                    "tool_calls_count": len(r["tool_calls"]),
                    "assertions": r["assertion_results"],
                    "agent_response": r["agent_response"]
                }
                for r in results
            ]
        }
        
        # Save payload to JSON
        timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_file_name = f"report-{suite_id}-{timestamp_str}.json"
        report_path = os.path.abspath(os.path.join(self.output_dir, report_file_name))
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)
            
        # Draw rich output console table
        self.console.print("\n[bold cyan]Vigil Evaluation Run Summary[/bold cyan]")
        self.console.print(f"Suite ID: [yellow]{suite_id}[/yellow]")
        self.console.print(f"Report Location: [green]{report_path}[/green]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Task ID", style="dim", width=30)
        table.add_column("Status", justify="center")
        table.add_column("Duration (ms)", justify="right")
        table.add_column("Tool Calls", justify="right")
        table.add_column("Assertions Passed", justify="center")
        table.add_column("Failure Reason", style="red")
        
        for r in results:
            status_style = "green" if r["status"] == "PASS" else ("yellow" if r["status"] == "FAIL" else "red")
            
            assertions = r["assertion_results"]
            passed_asserts = sum(1 for k, v in assertions.items() if v)
            total_asserts = len(assertions)
            asserts_str = f"{passed_asserts}/{total_asserts}"
            
            table.add_row(
                r["task_id"],
                f"[{status_style}]{r['status']}[/{status_style}]",
                str(r["duration_ms"]),
                str(len(r["tool_calls"])),
                asserts_str,
                r["failure_reason"] or ""
            )
            
        self.console.print(table)
        
        self.console.print(
            f"\n[bold]Results Summary:[/bold] Total: {total} | "
            f"[green]Passed: {passed}[/green] | "
            f"[yellow]Failed: {failed}[/yellow] | "
            f"[red]Errored: {errored}[/red] | "
            f"Pass Rate: [cyan]{pass_rate:.1f}%[/cyan]\n"
        )
        
        return report_path
