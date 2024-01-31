#    Copyright 2015 GlobalLogic.  All rights reserved.
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

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from telemetry_tempest_plugin.aodh.api import base

CONF = config.CONF


class TelemetryAlarmingNegativeGnocchiTest(base.BaseAlarmingTest):
    """Negative tests for show_alarm, update_alarm, show_alarm_history tests

        ** show non-existent alarm
        ** show the deleted alarm
        ** delete deleted alarm
        ** update deleted alarm
    """

    @classmethod
    def skip_checks(cls):
        """This section is used to evaluate config early

        Skip all test methods based on these checks
        """

        super(TelemetryAlarmingNegativeGnocchiTest, cls).skip_checks()
        if 'gnocchi' not in CONF.telemetry_services.metric_backends:
            msg = ("%s: Skipping Gnocchi specific tests withouth Gnocchi" %
                   cls.__name__)
            raise cls.skipException(msg)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ef45000d-0a72-4781-866d-4cb7bf2582ae')
    def test_get_update_show_history_delete_deleted_alarm(self):
        # get, update and delete the deleted alarm
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ["c0d457b6-957e-41de-a384-d5eb0957de3b"],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 100.0,
                'granularity': 90}
        body = self.alarming_client.create_alarm(
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)
        alarm_id = body['alarm_id']
        self.alarming_client.delete_alarm(alarm_id)
        # get the deleted alarm
        self.assertRaises(lib_exc.NotFound, self.alarming_client.show_alarm,
                          alarm_id)

        # update the deleted alarm
        updated_alarm_name = data_utils.rand_name('telemetry_alarm_updated')
        updated_rule = {'metrics': ["c0d457b6-957e-41de-a384-d5eb0957de3b"],
                        'comparison_operator': 'eq',
                        'aggregation_method': 'mean',
                        'threshold': 70,
                        'granularity': 50}
        self.assertRaises(
            lib_exc.NotFound, self.alarming_client.update_alarm,
            alarm_id,
            gnocchi_aggregation_by_metrics_threshold_rule=updated_rule,
            name=updated_alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold')
        # delete the deleted alarm
        self.assertRaises(lib_exc.NotFound, self.alarming_client.delete_alarm,
                          alarm_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3bd874d7-dcbf-410e-ab08-829969282d92')
    def test_create_invalid_alarm_constraint_start(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        tc_name = data_utils.rand_name('time_constraint')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        tc = [{'name': tc_name,
               'start': '11:00am',
               'duration': 10}]
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.skip_because(bug="2045115")
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('384dec5a-af5b-4a9e-8dc1-9d056fca71d6')
    def test_create_null_alarm_constraint(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        tc = None
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f358ee93-798e-4641-8fdc-13dc2f7a71c5')
    def test_create_duplicate_alarm_constraint_name(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        tc_name = data_utils.rand_name('time_constraint')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        tc = [{'name': tc_name,
               'start': '* 11 * * *',
               'duration': 10},
              {'name': tc_name,
               'start': '* * * * *',
               'duration': 20}]
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e1d5d605-61a0-415b-bcaf-dc3a15717344')
    def test_create_invalid_alarm_constraint_timezone(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        tc_name = data_utils.rand_name('time_constraint')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        tc = [{'name': tc_name,
               'start': '* 11 * * *',
               'duration': 10,
               'timezone': 'aaaa'}]
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7d3ee20c-8a0f-4a43-8a1a-2168da9905da')
    def test_create_invalid_alarm_constraint_duration(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        tc_name = data_utils.rand_name('time_constraint')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        tc = [{'name': tc_name,
               'start': '* 11 * * *',
               'duration': -10}]
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('21ab2919-8680-44d8-be90-57aac5b22474')
    def test_create_invalid_alarm_rule_granularity(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        tc_name = data_utils.rand_name('time_constraint')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0,
                'granularity': -1}
        tc = [{'name': tc_name,
               'start': '* 11 * * *',
               'duration': 10}]
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b942eeb3-7fc2-4ba4-ad8f-674f3ac7fb96')
    def test_create_invalid_alarm_none_rule(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        tc_name = data_utils.rand_name('time_constraint')
        rule = None
        tc = [{'name': tc_name,
               'start': '* 11 * * *',
               'duration': -10}]
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            time_constraints=tc,
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a805f2f3-ea3e-4574-b616-3dbe86cb95f8')
    def test_create_invalid_alarm_input_state(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            state='bad_state',
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ea90ef4a-135d-48f2-b984-c156a89f627c')
    def test_create_invalid_alarm_input_severity(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            state='ok',
            severity='bad_value',
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3af990af-f134-4b87-9234-a25280afc176')
    def test_create_invalid_alarm_input_enabled_string(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            state='ok',
            enabled='bad_value',
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.skip_because(bug="2045118")
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('db999b7e-3bc8-4be3-90f3-9d0034f61e8a')
    def test_create_invalid_alarm_input_enabled_int(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'mean',
                'comparison_operator': 'eq',
                'threshold': 300.0}
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            state='ok',
            enabled=0,
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0c64f10f-8529-46a5-9172-f0a64789632f')
    def test_create_invalid_alarm_statistic(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'aggregation_method': 'magic',
                'comparison_operator': 'gt',
                'threshold': 2.0}
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0c421fe7-69e9-4a7c-9df0-547f7bc4c91a')
    def test_create_invalid_alarm_com_op(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule = {'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'comparison_operator': 'bd_co',
                'threshold': 20.0}
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type='gnocchi_aggregation_by_metrics_threshold',
            gnocchi_aggregation_by_metrics_threshold_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5bbccedd-dd80-462c-a6da-d796d7667b5e')
    def test_create_alarm_wsme_workaround(self):
        # create bad time constraint
        alarm_name = data_utils.rand_name('telemetry_alarm')
        rule_key = 'gnocchi_aggregation_by_metrics_threshold_rule'
        rules = {
            'type': {
                'name': alarm_name,
                rule_key: {
                    'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                                'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                    'aggregation_method': 'mean',
                    'threshold': 2.0,
                }
            },
            'name': {
                'type': 'gnocchi_aggregation_by_metrics_threshold',
                rule_key: {
                    'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                                'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                    'aggregation_method': 'mean',
                    'threshold': 2.0,
                }
            },
            'threshold_rule/metrics': {
                'name': alarm_name,
                'type': 'gnocchi_aggregation_by_metrics_threshold',
                rule_key: {
                    'aggregation_method': 'mean',
                    'threshold': 2.0,
                }
            },
            'threshold_rule/threshold': {
                'name': alarm_name,
                'type': 'gnocchi_aggregation_by_metrics_threshold',
                rule_key: {
                    'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                                'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                    'aggregation_method': 'mean',
                }
            },
        }

        for field, adef in rules.items():
            self.assertRaises(
                lib_exc.BadRequest,
                self.alarming_client.create_alarm,
                name=getattr(adef, 'name', None),
                type=getattr(adef, 'type', None),
                gnocchi_aggregation_by_metrics_threshold_rule=adef[rule_key]
                )

    def _do_create_alarm_invalid_action(self, ok_actions=None,
                                        alarm_actions=None,
                                        insufficient_data_actions=None,
                                        error_message=None):

        ok_actions = ok_actions or []
        alarm_actions = alarm_actions or []
        insufficient_data_actions = insufficient_data_actions or []
        rule_key = 'gnocchi_aggregation_by_metrics_threshold_rule'
        alarm_name = data_utils.rand_name('telemetry_alarm')
        adef = {
            'enabled': False,
            'state': 'ok',
            'type': 'gnocchi_aggregation_by_metrics_threshold',
            'ok_actions': ok_actions,
            'alarm_actions': alarm_actions,
            'insufficient_data_actions': insufficient_data_actions,
            'repeat_actions': True,
            rule_key: {
                'metrics': ['41869681-5776-46d6-91ed-cccc43b6e4e3',
                            'a1fb80f4-c242-4f57-87c6-68f47521059e'],
                'comparison_operator': 'le',
                'aggregation_method': 'count',
                'threshold': 50,
                'evaluation_periods': '3',
                'granularity': '180',
            }
        }
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.create_alarm,
            name=alarm_name,
            type=adef['type'],
            enabled=adef['enabled'],
            state=adef['state'],
            ok_actions=adef['ok_actions'],
            alarm_actions=adef['alarm_actions'],
            insufficient_data_actions=adef['insufficient_data_actions'],
            repeat_actions=adef['repeat_actions'],
            gnocchi_aggregation_by_metrics_threshold_rule=adef[rule_key])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('95e505c3-51e0-4ac8-8e75-6dfb5828fcd2')
    def test_create_invalid_alarm_ok_actions(self):
        self._do_create_alarm_invalid_action(
            ok_actions=['spam://something/ok'],
            error_message='Unsupported action spam://something/ok')

    @decorators.skip_because(bug="2045116")
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4b2b7be0-9d13-4e36-ad28-d11c5aa06411')
    def test_create_invalid_alarm_too_many_actions(self):
        self._do_create_alarm_invalid_action(
            ok_actions=['http://no.where', 'http://no.where2'],
            error_message="alarm_actions count exceeds maximum value 1")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('2332b637-8193-448c-8b37-e0b6a6fded34')
    def test_post_invalid_alarm_alarm_actions(self):
        self._do_create_alarm_invalid_action(
            alarm_actions=['spam://something/alarm'],
            error_message='Unsupported action spam://something/alarm')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('78029ec7-cb70-4f89-a1b6-df235d6688b6')
    def test_post_invalid_alarm_insufficient_data_actions(self):
        self._do_create_alarm_invalid_action(
            insufficient_data_actions=['spam://something/insufficient'],
            error_message='Unsupported action spam://something/insufficient')

    @decorators.attr(type='negative')
    @decorators.idempotent_id('32bbc39e-7423-4309-acf9-39ff584764fc')
    def test_create_update_with_faults_delete_alarm(self):
        # create dual actions
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
        alarm_id = body['alarm_id']
        alarms = self.alarming_client.list_alarms(['name', 'eq', alarm_name])
        self.assertEqual(1, len(alarms))

        # update the alarm with wrong fields.
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.update_alarm,
            alarm_id=alarm_id,
            this_can_not_be_correct='ha')

        # update the alarm with invalid action
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.update_alarm,
            alarm_id=alarm_id,
            ok_actions='spam://something/ok')

        # update the alarm with invalid state
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.alarm_set_state,
            alarm_id=alarm_id,
            state='not valid')

        # Delete alarm and verify if deleted
        self.alarming_client.delete_alarm(alarm_id)
        self.assertRaises(lib_exc.NotFound,
                          self.alarming_client.show_alarm, alarm_id)
