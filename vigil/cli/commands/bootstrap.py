import os
import sys
import typer

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import docker
from sqlalchemy import create_engine

from vigil.config import get_settings

console = Console()

def run_bootstrap():
    """
    Evaluates system diagnostics sequentially and prints status.
    Exits with code 1 if any diagnostic check fails.
    """
    console.print("[bold blue]Starting Vigil Environment Bootstrap Wizard...[/bold blue]\n")
    settings = get_settings()
    
    checks = []
    all_passed = True
    
    # 1. Check Python version compatibility
    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    py_passed = py_ver.major == 3 and py_ver.minor >= 12
    checks.append(("Python Version (>= 3.12)", py_ver_str, "[bold green]PASS[/bold green]" if py_passed else "[bold red]FAIL[/bold red]"))
    if not py_passed:
        all_passed = False

    # 2. Verify environment files exist
    env_exists = os.path.exists(".env")
    checks.append((".env File Configured", "Present" if env_exists else "Missing", "[bold green]PASS[/bold green]" if env_exists else "[bold red]FAIL[/bold red]"))
    if not env_exists:
        all_passed = False

    # 3. Probe Docker daemon and test permissions
    docker_ver_str = "N/A"
    docker_passed = False
    try:
        from vigil.core.docker_client import get_docker_client
        client = get_docker_client()
        client.ping()
        docker_ver = client.version()
        docker_ver_str = docker_ver.get("Version", "Unknown")
        docker_passed = True
    except Exception as e:
        docker_ver_str = f"Error ({e})"
    checks.append(("Docker Socket Readability", docker_ver_str, "[bold green]PASS[/bold green]" if docker_passed else "[bold red]FAIL[/bold red]"))
    if not docker_passed:
        all_passed = False

    # 4. Scan for local existence of vigil-sandbox-base:latest
    image_status = "Missing"
    image_passed = False
    if docker_passed:
        try:
            client.images.get("vigil-sandbox-base:latest")
            image_status = "Available"
            image_passed = True
        except docker.errors.ImageNotFound:
            image_status = "Missing (Run docker build -t vigil-sandbox-base:latest -f dockerfiles/sandbox/Dockerfile .)"
        except Exception as e:
            image_status = f"Query Error ({e})"
    checks.append(("Sandbox Docker Image", image_status, "[bold green]PASS[/bold green]" if image_passed else "[bold red]FAIL[/bold red]"))
    if not image_passed:
        all_passed = False

    # 5. Resolve Database connectivity and migration checks
    db_status = "Disconnected"
    db_passed = False
    migrations_status = "N/A"
    migrations_passed = False
    try:
        engine = create_engine(str(settings.DATABASE_URL), connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            db_status = "Connected"
            db_passed = True
            
            # Check migrations status
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext
            
            alembic_cfg = Config("alembic.ini")
            script = ScriptDirectory.from_config(alembic_cfg)
            fs_heads = script.get_heads()
            
            context = MigrationContext.configure(conn)
            db_heads = context.get_current_heads()
            
            if set(db_heads or []) == set(fs_heads or []):
                migrations_status = "Up-to-Date"
                migrations_passed = True
            else:
                migrations_status = f"Pending (DB: {db_heads}, FS: {fs_heads})"
    except Exception as e:
        db_status = f"Failed ({e})"
        migrations_status = "Skipped"

    checks.append(("PostgreSQL Port Accessibility", db_status, "[bold green]PASS[/bold green]" if db_passed else "[bold red]FAIL[/bold red]"))
    if not db_passed:
        all_passed = False
        
    checks.append(("Alembic Database Migrations", migrations_status, "[bold green]PASS[/bold green]" if migrations_passed else "[bold red]FAIL[/bold red]"))
    if not migrations_passed:
        all_passed = False

    # Print Table
    table = Table(title="Vigil System Diagnostics Summary", show_header=True, header_style="bold cyan")
    table.add_column("Diagnostic Check", style="bold")
    table.add_column("Details", style="dim")
    table.add_column("Status", justify="right")
    
    for check in checks:
        table.add_row(*check)
        
    console.print(table)
    console.print("")

    if all_passed:
        console.print(Panel("[bold green]Success![/bold green] All Vigil infrastructure layers verified successfully. Your developer environment is fully operational.", title="Bootstrap Verdict"))
    else:
        console.print(Panel(
            "[bold red]Configuration Issues Detected![/bold red]\n\n"
            "Please review the failures listed above and verify:\n"
            "1. Docker Desktop is running and active context is set to 'default'.\n"
            "2. PostgreSQL port 5432 compose service is running.\n"
            "3. Database migrations are applied using: [yellow]poetry run alembic upgrade head[/yellow]\n"
            "4. Base sandbox Docker image is built using: [yellow]docker build -t vigil-sandbox-base:latest -f dockerfiles/sandbox/Dockerfile .[/yellow]",
            title="Bootstrap Verdict",
            border_style="red"
        ))
        raise typer.Exit(code=1)
