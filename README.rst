`mita`
------
A Jenkins slave orchestration service: will poll the queue of a master Jenkins
instance and look for jobs that are stuck and map the labels needed to
configured images ready to get created.

Currently supports only OpenStack as a backend for slave nodes.

configuration
-------------
The intent of the service is to provide multiple backends, although it
currently supports OpenStack, while keeping a check on the Jenkins queue.

Configuring the application requires three distinct parts:

*provider*: The ``provider`` key is a dictionary that contains the name of the
provider which itself should contain a ``username`` and ``password`` key. For
example this is how it would look for OpenStack::

    provider = {
        'openstack': {
            'username': 'adeza',
            'password': '3ebYzVIQEIZv3sj1==',
            'auth_url': 'http://openstack.example.com:5000',
            'auth_version': '2.0_password',
            'service_region': 'main',
            'tenant_name': 'ceph-ci',
        }
    }

This service relies heavily on Apache `LibCloud`_ , please refer to the
compute examples to see what other keys can be used here and common values:

https://libcloud.readthedocs.org/en/latest/compute/examples.html#create-an-openstack-node-using-a-local-openstack-provider



About the name
--------------
The ancient Inca empire didn't use any form of slavery and used a taxation
mechanism that mandated public service for all citizens that could perform
labor. And thus, this service ensures that nodes will be up and running (and
will later be terminated) to do some work.

.. _LibCloud https://libcloud.readthedocs.org/en/latest/compute/
