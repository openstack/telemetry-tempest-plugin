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
import unittest

from gabbi import runner
from gabbi import suitemaker
from gabbi import utils
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def run_test(test_class_instance, test_dir, filename):
    d = utils.load_yaml(yaml_file=os.path.join(test_dir, filename))
    cert_validate = not CONF.telemetry.disable_ssl_certificate_validation
    if 'defaults' in d:
        d['defaults']['cert_validate'] = cert_validate
    else:
        d['defaults'] = {'cert_validate': cert_validate}
    test_suite = suitemaker.test_suite_from_dict(
        loader=unittest.defaultTestLoader,
        test_base_name="gabbi",
        suite_dict=d,
        test_directory=test_dir,
        host='example.com', port=None,
        fixture_module=None,
        intercept=None,
        handlers=runner.initialize_handlers([]),
        test_loader_name="tempest")

    # NOTE(sileht): We hide stdout/stderr and reraise the failure
    # manually, tempest will print it ittest_class.
    with open(os.devnull, 'w') as stream:
        result = unittest.TextTestRunner(
            stream=stream, verbosity=0, failfast=True,
        ).run(test_suite)

    if not result.wasSuccessful():
        failures = (result.errors + result.failures
                    + result.unexpectedSuccesses)
        if failures:
            test, bt = failures[0]
            name = test.test_data.get('name', test.id())
            msg = 'From test "%s" :\n%s' % (name, bt)
            test_class_instance.fail(msg)

    test_class_instance.assertTrue(result.wasSuccessful())


def test_maker(test_dir, filename, name):
    def test(self):
        self._prep_test(filename)
        run_test(self, test_dir, filename)
    test.__name__ = name
    return test


def generate_tests(test_class, test_dir):
    # Create one scenario per yaml file
    filenames = os.listdir(test_dir)
    if not filenames:
        raise RuntimeError("%s is empty" % test_dir)
    for filename in filenames:
        if not filename.endswith('.yaml'):
            continue
        name = "test_%s" % filename[:-5].lower().replace("-", "_")
        setattr(test_class, name,
                test_maker(test_dir, filename, name))
