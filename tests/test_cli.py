from click.testing import CliRunner


def test_cli_group():
    from kevinbotlib_deploytool.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "KevinbotLib Deploy Tool" in result.output


def test_ssh_group():
    from kevinbotlib_deploytool.cli import ssh_group

    runner = CliRunner()
    result = runner.invoke(ssh_group)
    assert result.exit_code == 0
    assert "SSH Key Enroll" in result.output
