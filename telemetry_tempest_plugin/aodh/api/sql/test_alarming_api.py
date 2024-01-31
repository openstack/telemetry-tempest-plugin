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
import random

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from telemetry_tempest_plugin.aodh.api import base

CONF = config.CONF


class TelemetryAlarmingAPIMysqlTest(base.BaseAlarmingTest):

    @classmethod
    def skip_checks(cls):
        """This section is used to evaluate config early

        Skip all test methods based on these checks
        """

        super(TelemetryAlarmingAPIMysqlTest, cls).skip_checks()
        if CONF.telemetry_services.alarm_backend != 'mysql':
            msg = ("%s: Skipping mysql specific tests withouth mysql" %
                   cls.__name__)
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(TelemetryAlarmingAPIMysqlTest, cls).resource_setup()

        if CONF.alarming_plugin.create_alarms:
            cls.rule = {
                "event_type": "compute.instance.*",
                "query": [
                    {"field": "traits.name",
                     "type": "string",
                     "op": "eq",
                     "value": "test"}]
            }

    @decorators.idempotent_id('2fa9ba1e-6118-4ce7-984c-b5d2c275de55')
    def test_create_list_sort_limit_delete_alarm(self):
        # create test alarms
        alarms = {}
        sevs = ['critical', 'moderate']
        for i in range(3):
            alarm_name = data_utils.rand_name('sorted_alarms')
            alarms[alarm_name] = []
            for j in range(random.randint(2, 4)):
                body = self.alarming_client.create_alarm(
                    name=alarm_name,
                    type='event',
                    severity=random.choice(sevs),
                    event_rule=self.rule)
                alarms[alarm_name].append(body['alarm_id'])
        ordered_alarms = []
        for key in sorted(alarms):
            ordered_alarms.extend([(key, a) for a in sorted(alarms[key])])

        # Sort by severity and verify
        sort = ['severity:asc']
        body = self.alarming_client.list_alarms(sort=sort)
        self.assertEqual(set(sevs),
                         set([alarm['severity'] for alarm in body if alarm[
                             'name'].startswith('tempest-sorted_alarms')]))
        sort = ['severity']
        body = self.alarming_client.list_alarms(sort=sort)
        self.assertEqual(set(sevs),
                         set([alarm['severity'] for alarm in body if alarm[
                             'name'].startswith('tempest-sorted_alarms')]))

        # multiple sorts
        sort = ['name:asc', 'alarm_id:asc']
        body = self.alarming_client.list_alarms(sort=sort)
        name_ids = [(a['name'], a['alarm_id']) for a in body if a[
            'name'].startswith('tempest-sorted_alarms')]
        self.assertEqual(ordered_alarms, name_ids)

        # limit and sort
        sort = ['name:asc', 'alarm_id:asc']
        limit = 2
        body = self.alarming_client.list_alarms(limit=limit)
        self.assertEqual(2, len(body))
        body = self.alarming_client.list_alarms(sort=sort, limit=limit)
        self.assertEqual(2, len(body))
        self.assertEqual([ordered_alarms[0][0], ordered_alarms[1][0]],
                         [body[0]['name'], body[1]['name']])
        body = self.alarming_client.list_alarms(
            sort=sort, marker=ordered_alarms[1][1])
        name_ids = [(a['name'], a['alarm_id']) for a in body if a[
            'name'].startswith('tempest-sorted_alarms')]
        self.assertEqual(ordered_alarms[2:], name_ids)

        # Delete alarms and verify if deleted
        for name, alarm_id in ordered_alarms:
            self.alarming_client.delete_alarm(alarm_id)
            self.assertRaises(lib_exc.NotFound,
                              self.alarming_client.show_alarm, alarm_id)
