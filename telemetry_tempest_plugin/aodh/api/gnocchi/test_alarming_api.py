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


class TelemetryAlarmingAPIGnocchiTest(base.BaseAlarmingTest):

    @classmethod
    def skip_checks(cls):
        """This section is used to evaluate config early

        Skip all test methods based on these checks
        """

        super(TelemetryAlarmingAPIGnocchiTest, cls).skip_checks()
        if 'gnocchi' not in CONF.telemetry_services.metric_backends:
            msg = ("%s: Skipping Gnocchi specific tests withouth Gnocchi" %
                   cls.__name__)
            raise cls.skipException(msg)

    @decorators.idempotent_id('0024ca4b-3894-485a-bb4b-8d86e4714b48')
    def test_create_update_get_delete_alarm(self):
        # Create an alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        body = self.alarming_client.create_alarm(
            name=alarm_name,
            alarm_actions=['http://no.where'],
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule
        )
        self.assertEqual(alarm_name, body['name'])
        alarm_id = body['alarm_id']
        self.assertDictContainsSubset(
            rule,
            body['gnocchi_aggregation_by_metrics_threshold_rule'])

        # Update alarm with same rule and name
        body = self.alarming_client.update_alarm(
            alarm_id,
            name=alarm_name,
            alarm_actions=['http://no.where'],
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)
        self.assertEqual(alarm_name, body['name'])
        self.assertDictContainsSubset(
            rule,
            body['gnocchi_aggregation_by_metrics_threshold_rule'])

        # Update alarm with new rule and new name
        new_rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                                'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                    'aggregation_method': 'mean',
                    'comparison_operator': 'eq',
                    'threshold': 150.0}
        alarm_name_updated = data_utils.rand_name('telemetry-alarm-update')
        body = self.alarming_client.update_alarm(
            alarm_id,
            name=alarm_name_updated,
            alarm_actions=['http://no.where'],
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=new_rule)
        self.assertEqual(alarm_name_updated, body['name'])
        self.assertDictContainsSubset(
            new_rule,
            body['gnocchi_aggregation_by_metrics_threshold_rule'])

        # Update severity
        body = self.alarming_client.update_alarm(
            alarm_id,
            name=alarm_name_updated,
            alarm_actions=['http://no.where'],
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=new_rule,
            severity='low')

        # Get and verify details of an alarm after update
        body = self.alarming_client.show_alarm(alarm_id)
        self.assertEqual(alarm_name_updated, body['name'])
        self.assertDictContainsSubset(
            new_rule,
            body['gnocchi_aggregation_by_metrics_threshold_rule'])
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
        query = ['type', 'eq', 'gnocchi_aggregation_by_metrics_threshold']
        body = self.alarming_client.list_alarms(query)
        self.assertNotEqual(0, len(body))
        self.assertEqual(set(['gnocchi_aggregation_by_metrics_threshold']),
                         set(alarm['type'] for alarm in body))

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)

    @decorators.idempotent_id('c4486c22-cf8a-4e47-9168-22b92f3499f6')
    def test_get_capabilities(self):

        response = self.alarming_client.show_capabilities()
        self.assertIsNotNone(response)
        self.assertNotEqual({}, response)
        self.assertIn('api', response)
        self.assertIn('alarm_storage', response)

    @decorators.idempotent_id('a45a95f6-7855-4dbc-a507-af0f48cc3370')
    def test_create_n_delete_alarm_duplicate_actions(self):
        # create dual actions
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        body = self.alarming_client.create_alarm(
            name=alarm_name,
            alarm_actions=['http://no.where', 'http://no.where'],
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule
        )
        alarm_id = body['alarm_id']
        alarms = self.alarming_client.list_alarms(['name', 'eq', alarm_name])
        self.assertEqual(1, len(alarms))
        self.assertEqual(['http://no.where'], alarms[0]['alarm_actions'])

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)
