# Copyright 2014 OpenStack Foundation
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

import json

from urllib import parse

from tempest import clients as tempest_clients
from tempest import config
from tempest.lib.common import rest_client
from tempest.lib.services import clients


CONF = config.CONF


class AlarmingClient(rest_client.RestClient):

    version = '2'
    uri_prefix = "v2"

    def deserialize(self, body):
        return json.loads(body.decode('utf-8').replace("\n", ""))

    def serialize(self, body):
        return json.dumps(body)

    def list_alarms(self, query=None, sort=None, limit=None, marker=None):
        uri = '%s/alarms' % self.uri_prefix
        uri_dict = {}
        if query:
            uri_dict = {'q.field': query[0],
                        'q.op': query[1],
                        'q.value': query[2]}
        if sort:
            uri_dict.update({'sort': sort})
        if limit is not None:
            uri_dict.update({'limit': int(limit)})
        if marker:
            uri_dict.update({'marker': marker})
        if uri_dict:
            uri += "?%s" % parse.urlencode(uri_dict, doseq=True)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyList(resp, body)

    def show_alarm(self, alarm_id):
        uri = '%s/alarms/%s' % (self.uri_prefix, alarm_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)

    def show_alarm_history(self, alarm_id):
        uri = "%s/alarms/%s/history" % (self.uri_prefix, alarm_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyList(resp, body)

    def delete_alarm(self, alarm_id):
        uri = "%s/alarms/%s" % (self.uri_prefix, alarm_id)
        resp, body = self.delete(uri)
        self.expected_success(204, resp.status)
        if body:
            body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)

    def create_alarm(self, **kwargs):
        uri = "%s/alarms" % self.uri_prefix
        body = self.serialize(kwargs)
        resp, body = self.post(uri, body)
        self.expected_success(201, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)

    def update_alarm(self, alarm_id, **kwargs):
        uri = "%s/alarms/%s" % (self.uri_prefix, alarm_id)
        body = self.serialize(kwargs)
        resp, body = self.put(uri, body)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)

    def show_alarm_state(self, alarm_id):
        uri = "%s/alarms/%s/state" % (self.uri_prefix, alarm_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyData(resp, body)

    def alarm_set_state(self, alarm_id, state):
        uri = "%s/alarms/%s/state" % (self.uri_prefix, alarm_id)
        body = self.serialize(state)
        resp, body = self.put(uri, body)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyData(resp, body)

    def invalid_path(self, headers=None):
        uri = "invalid_path"
        extra_headers = headers is not None
        resp, body = self.get(uri, headers, extra_headers)
        self.expected_success(404, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyData(resp, body)

    def show_capabilities(self):
        uri = "%s/capabilities" % (self.uri_prefix)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)

    def show_version(self):
        uri = '/'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)


class Manager(clients.ServiceClients):

    default_params = {
        'disable_ssl_certificate_validation':
            CONF.identity.disable_ssl_certificate_validation,
        'ca_certs': CONF.identity.ca_certificates_file,
        'trace_requests': CONF.debug.trace_requests
    }

    alarming_params = {
        'service': CONF.alarming_plugin.catalog_type,
        'region': CONF.identity.region,
        'endpoint_type': CONF.alarming_plugin.endpoint_type,
    }
    alarming_params.update(default_params)

    def __init__(self, credentials=None, service=None):
        dscv = CONF.identity.disable_ssl_certificate_validation
        _, uri = tempest_clients.get_auth_provider_class(credentials)
        super(Manager, self).__init__(
            credentials=credentials,
            identity_uri=uri,
            scope='project',
            disable_ssl_certificate_validation=dscv,
            ca_certs=CONF.identity.ca_certificates_file,
            trace_requests=CONF.debug.trace_requests)
        self.set_alarming_client()

    def set_alarming_client(self):
        self.alarming_client = AlarmingClient(self.auth_provider,
                                              **self.alarming_params)
