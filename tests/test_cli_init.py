import os
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from kevinbotlib_deploytool.cli_init import init


def test_init_command_valid():
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            init,
            [
                "--ssh-host",
                "example.com",
                "--ssh-port",
                "22",
                "--python-version",
                "3.10",
                "--glibc-version",
                "2.36",
                "--arch",
                "x64",
                "--dest-dir",
                temp_dir,
            ],
        )
        assert result.exit_code == 0
        assert f"Deployfile created at {os.path.join(temp_dir, 'Deployfile.toml')}" in result.output
        assert os.path.exists(os.path.join(temp_dir, "Deployfile.toml"))


def test_init_command_invalid_port():
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            init,
            [
                "--ssh-host",
                "example.com",
                "--ssh-port",
                "70000",  # Invalid port
                "--python-version",
                "3.10",
                "--glibc-version",
                "2.36",
                "--arch",
                "x64",
                "--dest-dir",
                temp_dir,
            ],
        )
        assert result.exit_code != 0
        assert "SSH port must be between 1 and 65535" in result.output


def test_init_command_invalid_python_version():
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            init,
            [
                "--ssh-host",
                "example.com",
                "--ssh-port",
                "22",
                "--python-version",
                "4.0",  # Invalid version
                "--glibc-version",
                "2.36",
                "--arch",
                "x64",
                "--dest-dir",
                temp_dir,
            ],
        )
        assert result.exit_code != 0
        assert "Version must be < 4.0" in result.output


def test_init_command_invalid_glibc_version():
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            init,
            [
                "--ssh-host",
                "example.com",
                "--ssh-port",
                "22",
                "--python-version",
                "3.10",
                "--glibc-version",
                "invalid",  # Invalid version
                "--arch",
                "x64",
                "--dest-dir",
                temp_dir,
            ],
        )
        assert result.exit_code != 0
        assert "Invalid version format 'invalid'. Use X.Y (e.g., 3.10)" in result.output


def test_init_command_existing_deployfile():
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, "Deployfile.toml"), "w") as f:
            f.write("overwrite me")

        result = runner.invoke(
            init,
            [
                "--ssh-host",
                "example.com",
                "--ssh-port",
                "22",
                "--python-version",
                "3.10",
                "--glibc-version",
                "2.36",
                "--arch",
                "x64",
                "--dest-dir",
                temp_dir,
            ],
        )
        assert result.exit_code == 0
        assert f"Deployfile created at {os.path.join(temp_dir, 'Deployfile.toml')}" in result.output
        assert os.path.exists(os.path.join(temp_dir, "Deployfile.toml"))
