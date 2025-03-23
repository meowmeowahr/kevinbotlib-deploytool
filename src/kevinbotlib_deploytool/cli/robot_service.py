from pathlib import Path

import click
import jinja2
import paramiko
from rich.console import Console

from kevinbotlib_deploytool import deployfile
from kevinbotlib_deploytool.cli.common import confirm_host_key_df, get_private_key
from kevinbotlib_deploytool.cli.spinner import rich_spinner
from kevinbotlib_deploytool.service import ROBOT_SYSTEMD_USER_SERVICE_TEMPLATE
from kevinbotlib_deploytool.sshkeys import SSHKeyManager

console = Console()


@click.group("service")
def service_group():
    """Robot systemd service management tools"""


@click.command("install")
@click.option(
    "-d",
    "--df-directory",
    default=".",
    help="Directory of the Deployfile",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
def install_service(df_directory):
    """Install the robot systemd service"""
    df = deployfile.read_deployfile(Path(df_directory) / "Deployfile.toml")

    private_key_path, pkey = get_private_key(console, df)

    confirm_host_key_df(console, df, pkey)

    with rich_spinner(console, "Installing service over SSH") as spinner:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507 # * this is ok, because the user is asked beforehand
        ssh.connect(hostname=df.host, port=df.port, username=df.user, pkey=pkey, timeout=10)

        # Check if systemd is available
        check_systemd_ver(ssh)

        # Check if the service file already exists
        check_service_file(df, ssh)

        # Create the service file
        # Use Jinja2 to render the service file
        spinner.status = "Creating service file"
        template = jinja2.Template(ROBOT_SYSTEMD_USER_SERVICE_TEMPLATE)
        service_file_content = template.render(
            working_directory=f"/home/{df.user}/{df.name}/robot",
            exec=f"/home/{df.user}/{df.name}/env/bin/python3 /home/{df.user}/{df.name}/robot/src/{df.name.replace('-', '_')}/__main__.py",
        )
        service_file_path = f"/home/{df.user}/.config/systemd/user/{df.name}.service"
        # Write the service file to the remote system
        spinner.status = "Writing service file over SFTP"
        with ssh.open_sftp() as sftp:
            sftp_makedirs(sftp, Path(service_file_path).parent)
            with sftp.open(service_file_path, "w") as service_file:
                service_file.write(service_file_content)
        console.print(f"[bold green]✔ Service file created at {service_file_path}[/bold green]")
        spinner.status = "Setting permissions for service file"
        # Set permissions for the service file
        ssh.exec_command(f"chmod 644 {service_file_path}")
        spinner.status = "Reloading systemd"
        # Reload systemd to recognize the new service file
        ssh.exec_command("systemctl --user daemon-reload")
        console.print("[bold green]✔ Systemd reloaded successfully[/bold green]")
        spinner.status = "Enabling service"
        # Enable the service
        ssh.exec_command(f"systemctl --user enable {df.name}.service")
        spinner.status = "Starting service"
        # Start the service
        ssh.exec_command(f"systemctl --user start {df.name}.service")
        console.print("[bold green]✔ Service started successfully[/bold green]")
        spinner.status = "Service installed successfully"
        console.print("[bold green]✔ Service installed successfully[/bold green]")

        ssh.close()


@click.command("uninstall")
@click.option(
    "-d",
    "--df-directory",
    default=".",
    help="Directory of the Deployfile",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
)
def uninstall_service(df_directory: str):
    """Uninstall the robot systemd service"""
    df = deployfile.read_deployfile(Path(df_directory) / "Deployfile.toml")

    private_key_path, pkey = get_private_key(console, df)

    confirm_host_key_df(console, df, pkey)

    with rich_spinner(console, "Uninstalling service over SSH") as spinner:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=df.host, port=df.port, username=df.user, pkey=pkey, timeout=10)
        
        check_systemd_ver(ssh)
        check_service_file(df, ssh)

        console.print("[bold red]Stopping service...[/bold red]")
        ssh.exec_command(f"systemctl --user stop {df.name}.service")
        console.print("[bold green]✔ Service stopped successfully[/bold green]")
        
        console.print("[bold red]Disabling service...[/bold red]")
        ssh.exec_command(f"systemctl --user disable {df.name}.service")
        console.print("[bold green]✔ Service disabled successfully[/bold green]")
        
        
        console.print("[bold red]Removing service file...[/bold red]")
        ssh.exec_command(f"rm -f ~/.config/systemd/user/{df.name}.service")
        console.print("[bold green]✔ Service file removed successfully[/bold green]")
        
        console.print("[bold red]Reloading systemd...[/bold red]")
        ssh.exec_command("systemctl --user daemon-reload")
        console.print("[bold green]✔ Service uninstalled successfully[/bold green]")


service_group.add_command(install_service)
service_group.add_command(uninstall_service)


def check_service_file(df, ssh):
    # Check for user service file in ~/.config/systemd/user/
    check_cmd = f"test -f ~/.config/systemd/user/{df.name}.service && echo exists || echo missing"
    _, stdout, _ = ssh.exec_command(check_cmd)
    result = stdout.read().decode().strip()
    if result == "exists":
        console.print(
            f"[yellow]User service file already exists at ~/.config/systemd/user/{df.name}.service. Overwriting...",
        )


def check_systemd_ver(ssh: paramiko.SSHClient):
    stdin, stdout, stderr = ssh.exec_command("systemctl --version")
    systemd_version = stdout.read().decode("utf-8").strip().splitlines()[0].split(" ")[-2]
    if not systemd_version:
        console.print("[red]Systemd is not available on the remote system.[/red]")
        raise click.Abort
    console.print(f"[green]Systemd version: {systemd_version}[/green]")


def sftp_makedirs(sftp, path):
    parts = Path(path).parts
    current = ""
    for part in parts:
        current = f"{current}/{part}" if current else part
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)
