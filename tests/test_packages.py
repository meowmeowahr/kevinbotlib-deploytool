import subprocess
from unittest.mock import patch

from kevinbotlib_deploytool.packages import LocalPackageManagement


@patch("subprocess.run")
def test_get_installed_packages(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = b"package1==1.0.0\npackage2==2.0.0\n"
    mock_subprocess_run.return_value.stderr = b""

    packages = LocalPackageManagement.get_installed_packages()

    assert packages == ["package1==1.0.0", "package2==2.0.0"]
    mock_subprocess_run.assert_called_once_with(
        ["pip", "list", "--format=freeze"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
