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

from aiorchestra.core import utils

from asyncssh_plugin.tests import config


@utils.operation
async def inject_host_and_key(source, target, input):
    key = config.CONFIG['ssh_keypair']
    with open(key, 'rb') as k:
        key_content = k.read()
        source.batch_update_runtime_properties(**{
            'access_ip': config.CONFIG.get('host'),
            'ssh_keypair': {
                'private_key_content': key_content
            }
        })


@utils.operation
async def eject_host_and_key(source, target, input):
    for attr in ['access_ip', 'ssh_keypair']:
        if attr in source.runtime_properties:
            del source.runtime_properties[attr]
