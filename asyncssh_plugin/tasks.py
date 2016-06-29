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

from asyncssh import public_key

from aiorchestra.core import utils


def prepare_env(env):
    bin_bash = '#!/bin/bash\n{0}'
    pattern = 'export {0}="{1}"'
    session_env = ''
    exports = []
    for k, v in env.items():
        exports.append(session_env.join(
            [pattern.format(k, v), ]))
    return bin_bash.format('\n'.join(exports))


async def run_command(node, conn, command):
    node.context.logger.debug('[{0}] - Running command "{1}".'
                              .format(node.name, command))
    stdin, stdout, stderr = await conn.open_session(command)
    eof = False
    while not eof:
        line = await stdout.readline()
        if line:
            node.context.logger.info('{1}'.format(node.name, line))
        eof = stdout.at_eof()
    errs = await stderr.read()
    await stdout.channel.wait_closed()
    exit_status = stdout.channel.get_exit_status()
    node.context.logger.debug('[{0}] - Script exit code: {1}.'
                              .format(node.name, exit_status))
    if exit_status:
        node.context.logger.error('[{0}] - Script execution errors:\n{1}'
                                  .format(node.name, errs))
        raise Exception('[{0}] - Unable to finish software '
                        'configuration successfully, '
                        'aborting. Reason: {1}.'
                        .format(node.name, errs))


async def setup_connection(event_loop,
                           task_retry_interval=None,
                           task_retries=None,
                           username=None, password=None,
                           private_key=None, host=None,
                           port=None):
    pkey = public_key.import_private_key(private_key)
    args = (asyncssh.SSHClient, host)
    kwargs = {}
    kwargs.update(
        username=username,
        client_keys=[pkey, ],
        password=password,
        port=port,
        loop=event_loop,
        known_hosts=None,
    )
    conn, client = await utils.retry(
        asyncssh.create_connection,
        args=args,
        kwargs=kwargs,
        exceptions=(ConnectionRefusedError,),
        task_retry_interval=task_retry_interval,
        task_retries=task_retries
    )
    return conn, client


async def run_script(node, script, event_loop,
                     task_retry_interval=None,
                     task_retries=None,
                     env=None, username=None,
                     password=None, private_key=None,
                     host=None, port=None):
    conn, client = await setup_connection(
        event_loop,
        task_retry_interval=task_retry_interval,
        task_retries=task_retries,
        username=username, password=password,
        private_key=private_key, host=host, port=port)
    async with conn:
        node.context.logger.info('[{0}] - SSH connection established, '
                                 'attempting to run software '
                                 'configuration.'.format(node.name))
        session_env = prepare_env(env)
        setup_commands = [
          "rm -fr /tmp/aiorchestra*",
          'echo -e \'{0}\' >> /tmp/aiorchestra.rc'.format(session_env),
          'echo -e \'{0}\' >> /tmp/aiorchestra-script.sh'.format(script),
          'chmod +x /tmp/aiorchestra-script.sh',
          'chmod +x /tmp/aiorchestra.rc',
        ]

        install_command = ("source /tmp/aiorchestra.rc && "
                           "/bin/bash /tmp/aiorchestra-script.sh;")

        node.context.logger.debug('[{0}] - Running preparations for '
                                  'software configuration script.')
        for command in setup_commands:
            await run_command(node, conn, command)

        node.context.logger.info('[{0}] - Running software '
                                 'configuration script.'
                                 .format(node.name))
        await run_command(node, conn, install_command)


@utils.operation
async def create(node, inputs):
    node.context.logger.info('[{0}] - Setting up SSH '
                             'connection environment.'
                             .format(node.name))
    node.update_runtime_properties('ssh', {
        'host': node.runtime_properties['access_ip'],
        'port': node.properties['port'],
        'username': node.properties['username'],
        'password': node.properties.get('password'),
        'private_key': node.runtime_properties[
            'ssh_keypair']['private_key_content'],
        'env': node.runtime_properties.get('environment', {})
    })


async def run(script_type, node, event_loop,
              task_retry_interval=None,
              task_retries=None):

    try:
        with open(node.properties[script_type], 'r') as s:
            script = s.read()
        await run_script(node, str(script),
                         event_loop,
                         task_retries=task_retries,
                         task_retry_interval=task_retry_interval,
                         **node.runtime_properties['ssh'])
    except Exception as ex:
        node.context.logger.info('[{0}] - Exception during software '
                                 'configuration, reason: {1}.'
                                 .format(node.name, str(ex)))
        raise ex


@utils.operation
async def install(node, inputs):
    task_retry_interval = inputs.get('task_retry_interval')
    task_retries = inputs.get('task_retries')
    node.context.logger.info('[{0}] - Starting software configuration.'
                             .format(node.name))
    event_loop = node.context.event_loop
    await run('install_script', node, event_loop,
              task_retry_interval=task_retry_interval,
              task_retries=task_retries)


@utils.operation
async def uninstall(node, inputs):
    node.context.logger.info('[{0}] - Starting graceful uninstall. '
                             .format(node.name))
    if not node.properties['uninstall_script']:
        node.context.logger.info('[{0}] - Skipping graceful uninstall. '
                                 'Uninstall script was not specified.'
                                 .format(node.name))
    else:
        task_retries = inputs.get('task_retries')
        task_retry_interval = inputs.get('task_retry_interval')
        event_loop = node.context.event_loop
        try:
            await run('uninstall_script', node, event_loop,
                      task_retry_interval=task_retry_interval,
                      task_retries=task_retries)
        except Exception as ex:
            node.context.logger.info('[{0}] - Graceful uninstall failed. '
                                     'Reason: {1}. '
                                     'Proceeding to next task.'
                                     .format(node.name, str(ex)))
            pass


@utils.operation
async def delete(node, inputs):
    node.context.logger.info('[{0}] - Destroying SSH '
                             'connection environment.'
                             .format(node.name))
    if 'ssh' in node.runtime_properties:
        del node.runtime_properties['ssh']


@utils.operation
async def inject(source, target, inputs):
    source.context.logger.info('[{0} -----> {1}] Setting up '
                               'environment using '
                               'target node properties.'
                               .format(target.name, source.name))
    env = source.runtime_properties.get('environment', {})
    env.update(target.properties)
    source.update_runtime_properties('environment', env)


@utils.operation
async def eject(source, target, inputs):
    source.context.logger.info('[{0} --X--> {1}] Destroying environment.'
                               .format(target.name, source.name))
    if 'environment' in source.runtime_properties:
        del source.runtime_properties['environment']
