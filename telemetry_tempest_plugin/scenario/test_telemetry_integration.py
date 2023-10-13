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
from tempest.lib.common.utils import data_utils
from tempest.scenario import manager

from telemetry_tempest_plugin.scenario import utils

TEST_DIR = os.path.join(os.path.dirname(__file__),
                        'telemetry_integration_gabbits')


class TestTelemetryIntegration(manager.ScenarioTest):
    credentials = ['admin', 'primary']

    TIMEOUT_SCALING_FACTOR = 5

    @classmethod
    def skip_checks(cls):
        super(TestTelemetryIntegration, cls).skip_checks()
        for name in ["aodh", "gnocchi", "nova", "heat",
                     "ceilometer", "glance"]:
            cls._check_service(name)

    @classmethod
    def _check_service(cls, name):
        if not getattr(config.CONF.service_available, name, False):
            raise cls.skipException("%s support is required" %
                                    name.capitalize())

    @staticmethod
    def _get_endpoint(auth, service):
        opt_section = getattr(config.CONF, service)
        endpoint_type = opt_section.endpoint_type
        is_keystone_v3 = 'catalog' in auth[1]

        if is_keystone_v3:
            if endpoint_type.endswith("URL"):
                endpoint_type = endpoint_type[:-3]
            catalog = auth[1]['catalog']
            endpoints = [e['endpoints'] for e in catalog
                         if e['type'] == opt_section.catalog_type]
            if not endpoints:
                raise Exception("%s endpoint not found" %
                                opt_section.catalog_type)
            endpoints = [e['url'] for e in endpoints[0]
                         if e['interface'] == endpoint_type]
            if not endpoints:
                raise Exception("%s interface not found for endpoint %s" %
                                (endpoint_type,
                                 opt_section.catalog_type))
            return endpoints[0].rstrip('/')

        else:
            if not endpoint_type.endswith("URL"):
                endpoint_type += "URL"
            catalog = auth[1]['serviceCatalog']
            endpoints = [e for e in catalog
                         if e['type'] == opt_section.catalog_type]
            if not endpoints:
                raise Exception("%s endpoint not found" %
                                opt_section.catalog_type)
            return endpoints[0]['endpoints'][0][endpoint_type].rstrip('/')

    def _prep_test(self, filename):
        admin_auth = self.os_admin.auth_provider.get_auth()
        auth = self.os_primary.auth_provider.get_auth()
        networks = self.os_primary.networks_client.list_networks(
            **{'router:external': False, 'fields': 'id'})['networks']

        os.environ.update({
            "ADMIN_TOKEN": admin_auth[0],
            "USER_TOKEN": auth[0],
            "CEILOMETER_METRIC_NAME":
            config.CONF.telemetry.alarm_metric_name,
            "GNOCCHI_AGGREGATION_METHOD":
            config.CONF.telemetry.alarm_aggregation_method,
            "AODH_THRESHOLD": str(config.CONF.telemetry.alarm_threshold),
            "AODH_GRANULARITY": str(config.CONF.telemetry.alarm_granularity),
            "AODH_SERVICE_URL": self._get_endpoint(auth, "alarming_plugin"),
            "GNOCCHI_SERVICE_URL": self._get_endpoint(auth, "metric"),
            "HEAT_SERVICE_URL": self._get_endpoint(auth, "heat_plugin"),
            "NOVA_SERVICE_URL": self._get_endpoint(auth, "compute"),
            "GLANCE_SERVICE_URL": self._get_endpoint(auth, "image"),
            "SG_CORE_SERVICE_URL":
            str(config.CONF.telemetry.sg_core_service_url),
            "GLANCE_IMAGE_NAME": self.image_create(),
            "NOVA_FLAVOR_REF": config.CONF.compute.flavor_ref,
            "NEUTRON_NETWORK": networks[0].get('id'),
            "STACK_NAME": data_utils.rand_name('telemetry'),
        })


utils.generate_tests(TestTelemetryIntegration, TEST_DIR)
