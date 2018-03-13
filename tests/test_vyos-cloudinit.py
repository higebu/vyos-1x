#!/usr/bin/env python3
#
# Copyright (C) 2018 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import os
import tempfile
from unittest import TestCase, mock
import importlib

from vyos.util import ConfigError
vyos_cloudinit = importlib.import_module("src.conf-mode.vyos-cloudinit")


class TestGenerate(TestCase):

    def test_verify(self):
        tests = [
            {'name': 'ec2',
             'c': {'environment': 'ec2'},
             'expected': None
             },
            {'name': 'openstack',
             'c': {'environment': 'openstack'},
             'expected': None
             },
            {'name': 'invalid env',
             'c': {'environment': 'invalid'},
             'expected': vyos_cloudinit.UnsupportedEnvError
             },
            {'name': 'user-defined',
             'c': {'ssh-user': 'user', 'ssh-key': 'http://key', 'user-data': 'http://data'},
             'expected': None
             },
            {'name': 'invalid ssh-key',
             'c': {'ssh-user': 'user', 'ssh-key': 'key', 'user-data': 'http://data'},
             'expected': vyos_cloudinit.UnsupportedSSHKeyURLSchemeError
             },
            {'name': 'invalid user-data',
             'c': {'ssh-user': 'user', 'ssh-key': 'http://key', 'user-data': 'data'},
             'expected': vyos_cloudinit.UnsupportedUserDataURLSchemeError
             }
        ]
        for t in tests:
            with self.subTest(msg=t['name'], c=t['c'], expected=t['expected']):
                actual = vyos_cloudinit.verify(t['c'])
                self.assertIs(t['expected'], actual)

    def test_generate(self):
        tests = [
            {'name': 'ec2',
             'c': {'environment': 'ec2'},
             'expected': [
                 'ENVIRONMENT="ec2"',
                 'SSH_USER="vyos"',
                 'SSH_KEY="http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key"',
                 'USER_DATA="http://169.254.169.254/latest/user-data"']
             },
            {'name': 'openstack',
             'c': {'environment': 'openstack'},
             'expected': [
                 'ENVIRONMENT="openstack"',
                 'SSH_USER="vyos"',
                 'SSH_KEY="http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key"',
                 'USER_DATA="http://169.254.169.254/latest/user-data"']
             },
            {'name': 'user-defined',
             'c': {'ssh-user': 'user', 'ssh-key': 'key', 'user-data': 'data'},
             'expected': [
                 'ENVIRONMENT=""',
                 'SSH_USER="user"',
                 'SSH_KEY="key"',
                 'USER_DATA="data"']
             }
        ]
        for t in tests:
            with self.subTest(msg=t['name'], c=t['c'], expected=t['expected']):
                vyos_cloudinit.config_file = tempfile.mkstemp()[1]
                try:
                    vyos_cloudinit.generate(t['c'])
                    with open(vyos_cloudinit.config_file) as f:
                        actual = f.read()
                finally:
                    os.remove(vyos_cloudinit.config_file)
                self.assertEqual(t['expected'], actual.splitlines()[1:])


class TestApply(TestCase):

    def test_apply(self):
        tests = [
            {'name': 'ec2',
             'c': {'environment': 'ec2'},
             'expected': vyos_cloudinit.enable_cmd
             },
            {'name': 'empty',
             'c': {},
             'expected': vyos_cloudinit.disable_cmd
             }
        ]
        for t in tests:
            with self.subTest(msg=t['name'], c=t['c'], expected=t['expected']):
                with mock.patch('os.system') as os_system:
                    vyos_cloudinit.apply(t['c'])
                    os_system.assert_called_once_with(t['expected'])
