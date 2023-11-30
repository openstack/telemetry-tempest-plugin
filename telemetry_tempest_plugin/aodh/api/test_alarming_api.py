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


class TelemetryAlarmingAPITest(base.BaseAlarmingTest):

    @classmethod
    def resource_setup(cls):
        super(TelemetryAlarmingAPITest, cls).resource_setup()

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
        alarm_list = self.alarming_client.list_alarms()

        # Verify created alarm in the list
        fetched_ids = [a['alarm_id'] for a in alarm_list]
        missing_alarms = [a for a in self.alarm_ids if a not in fetched_ids]
        self.assertEqual(0, len(missing_alarms),
                         "Failed to find the following created alarm(s)"
                         " in a fetched list: %s" %
                         ', '.join(str(a) for a in missing_alarms))

    @decorators.idempotent_id('1297b095-39c1-4e74-8a1f-4ae998cedd68')
    def test_create_update_get_delete_alarm(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body = self.alarming_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(self.rule, body['event_rule'])

        # Update alarm with same rule and name
        body = self.alarming_client.update_alarm(
            alarm_id,
            event_rule=self.rule,
            name=alarm_name,
            type='event')
        self.assertEqual(alarm_name, body['name'])
        self.assertDictContainsSubset(self.rule, body['event_rule'])

        # Update alarm with new rule and new name
        new_rule = {
            "event_type": "compute.instance.create",
            "query": [
                {"field": "traits.name",
                 "type": "string",
                 "op": "eq",
                 "value": "test"}]
        }
        alarm_name_updated = data_utils.rand_name('telemetry-alarm-update')
        body = self.alarming_client.update_alarm(
            alarm_id,
            event_rule=new_rule,
            name=alarm_name_updated,
            type='event')
        self.assertEqual(alarm_name_updated, body['name'])
        self.assertDictContainsSubset(new_rule, body['event_rule'])

        # Update severity
        body = self.alarming_client.update_alarm(
            alarm_id,
            event_rule=new_rule,
            name=alarm_name_updated,
            type='event',
            severity='low')

        # Get and verify details of an alarm after update
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual(alarm_name_updated, body['name'])
        self.assertDictContainsSubset(new_rule, body['event_rule'])
        self.assertEqual('low', body['severity'])

        # Get history for the alarm and verify the same
        body = self.alarming_client.show_alarm_history(alarm_id)
        self.assertEqual("rule change", body[0]['type'])
        self.assertIn(alarm_name_updated, body[0]['detail'])
        self.assertEqual("creation", body[1]['type'])
        self.assertIn(alarm_name, body[1]['detail'])

        # Query by state and verify
        query = ['state', 'eq', 'insufficient data']
        body = self.alarming_client.list_alarms(query)
        self.assertNotEqual(0, len(body))
        self.assertEqual(set(['insufficient data']),
                         set(alarm['state'] for alarm in body))

        # Query by type and verify
        query = ['type', 'eq', 'event']
        body = self.alarming_client.list_alarms(query)
        self.assertNotEqual(0, len(body))
        self.assertEqual(set(['event']), set(alarm['type'] for alarm in body))

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

    @decorators.idempotent_id('b666f7d5-ce8c-4b2d-887e-15993433c2e9')
    def test_create_query_delete_disabled_alarm(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body = self.alarming_client.create_alarm(
            name=alarm_name, type='event', enabled=False,
            event_rule=self.rule)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(self.rule, body['event_rule'])
        self.assertFalse(body['enabled'])

        # Query by enabled false and verify
        query = ['enabled', 'eq', 'false']
        body = self.alarming_client.list_alarms(query)
        self.assertNotEqual(0, len(body))
        self.assertEqual(set([False]),
                         set(alarm['enabled'] for alarm in body))

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

    @decorators.idempotent_id('bf44b72f-0384-4b34-ab78-bdfd3bf1b16c')
    def test_create_delete_alarm_defaults(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body = self.alarming_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(self.rule, body['event_rule'])

        # Verify default
        expected_defaults = {
            'enabled': True,
            'ok_actions': [],
            'alarm_actions': [],
            'insufficient_data_actions': [],
            'repeat_actions': False,
        }
        for key in expected_defaults:
            self.assertEqual(expected_defaults[key], body[key])

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

    @decorators.idempotent_id('0a883365-7158-4dbb-a946-3b07dc171c93')
    def test_create_excercise_delete_alarm_state(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body = self.alarming_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule)
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(self.rule, body['event_rule'])

        # Verify initial state
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual("insufficient data", body['state'])
        self.assertEqual("Not evaluated yet", body['state_reason'])

        # Update state and verify
        self.alarming_client.alarm_set_state(alarm_id, state='ok')
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual('ok', body['state'])
        self.assertEqual('Manually set via API', body['state_reason'])

        # Update state and verify reason read only
        body['state'] = 'alarm'
        body['state_reason'] = 'Oops!'
        self.alarming_client.update_alarm(**body)
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual('alarm', body['state'])
        self.assertEqual('Manually set via API', body['state_reason'])

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

    @decorators.idempotent_id('ced16dd6-cbd8-4a2b-a9c3-aed6e4a7102c')
    def test_create_query_delete_alarm_same_name(self):
        # Create two alarms with same name
        alarm_name = data_utils.rand_name('telemetry_alarm')
        body1 = self.alarming_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule)
        body2 = self.alarming_client.create_alarm(
            name=alarm_name, type='event',
            event_rule=self.rule)
        alarm1_id = body1['alarm_id']
        alarm2_id = body2['alarm_id']
        self.assertEqual(alarm_name, body1['name'])
        self.assertEqual(alarm_name, body2['name'])
        self.assertNotEqual(alarm1_id, alarm2_id)

        # Query by name and verify
        query = ['name', 'eq', alarm_name]
        body = self.alarming_client.list_alarms(query)
        self.assertEqual(2, len(body))
        self.assertEqual(set([alarm_name]),
                         set(alarm['name'] for alarm in body))

        # Delete alarms and verify if deleted
        self.alarming_client.delete_alarm(alarm1_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm1_id)
        self.alarming_client.delete_alarm(alarm2_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm2_id)

    @decorators.idempotent_id('aca49486-70bb-4016-87e0-f6131374f742')
    def test_set_get_alarm_state(self):
        alarm_states = ['ok', 'alarm', 'insufficient data']
        alarm = self.create_alarm(event_rule=self.rule)

        # Set alarm state and verify
        new_state =\
            [elem for elem in alarm_states if elem != alarm['state']][0]
        state = self.alarming_client.alarm_set_state(alarm['alarm_id'],
                                                     new_state)

        self.assertEqual(new_state, state.data)
        # Get alarm state and verify
        state = self.alarming_client.show_alarm_state(alarm['alarm_id'])
        self.assertEqual(new_state, state.data)

    @decorators.idempotent_id('0cc2f5d1-6f48-4274-bfa8-f62f82eab6ed')
    def test_get_capabilities(self):

        response = self.alarming_client.show_capabilities()
        self.assertIsNotNone(response)
        self.assertNotEqual({}, response)
        self.assertIn('api', response)
        self.assertIn('alarm_storage', response)

    @decorators.idempotent_id('d42d0103-0497-4109-9746-dacaa17e831c')
    def test_get_versions(self):

        response = self.alarming_client.show_version()
        media_types = [
            {
                'base': 'application/json',
                'type': 'application/vnd.openstack.telemetry-v2+json'
            }, {
                'base': 'application/xml',
                'type': 'application/vnd.openstack.telemetry-v2+xml'
            }
        ]
        self.assertIsNotNone(response)
        self.assertNotEqual({}, response)
        self.assertEqual('v2', response['versions']['values'][0]['id'])
        self.assertIn('links', response['versions']['values'][0])
        self.assertEqual(media_types, response['versions']['values'][0][
            'media-types'])
        self.assertIn('status', response['versions']['values'][0])
        self.assertIn('updated', response['versions']['values'][0])

    @decorators.idempotent_id('c1dcefdf-3b96-40d0-8f39-04fc0702ab6b')
    def test_create_n_delete_alarm_rule_loadbalancer(self):
        # create dual actions
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {
            "pool_id": "2177ccd8-b09c-417a-89a0-e8d2419be612",
            "stack_id": "1b974012-ebcb-4888-8ae2-47714d4d2c4d",
            "autoscaling_group_id": "681c9266-61d2-4c9a-ad18-526807f6adc0"
        }
        body = self.alarming_client.create_alarm(
            name=alarm_name,
            type='loadbalancer_member_health',
            loadbalancer_member_health_rule=rule
        )
        alarm_id = body['alarm_id']
        alarms = self.alarming_client.list_alarms(['name', 'eq', alarm_name])
        self.assertEqual(1, len(alarms))

        # Check the actions are empty
        self.assertEqual([], alarms[0]['alarm_actions'])

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

    @decorators.idempotent_id('e1d65c3c-a64d-4968-949c-96f2b2d8b363')
    def test_create_list_sort_limit_delete_alarm(self):
        # create test alarms
        alarms = {}
        for i in range(3):
            alarm_name = data_utils.rand_name('sorted_alarms')
            alarms[alarm_name] = []
            for j in range(random.randint(2, 4)):
                body = self.alarming_client.create_alarm(
                    name=alarm_name, type='event',
                    event_rule=self.rule)
                alarms[alarm_name].append(body['alarm_id'])
        ordered_alarms = []
        for key in sorted(alarms):
            ordered_alarms.extend([(key, a) for a in sorted(alarms[key])])

        # Sort by name and verify
        sort = ['name:asc']
        body = self.alarming_client.list_alarms(sort=sort)
        self.assertEqual([alarm[0] for alarm in ordered_alarms],
                         [alarm['name'] for alarm in body if alarm[
                             'name'].startswith('tempest-sorted_alarms')])
        sort = ['name']
        body = self.alarming_client.list_alarms(sort=sort)
        self.assertEqual([alarm[0] for alarm in ordered_alarms],
                         [alarm['name'] for alarm in body if alarm[
                             'name'].startswith('tempest-sorted_alarms')])

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
