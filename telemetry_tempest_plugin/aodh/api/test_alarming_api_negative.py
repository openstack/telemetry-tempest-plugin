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

import datetime

from oslo_utils import uuidutils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from telemetry_tempest_plugin.aodh.api import base


class TelemetryAlarmingNegativeTest(base.BaseAlarmingTest):
    """Negative tests for show_alarm, update_alarm, show_alarm_history tests

        ** show non-existent alarm
        ** show the deleted alarm
        ** delete deleted alarm
        ** update deleted alarm
    """

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('668743d5-08ad-4480-b2b8-15da34f81e7e')
    def test_get_non_existent_alarm(self):
        # get the non-existent alarm
        non_existent_id = uuidutils.generate_uuid()
        self.assertRaises(lib_exc.NotFound, self.alarming_client.show_alarm,
                          non_existent_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d6adbf73-03ca-4730-b1d7-13233475d271')
    def test_get_non_existent_alarm_timestamp(self):
        # list invalid query
        date_time = datetime.datetime(2012, 7, 2, 10, 41)
        isotime = date_time.isoformat()
        query = ['timestamp', 'gt', isotime]
        self.assertRaises(lib_exc.BadRequest, self.alarming_client.list_alarms,
                          query)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f6f9e0a3-9623-43bb-a39a-284073c38b1f')
    def test_get_alarms_all_projects(self):
        # don't get alarms from all projects
        query = ['all_projects', 'eq', 'true']
        self.assertRaises(lib_exc.Forbidden, self.alarming_client.list_alarms,
                          query)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b3f61233-92f6-4402-a98d-fd5858379949')
    def test_get_alarms_invalid_op(self):
        # fail on op
        query = ['project_id', 'ne', 'b3f61233-92f6-4402-a98d-fd5858379949']
        self.assertRaises(lib_exc.BadRequest, self.alarming_client.list_alarms,
                          query)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7373e681-8e11-4071-a955-aa9582bef914')
    def test_create_invalid_alarm_input_type(self):
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
            type='bad_type',
            bad_type_rule=rule)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6d3f39dd-64ee-438d-804e-f193dc2c7d4b')
    def test_list_invalid_project(self):
        # Get invalid paths
        self.assertRaises(
            lib_exc.Unauthorized,
            self.alarming_client.list_alarms,
            ['project_id', 'eq', 'other-project'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c4718d72-3091-4965-b3f2-6d6c2375d26a')
    def test_list_non_existing_history(self):
        # Get invalid paths
        alarm_id = data_utils.rand_name('aid')
        self.assertRaises(
            lib_exc.NotFound,
            self.alarming_client.show_alarm_history,
            alarm_id=alarm_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('350dae2b-8720-48ae-b3a6-d92dbba55d07')
    def test_list_invalid_sort_key(self):
        # list with invalid sort key
        self.assertRaises(
            lib_exc.BadRequest,
            self.alarming_client.list_alarms,
            sort=['invalid_key:asc'])
