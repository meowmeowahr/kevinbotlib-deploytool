"""
Internal command-line interface for KevinbotLib Deploy Tool
"""

# SPDX-FileCopyrightText: 2025-present meowmeowahr <meowmeowahr@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import click

from kevinbotlib_deploytool.cli.deploy_code import deploy_code_command
from kevinbotlib_deploytool.cli.init import init
from kevinbotlib_deploytool.cli.robot import robot_group
from kevinbotlib_deploytool.cli.ssh import ssh_group
from kevinbotlib_deploytool.cli.test import deployfile_test_command
from kevinbotlib_deploytool.cli.venv import venv_group


@click.group()
def cli():
    """KevinbotLib Deploy Tool"""


cli.add_command(init)
cli.add_command(ssh_group)
cli.add_command(robot_group)
cli.add_command(venv_group)
cli.add_command(deploy_code_command)
cli.add_command(deployfile_test_command)
