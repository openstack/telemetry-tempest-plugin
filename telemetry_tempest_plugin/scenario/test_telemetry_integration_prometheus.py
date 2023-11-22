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

TEST_DIR = os.path.join(os.path.dirname(__file__),
                        'telemetry_integration_prometheus_gabbits')


class PrometheusGabbiTest(tempest.test.BaseTestCase):
    credentials = ['admin']

    TIMEOUT_SCALING_FACTOR = 5

    @classmethod
    def skip_checks(cls):
        super(PrometheusGabbiTest, cls).skip_checks()
        if not CONF.service_available.sg_core:
            raise cls.skipException("sg-core support is required")

    def _prep_test(self, filename):
        os.environ.update({
            "SG_CORE_SERVICE_URL":
            str(config.CONF.telemetry.sg_core_service_url),
        })


utils.generate_tests(PrometheusGabbiTest, TEST_DIR)
