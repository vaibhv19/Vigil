from typer.testing import CliRunner
from vigil.cli.main import app

def test_cli_bootstrap_success():
    """
    Verify that vigil bootstrap CLI subcommand executes successfully and reports green status.
    """
    runner = CliRunner()
    result = runner.invoke(app, ["bootstrap"])
    assert result.exit_code == 0
    assert "Starting Vigil Environment Bootstrap" in result.output
    assert "Success!" in result.output
