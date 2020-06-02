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

from tempest import config
import tempest.test

from telemetry_tempest_plugin.scenario import utils

CONF = config.CONF

TEST_DIR = os.path.join(os.path.dirname(__file__), 'gnocchi_gabbits')


class GnocchiGabbiTest(tempest.test.BaseTestCase):
    credentials = ['admin']

    TIMEOUT_SCALING_FACTOR = 5

    @classmethod
    def skip_checks(cls):
        super(GnocchiGabbiTest, cls).skip_checks()
        if not CONF.service_available.gnocchi:
            raise cls.skipException("Gnocchi support is required")

    def _prep_test(self, filename):
        token = self.os_admin.auth_provider.get_token()
        url = self.os_admin.auth_provider.base_url(
            {'service': CONF.metric.catalog_type,
             'endpoint_type': CONF.metric.endpoint_type,
             'region': CONF.identity.region})

        os.environ.update({
            "GNOCCHI_SERVICE_URL": url,
            "GNOCCHI_SERVICE_TOKEN": token,
            "GNOCCHI_AUTHORIZATION": "not used",
        })


utils.generate_tests(GnocchiGabbiTest, TEST_DIR)
