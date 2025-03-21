# tests/test_deployfile.py
import tempfile
from pathlib import Path

from kevinbotlib_deploytool.deployfile import DeployTarget, read_deployfile, write_deployfile


def test_write_and_read_deployfile():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "Deployfile.toml"

        target = DeployTarget(
            python_version="3.11", glibc_version="2.37", arch="aarch64", host="robot.local", port=2222, user="example"
        )

        write_deployfile(target, path)
        assert path.exists()

        read_target = read_deployfile(path)
        assert read_target == target


def test_read_error():
    non_existent_path = Path("/non/existent/Deployfile.toml")
    try:
        read_deployfile(non_existent_path)
    except FileNotFoundError:
        pass
    else:
        msg = "Expected FileNotFoundError"
        raise AssertionError(msg)


def test_from_dict():
    data = {
        "target": {
            "python_version": "3.12",
            "glibc_version": "2.38",
            "arch": "armhf",
            "host": "example.com",
            "port": 2022,
            "user": "example",
        }
    }
    target = DeployTarget.from_dict(data)
    assert target.python_version == "3.12"
    assert target.glibc_version == "2.38"
    assert target.arch == "armhf"
    assert target.host == "example.com"
    assert target.port == 2022


def test_to_dict():
    target = DeployTarget(
        python_version="3.10", glibc_version="2.36", arch="x64", host="robot.local", port=22, user="example"
    )
    data = target.to_dict()
    assert "target" in data
    assert data["target"]["host"] == "robot.local"
