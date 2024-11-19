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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from telemetry_tempest_plugin.aodh.api import base

CONF = config.CONF


class TelemetryAlarmingAPIAdminTest(base.BaseAlarmingAdminTest):

    @classmethod
    def resource_setup(cls):
        super(TelemetryAlarmingAPIAdminTest, cls).resource_setup()

        if CONF.alarming_plugin.create_alarms:
            cls.rule = {
                "event_type": "compute.instance.*",
                "query": [
                    {"field": "traits.name",
                     "type": "string",
                     "op": "eq",
                     "value": "test"}]
            }
            for i in range(2):
                cls.create_alarm(event_rule=cls.rule)

    @decorators.idempotent_id('1c918e06-210b-41eb-bd45-14676dd77cd7')
    def test_alarm_list(self):
        # List alarms
        alarm_list = self.admin_client.list_alarms(query=['all_projects',
                                                          'eq',
                                                          'true'])

        # Verify created alarm in the list
        fetched_ids = [a['alarm_id'] for a in alarm_list]
        missing_alarms = [a for a in self.alarm_ids if a not in fetched_ids]
        self.assertEqual(0, len(missing_alarms),
                         "Failed to find the following created alarm(s)"
                         " in a fetched list: %s" %
                         ', '.join(str(a) for a in missing_alarms))

    @decorators.idempotent_id('f9966992-405d-475c-aa41-47213cecdf94')
    def test_alarm_create_set_log_test_actions(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        alarm_actions = ['test://', 'log://']
        body = self.admin_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule,
            alarm_actions=alarm_actions)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertLessEqual(self.rule.items(), body['event_rule'].items())
        self.assertEqual(['test:', 'log:'], body['alarm_actions'])

        # Verify not seen by non-admin
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

        # Delete alarm and verify if deleted
        self.admin_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.admin_client.show_alarm, alarm_id)

    @decorators.idempotent_id('5d9f41d4-febc-47a8-a9cb-29ef77229e7b')
    def test_alarm_update_and_delete(self):
        # Create an alarm as normal user
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body = self.alarming_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertLessEqual(self.rule.items(), body['event_rule'].items())

        # Verify initial state as non-admin
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual("insufficient data", body['state'])
        self.assertEqual("Not evaluated yet", body['state_reason'])

        # Verify initial state as admin
        body = self.admin_client.show_alarm(alarm_id)
        self.assertEqual("insufficient data", body['state'])
        self.assertEqual("Not evaluated yet", body['state_reason'])

        # Update state and verify as admin
        self.admin_client.alarm_set_state(alarm_id, state='ok')
        body = self.admin_client.show_alarm(alarm_id)
        self.assertEqual('ok', body['state'])
        self.assertEqual('Manually set via API', body['state_reason'])

        # Verify state as non-admin
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual('ok', body['state'])
        self.assertEqual('Manually set via API', body['state_reason'])

        # Delete alarm as admin and verify if deleted
        self.admin_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.admin_client.show_alarm, alarm_id)
