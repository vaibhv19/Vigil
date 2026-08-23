import os
import socket
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pydantic import ValidationError
import docker

from vigil.config import get_settings

app = typer.Typer(name="vigil", help="Vigil Eval Harness CLI")
console = Console()

@app.callback()
def callback():
    """
    Vigil CLI tool.
    """
    pass

@app.command(name="status")
def status():
    """
    Verify configuration and report system environment states.
    """
    console.print("[bold blue]Checking Vigil System Status...[/bold blue]\n")
    
    # 1. Load configuration
    try:
        settings = get_settings()
    except ValidationError as e:
        console.print("[bold red]Configuration Load Failure![/bold red]")
        console.print(e)
        raise typer.Exit(code=1)
    
    # 2. Prepare Config Summary Table
    table = Table(title="Configuration Settings", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="dim")
    table.add_column("Value")
    
    table.add_row("Environment (ENV)", settings.ENV)
    table.add_row("Log Level (LOG_LEVEL)", settings.LOG_LEVEL)
    
    # Mask database password
    db_url = str(settings.DATABASE_URL)
    if "@" in db_url:
        try:
            # Simple masking for display
            parts = db_url.split("@")
            prefix = parts[0]
            suffix = parts[1]
            if ":" in prefix:
                proto_user = prefix.split(":")
                proto = proto_user[0]
                user = proto_user[1]
                masked_url = f"{proto}://{user}:****@{suffix}"
            else:
                masked_url = f"{prefix}:****@{suffix}"
        except Exception:
            masked_url = "postgresql://****:****@..."
    else:
        masked_url = db_url
        
    table.add_row("Database URL", masked_url)
    table.add_row("Docker Host URL", settings.DOCKER_HOST_URL)
    table.add_row("Workspace Base Dir", settings.WORKSPACE_BASE_DIR)
    
    console.print(table)
    console.print("")

    # 3. Verify Integrations (Docker)
    docker_status = "[bold yellow]Checking...[/bold yellow]"
    try:
        client = docker.DockerClient(base_url=settings.DOCKER_HOST_URL)
        client.ping()
        docker_status = "[bold green]Connected[/bold green]"
    except Exception as e:
        docker_status = f"[bold red]Failed ({e})[/bold red]"
        
    # 4. Verify Integrations (Postgres port socket check)
    pg_status = "[bold yellow]Checking...[/bold yellow]"
    try:
        hosts = settings.DATABASE_URL.hosts()
        host = hosts[0].get("host") if hosts else "localhost"
        port = hosts[0].get("port") if hosts else 5432
        with socket.create_connection((host, port), timeout=3):
            pg_status = "[bold green]Accessible[/bold green]"
    except Exception as e:
        pg_status = f"[bold red]Inaccessible ({e})[/bold red]"

    # 5. Verify Workspace Directory
    workspace_exists = os.path.exists(settings.WORKSPACE_BASE_DIR)
    ws_status = "[bold green]Ready[/bold green]" if workspace_exists else "[bold yellow]Missing (will be auto-created)[/bold yellow]"

    # Print results panel
    console.print(
        Panel(
            f"Docker Daemon: {docker_status}\n"
            f"PostgreSQL Port: {pg_status}\n"
            f"Workspace Path: {ws_status}",
            title="[bold green]Environment Diagnostics[/bold green]",
            expand=False
        )
    )

@app.command(name="run")
def run(
    suite: str = typer.Option(..., "--suite", "-s", help="Path to a directory of YAML task definitions."),
    name: str = typer.Option("Suite Run", "--name", "-n", help="Descriptive name for this suite run."),
    agent_version: str = typer.Option("develop", "--agent-version", "-v", help="Agent version tag for tracking."),
    model_provider: str = typer.Option("openai", "--provider", help="LLM provider (openai)."),
    model_name: str = typer.Option("gpt-4o-mini", "--model", help="LLM model name."),
    concurrency: int = typer.Option(1, "--concurrency", "-c", help="Number of parallel task workers (1-5, max 5)."),
):
    """
    Execute an evaluation suite against an agent inside sandboxed containers.
    """
    import os
    from vigil.agents.langgraph_adapter import LangGraphAgentAdapter
    from vigil.eval.runner import EvalRunner
    from vigil.eval.reporter import VigilEvalReporter

    if not os.path.isdir(suite):
        console.print(f"[bold red]Error:[/bold red] Suite directory not found: {suite}")
        raise typer.Exit(code=1)

    try:
        settings = get_settings()
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    workers = max(1, min(concurrency, 5))

    console.print(f"[bold blue]Starting Vigil evaluation...[/bold blue]")
    console.print(f"  Suite: [yellow]{suite}[/yellow]")
    console.print(f"  Name: [yellow]{name}[/yellow]")
    console.print(f"  Agent Version: [yellow]{agent_version}[/yellow]")
    console.print(f"  Model: [yellow]{model_provider}/{model_name}[/yellow]")
    console.print(f"  Concurrency: [yellow]{workers} worker(s) (max 5)[/yellow]\n")

    adapter = LangGraphAgentAdapter(model_provider=model_provider, model_name=model_name)
    runner = EvalRunner(agent_adapter=adapter, host_workspace_base=settings.WORKSPACE_BASE_DIR)

    try:
        results = runner.run_suite(
            task_dir=suite,
            suite_id=f"{name}-{agent_version}",
            name=name,
            agent_version=agent_version,
            max_workers=workers,
        )
    except Exception as e:
        console.print(f"[bold red]Evaluation failed:[/bold red] {e}")
        raise typer.Exit(code=1)

    reporter = VigilEvalReporter()
    reporter.generate_report(suite_id=f"{name}-{agent_version}", results=results)

@app.command(name="bootstrap")
def bootstrap():
    """
    Evaluate system diagnostics checklist (Docker, DB, environment) to bootstrap local setups.
    """
    from vigil.cli.commands.bootstrap import run_bootstrap
    run_bootstrap()

if __name__ == "__main__":
    app()
