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
import requests
import time

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.scenario import manager

from telemetry_tempest_plugin.scenario import utils


TEST_DIR = os.path.join(os.path.dirname(__file__),
                        'telemetry_integration_prometheus_gabbits')


class PrometheusGabbiTest(manager.ScenarioTest):
    credentials = ['admin', 'primary']

    TIMEOUT_SCALING_FACTOR = 5

    @classmethod
    def resource_setup(cls):
        cls.stack_name = data_utils.rand_name("telemetry")

    @classmethod
    def skip_checks(cls):
        super(PrometheusGabbiTest, cls).skip_checks()
        for name in ["aodh", "nova", "heat",
                     "ceilometer", "glance", "sg_core"]:
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

        super(PrometheusGabbiTest, cls).resource_cleanup()

    def _prep_query(self, prometheus_rate_duration, resource_prefix):
        if config.CONF.telemetry.autoscaling_instance_grouping == "metadata":
            query = ("\"(rate(ceilometer_cpu{{server_group=~'stack_id'}}"
                     "[{}s])) * 100\"").format(prometheus_rate_duration)
            metadata_query = '''
            {{
                "str_replace": {{
                    "template": {},
                    "params": {{
                        "stack_id": {{ "get_param": "OS::stack_id" }}
                    }}
                }}
            }}
            '''.format(query)
            return metadata_query

        else:
            prefix_query = '''
            "(rate(ceilometer_cpu{{resource_name=~'te-{}.*'}}[{}s])) * 100"
            '''.format(resource_prefix, prometheus_rate_duration)
            return prefix_query

    def _prep_test(self, filename):
        auth = self.os_primary.auth_provider.get_auth()
        networks = self.os_primary.networks_client.list_networks(
            **{'router:external': False, 'fields': 'id'})['networks']
        # NOTE(marihan): This is being used in prometheus query as heat is
        # using the last 7 digits from stack_name to create the autoscaling
        # resources.
        resource_prefix = self.stack_name[-7:]
        prometheus_rate_duration = (
            config.CONF.telemetry.ceilometer_polling_interval
            + config.CONF.telemetry.prometheus_scrape_interval)
        query = self._prep_query(prometheus_rate_duration, resource_prefix)
        os.environ.update({
            "USER_TOKEN": auth[0],
            "AODH_THRESHOLD": str(config.CONF.telemetry.alarm_threshold),
            "SCALEDOWN_THRESHOLD":
            str(config.CONF.telemetry.scaledown_alarm_threshold),
            "AODH_SERVICE_URL": self._get_endpoint(auth, "alarming_plugin"),
            "HEAT_SERVICE_URL": self._get_endpoint(auth, "heat_plugin"),
            "NOVA_SERVICE_URL": self._get_endpoint(auth, "compute"),
            "SG_CORE_SERVICE_URL":
            config.CONF.telemetry.sg_core_service_url,
            "CEILOMETER_POLLING_INTERVAL":
            str(config.CONF.telemetry.ceilometer_polling_interval),
            "PROMETHEUS_SERVICE_URL":
            config.CONF.telemetry.prometheus_service_url,
            "GLANCE_IMAGE_NAME": self.image_create(),
            "NOVA_FLAVOR_REF": config.CONF.compute.flavor_ref,
            "NEUTRON_NETWORK": networks[0].get('id'),
            "STACK_NAME": self.stack_name,
            "RESOURCE_PREFIX": resource_prefix,
            "PROMETHEUS_RATE_DURATION": str(prometheus_rate_duration),
            "LOAD_LENGTH": str(prometheus_rate_duration * 2),
            "QUERY": query,
        })


utils.generate_tests(PrometheusGabbiTest, TEST_DIR)
