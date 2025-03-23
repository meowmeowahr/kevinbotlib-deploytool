import tarfile
import tempfile
from pathlib import Path

import click
import paramiko
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from kevinbotlib_deploytool.cli.spinner import rich_spinner
from kevinbotlib_deploytool.deployfile import read_deployfile
from kevinbotlib_deploytool.sshkeys import SSHKeyManager

console = Console()


@click.command("deploy-code")
@click.option(
    "-d",
    "--directory",
    default=".",
    help="Directory of the Deployfile and robot code",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
def deploy_code_command(directory):
    """Package and deploy the robot code to the target system."""
    deployfile_path = Path(directory) / "Deployfile.toml"
    if not deployfile_path.exists():
        console.print(f"[red]Deployfile not found in {directory}[/red]")
        raise click.Abort

    df = read_deployfile(deployfile_path)

    # check for src/name/__init__.py
    src_path = Path(directory) / "src" / df.name.replace("-", "_")
    if not (src_path / "__init__.py").exists():
        console.print(f"[red]Robot code is invalid: must contain {src_path / '__init__.py'}[/red]")
        raise click.Abort

    # check for pyproject.toml
    pyproject_path = Path(directory) / "pyproject.toml"
    if not pyproject_path.exists():
        console.print(f"[red]Robot code is invalid: pyproject.toml not found in {directory}[/red]")
        raise click.Abort

    key_manager = SSHKeyManager("KevinbotLibDeployTool")
    key_info = key_manager.list_keys()
    if df.name not in key_info:
        console.print(f"[red]No SSH key for '{df.name}'. Run 'kevinbotlib ssh init' first.[/red]")
        raise click.Abort

    private_key_path, _ = key_info[df.name]

    # Load private key
    try:
        pkey = paramiko.RSAKey.from_private_key_file(private_key_path)
    except Exception as e:
        console.print(f"[red]Failed to load private key: {e}[/red]")
        raise click.Abort from e

    with rich_spinner(console, "Beginning transport session"):
        try:
            sock = paramiko.Transport((df.host, df.port))
            sock.connect(username=df.user, pkey=pkey)
            host_key = sock.get_remote_server_key()
            sock.close()
        except Exception as e:
            console.print(Panel(f"[red]Failed to get host key: {e}", title="Host Key Error"))
            raise click.Abort from e

    console.print(Panel(f"[yellow]Host key for {df.host}:\n{host_key.get_base64()}", title="Host Key Confirmation"))
    if not click.confirm("Do you want to continue connecting?"):
        raise click.Abort

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tarball_path = tmp_path / "robot_code.tar.gz"

        with rich_spinner(console, "Creating code tarball", success_message="Code tarball created"):
            project_root = Path(directory)
            with tarfile.open(tarball_path, "w:gz") as tar:
                src_path = project_root / "src"
                if src_path.exists():
                    tar.add(src_path, arcname="src", filter=_exclude_pycache)

                assets_path = project_root / "assets"
                if assets_path.exists():
                    tar.add(assets_path, arcname="assets", filter=_exclude_pycache)

                pyproject_path = project_root / "pyproject.toml"
                if pyproject_path.exists():
                    tar.add(pyproject_path, arcname="pyproject.toml")

        with rich_spinner(console, "Connecting via SSH", success_message="SSH connection established"):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507 # * this is ok, because the user is asked beforehand
            pkey = paramiko.RSAKey.from_private_key_file(private_key_path)
            ssh.connect(hostname=df.host, port=df.port, username=df.user, pkey=pkey)
            sftp = ssh.open_sftp()

        remote_code_dir = f"$HOME/{df.name}/robot"
        remote_tarball_path = f"/home/{df.user}/{df.name}/robot_code.tar.gz"

        sftp_makedirs(sftp, f"/home/{df.user}/{df.name}")

        # Delete old code on the remote
        with rich_spinner(console, "Deleting old code on remote", success_message="Old code deleted"):
            ssh.exec_command(f"rm -rf {remote_code_dir}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            upload_task = progress.add_task("Uploading code tarball", total=tarball_path.stat().st_size)
            with tarball_path.open("rb") as fsrc:
                try:
                    with sftp.open(remote_tarball_path, "wb") as fdst:
                        while True:
                            chunk = fsrc.read(32768)
                            if not chunk:
                                break
                            fdst.write(chunk)
                            progress.update(upload_task, advance=len(chunk))
                except FileNotFoundError as e:
                    console.print(f"[red]Remote path not found: {remote_tarball_path}[/red]")
                    raise click.Abort from e

        with rich_spinner(console, "Extracting code on remote", success_message="Code extracted"):
            ssh.exec_command(f"mkdir -p {remote_code_dir} && tar -xzf {remote_tarball_path} -C {remote_code_dir}")
            ssh.exec_command(f"rm {remote_tarball_path}")

        console.print(f"[bold green]\u2714 Robot code deployed to {remote_code_dir}[/bold green]")
        ssh.close()


def _exclude_pycache(tarinfo):
    if "__pycache__" in tarinfo.name or tarinfo.name.endswith(".pyc"):
        return None
    return tarinfo


def sftp_makedirs(sftp, path):
    parts = Path(path).parts
    current = ""
    for part in parts:
        current = f"{current}/{part}" if current else part
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)
