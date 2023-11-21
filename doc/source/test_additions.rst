=======================
Adding additional tests
=======================

:Modify .zuul.yaml:
    Make required modifications to the devstack configuration in the .zuul.yaml. Mainly add any new required projects and env variables. If you require a non-openstack project, check that it's listed in the project-config under the openstack tenant: https://opendev.org/openstack/project-config/src/branch/master/zuul/main.yaml. Create a patch for the project-config to add that project if it isn't already there, otherwise it won't be available in check and gate jobs.

:Add tests:
    Add new tests. These can be either the scenario tests using gabbi: https://gabbi.readthedocs.io/en/latest/ or python code using tempest directly. See https://docs.openstack.org/tempest/latest/field_guide/index.html. If there is some configuration required to run the tests, take a look at the telemetry_tempest_plugin/conf.py.

:Example:
    An example of adding a simple test can be seen here: https://review.opendev.org/c/openstack/telemetry-tempest-plugin/+/898201
