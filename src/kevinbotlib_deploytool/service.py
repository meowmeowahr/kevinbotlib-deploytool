# Jinja2 template for systemd service that runs in user mode --user
ROBOT_SYSTEMD_USER_SERVICE_TEMPLATE = """
[Unit]
Description=KevinbotLib Robot Service
After=network.target
[Service]
Type=simple
WorkingDirectory={{ working_directory }}
ExecStart={{ exec }}
Restart=on-failure
RestartSec=5
KillSignal=SIGUSR1
"""
