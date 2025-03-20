from click.testing import CliRunner


def test_cli_group():
    from src.kevinbotlib_deploytool.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "KevinbotLib Deploy Tool" in result.output
