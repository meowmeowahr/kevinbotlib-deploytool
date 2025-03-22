import subprocess
import sys


class LocalPackageManagement:
    @staticmethod
    def get_installed_packages() -> list[str]:
        """Get a list of installed packages."""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            check=True,
            capture_output=True,
        )
        return result.stdout.decode("utf-8").splitlines()
