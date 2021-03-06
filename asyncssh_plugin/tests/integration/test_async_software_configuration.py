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

from aiorchestra.tests import base

from asyncssh_plugin.tests import config


class BaseAIOrchestraAsyncSSHPlugin(base.BaseAIOrchestraTestCase):
    tosca_directory = base.os.path.join(
        base.os.path.dirname(
            base.os.path.abspath(__file__)), '../templates')


class TestExamples(BaseAIOrchestraAsyncSSHPlugin):

    def setUp(self):
        super(TestExamples, self).setUp()

    def tearDown(self):
        super(TestExamples, self).tearDown()

    @base.with_deployed('aiorchestra-software-config.yaml',
                        inputs=config.CONFIG)
    def test_software_config(self, context):
        pass
