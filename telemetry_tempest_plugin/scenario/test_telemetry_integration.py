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
import time

import requests
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
    def resource_setup(cls):
        cls.stack_name = data_utils.rand_name("telemetry")
        networks = cls.os_primary.networks_client
        subnets = cls.os_primary.subnets_client
        cls.stack_network_id = networks.create_network()['network']['id']
        cls.stack_subnet_id = subnets.create_subnet(
            ip_version=4,
            network_id=cls.stack_network_id,
            cidr=config.CONF.network.project_network_cidr
        )['subnet']['id']

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

    @classmethod
    def resource_cleanup(cls):
        headers = {'X-Auth-Token': cls.os_primary.auth_provider.get_auth()[0]}
        url = os.environ['HEAT_SERVICE_URL'] + "/stacks/" + cls.stack_name
        r = requests.get(url, headers=headers)

        if r.status_code == 200 and \
                "stack" in r.json():
            stack = r.json()["stack"]
            stack_url = (f'{os.environ["HEAT_SERVICE_URL"]}/stacks/'
                         f'{stack["stack_name"]}/{stack["id"]}')
            requests.delete(stack_url, headers=headers)

            repeats = 0
            r = requests.get(stack_url, headers=headers)
            while r.json()["stack"]["stack_status"] == \
                    "DELETE_IN_PROGRESS" and repeats < 30:
                time.sleep(2)
                r = requests.get(stack_url, headers=headers)
                repeats += 1
        cls.os_primary.subnets_client.delete_subnet(cls.stack_subnet_id)
        cls.os_primary.networks_client.delete_network(cls.stack_network_id)

        super(TestTelemetryIntegration, cls).resource_cleanup()

    def _prep_test(self, filename):
        admin_auth = self.os_admin.auth_provider.get_auth()
        auth = self.os_primary.auth_provider.get_auth()

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
            "GLANCE_IMAGE_NAME": self.image_create(),
            "NOVA_FLAVOR_REF": config.CONF.compute.flavor_ref,
            "NEUTRON_NETWORK": self.stack_network_id,
            "STACK_NAME": self.stack_name,
        })


utils.generate_tests(TestTelemetryIntegration, TEST_DIR)
