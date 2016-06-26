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

import asyncssh
import sys

from asyncssh import public_key

from aiorchestra.core import utils


class MySSHClientSession(asyncssh.SSHClientSession):
    def data_received(self, data, datatype):
        if datatype == asyncssh.EXTENDED_DATA_STDERR:
            print(data, end='', file=sys.stderr)
        else:
            print(data, end='')

    def exit_status_received(self, status):
        if status:
            print('Program exited with status %d' % status, file=sys.stderr)
        else:
            print('Program exited successfully')

    def connection_lost(self, exc):
        if exc:
            print('SSH session error: ' + str(exc), file=sys.stderr)


async def run_script(script, env, username, password,
                     private_key, pub_key, host, port, event_loop):
    pkey = public_key.import_private_key(private_key)
    pub_key = public_key.import_public_key(pub_key)
    conn, client = await asyncssh.create_connection(
        asyncssh.SSHClient, host,
        username=username,
        client_keys=[pkey, ],
        password=password,
        port=port,
        loop=event_loop,
        known_hosts=([pub_key], [], [])
    )
    async with conn:
        command = ('echo -e "{0}" >> /tmp/aiochestra-install-script.sh; '
                   'chmod +x /tmp/aiochestra-install-script.sh; '
                   './tmp/aiochestra-install-script.sh;'.format(script))

        channel, session = await conn.create_session(
            asyncssh.SSHClientSession,
            command=command,
            env=env
        )
        await channel.wait_closed()


@utils.operation
async def install(node, inputs):
    event_loop = node.context.event_loop
    host = node.runtime_properties['access_ip']
    port = node.properties['port']

    username = node.properties['username']
    password = node.properties.get('password')
    key = node.runtime_properties[
        'ssh_keypair']['private_key_content']
    pub_key = node.runtime_properties[
        'ssh_keypair']['public_key']
    script = node.properties['script']
    env = node.properties.get('environment')
    _script = None
    with open(script, 'rb') as s:
        _script = s.read()

    async def try_to_connect():
        try:
            await run_script(_script, env, username,
                             password, key, pub_key, host,
                             port, event_loop)
            return True
        except Exception as ex:
            node.context.logger.info(str(ex))
            return False

    await utils.retry(try_to_connect, exceptions=(Exception, ),
                      task_retries=20, task_retry_interval=5)


@utils.operation
async def uninstall(node, inputs):
    pass
