# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

from oslo_config import cfg
from oslo_config import types


service_option = [cfg.BoolOpt('ceilometer',
                              default=True,
                              help="Whether or not Ceilometer is expected to"
                                   "be available"),
                  cfg.BoolOpt("aodh",
                              default=True,
                              help="Whether or not Aodh is expected to be"
                                   "available",
                              deprecated_opts=[cfg.DeprecatedOpt(
                                  'aodh_plugin',
                                  group='service_available')]),
                  cfg.BoolOpt('gnocchi',
                              default=True,
                              help="Whether or not Gnocchi is expected to be"
                                   "available",
                              deprecated_for_removal=True),
                  cfg.BoolOpt('sg_core',
                              default=False,
                              help="Whether or not sg-core is expected to be"
                                   "available",
                              deprecated_for_removal=True)]

telemetry_group = cfg.OptGroup(name='telemetry',
                               title='Telemetry Service Options')

telemetry_services_group = cfg.OptGroup(name='telemetry_services',
                                        title='Telemetry Services')

event_group = cfg.OptGroup(name='event',
                           title='Event Service Options')

alarming_group = cfg.OptGroup(name='alarming_plugin',
                              title='Alarming Service Options')

metric_group = cfg.OptGroup(name='metric',
                            title='Metric Service Options')

TelemetryGroup = [
    cfg.IntOpt('notification_wait',
               default=120,
               help="The seconds to wait for notifications which "
                    "containers and objects sent to swift."),
    cfg.IntOpt('notification_sleep',
               default=1,
               help="The seconds to sleep after an unsuccessful "
                    "notification received."),
    cfg.IntOpt('alarm_granularity',
               default=300,
               help="Granularity to use for aodh alarms. This must match the "
                    "configured Gnocchi archive policy"),
    cfg.StrOpt('alarm_metric_name',
               default="cpu",
               help="Name of the metric to create an alarm on."),
    cfg.StrOpt('alarm_aggregation_method',
               default="rate:mean",
               help="Aggregation method to use for alarm."),
    cfg.IntOpt('alarm_threshold',
               default=10,
               help="Threshold to cross for the alarm to trigger."),
    cfg.BoolOpt("disable_ssl_certificate_validation",
                default=False,
                help="Disable SSL certificate validation when running "
                     "scenario tests"),
    cfg.StrOpt('sg_core_service_url',
               default="127.0.0.1:3000",
               help="URL to sg-core prometheus endpoint"),
    cfg.IntOpt('ceilometer_polling_interval',
               default=300,
               help="Polling interval configured for ceilometer. This can "
                    "be used in test cases to wait for metrics to appear.")
]

telemetry_services_opts = [
    cfg.ListOpt('metric_backends',
                default=[],
                item_type=types.String(choices=['gnocchi', 'prometheus']),
                help="Backend store used to store metrics"),
    cfg.StrOpt('alarm_backend',
               default='mysql',
               choices=['mysql', 'postgresql'],
               help="Database used by the aodh service"),
]

event_opts = [
    cfg.StrOpt('catalog_type',
               default='event',
               help="Catalog type of the Event service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the event service."),
]

AlarmingGroup = [
    cfg.StrOpt('catalog_type',
               default='alarming',
               help="Catalog type of the Alarming service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the alarming service."),
    cfg.BoolOpt('create_alarms',
                default=True,
                help="If create alarms dynamically before testing."),
]

metric_opts = [
    cfg.StrOpt('catalog_type',
               default='metric',
               help="Catalog type of the Metric service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the metric service."),
]
