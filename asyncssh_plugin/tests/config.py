#    Author: Denys Makogon
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import getpass

tosca_directory = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)), 'templates/scripts')

CONFIG = {
    'username': os.environ.get('USERNAME', getpass.getuser()),
    'ssh_port': os.environ.get('SSH_PORT', 22),
    'install_script': os.path.join(tosca_directory, 'install.sh'),
    'uninstall_script': os.path.join(tosca_directory, 'uninstall.sh'),
    'ssh_keypair': os.environ.get('SSH_KEYPAIR',
                                  os.path.expanduser('~/.ssh/id_rsa')),
    'host': os.environ.get('SSH_HOST', 'localhost'),
}
