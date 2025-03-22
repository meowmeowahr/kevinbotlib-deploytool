import os
from tempfile import TemporaryDirectory

from kevinbotlib_deploytool.cli.init import attempt_read_project_name


def test_attempt_read_project_name_no_pyproject():
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        os.chdir(temp_dir)
        assert attempt_read_project_name() is None


def test_attempt_read_project_name_invalid_toml():
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        os.chdir(temp_dir)
        with open("pyproject.toml", "w") as f:
            f.write("invalid_toml")

        assert attempt_read_project_name() is None


def test_attempt_read_project_name_no_project_name():
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        os.chdir(temp_dir)
        with open("pyproject.toml", "w") as f:
            f.write("[project]\n")

        assert attempt_read_project_name() is None


def test_attempt_read_project_name_valid():
    with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        os.chdir(temp_dir)
        with open("pyproject.toml", "w") as f:
            f.write("[project]\nname = 'test_project'\n")

        assert attempt_read_project_name() == "test_project"
