# SPDX-FileCopyrightText: 2025-present meowmeowahr <meowmeowahr@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import click

from kevinbotlib_deploytool.cli.init import init
from kevinbotlib_deploytool.cli.ssh import ssh
from kevinbotlib_deploytool.cli.test import deployfile_test_command
from kevinbotlib_deploytool.cli.venv import venv


@click.group()
def cli():
    """KevinbotLib Deploy Tool"""


cli.add_command(init)
cli.add_command(ssh)
cli.add_command(deployfile_test_command)
cli.add_command(venv)
