# SPDX-FileCopyrightText: 2025-present meowmeowahr <meowmeowahr@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import click

from kevinbotlib_deploytool.cli.init import init
from kevinbotlib_deploytool.cli.ssh import ssh


@click.group()
def cli():
    """KevinbotLib Deploy Tool"""


cli.add_command(init)
cli.add_command(ssh)
