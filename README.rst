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


*jenkins*: The Jenkins section is very simple, it only requires three items:
``url``, ``user``, and ``token``::

    jenkins = {
        'url': 'http://jenkins.ceph.com',
        'user': 'alfredodeza',
        'token': 'API_TOKEN',
    }

*nodes*: This is where the virtual machines can be configured along with the
labels. The ``labels`` key is crucial when configuring each node entry in this
section because it allows the service to map the labels from the job that is
stuck in the Jenkins queue to a configured node in this section. A single node
might look like::


    nodes = {
        'precise-slave': {
            'script': dedent("""#!/bin/bash
            sudo apt-get update
            """),
            'keyname': 'jenkins-slave',
            'image_name': 'Ubuntu Trusty (2014.04) cloudimg',
            'size': 'm3.xlarge',
            'labels': ['amd64', 'x86_64', 'precise', 'trusty', 'wheezy', 'jessie'],
            'provider': 'openstack'
        }
    }

The top-level keys is the name that will be used to register the machine in the
cloud provider. The ``labels`` is a throwaway value that has no use for the
cloud provider (only important to be able to map it to a jenkins job need).

The ``provider`` key allows the system to understand that this should map to
a configured provider backend.

Again, this configuration section relies on Apache `LibCloud`_ , please refer to the
compute examples to see what other keys can be used here and common values.


Unique IDs and Jenkins Slaves
-----------------------------
In order for the service to properly remove a Jenkins node after the inactivity
grace period, it needs a way to map back to the provider. The Jenkins API does
not provide information about a node that would make it unique, so we rely on
a convention when naming the node.

It is particularly important to follow this convention when more than one type
of node will be created to cope with demand.

For example, if a node named 'ubuntu' will have to exist more than once, the
service will not be able to understand which one of all the 'ubuntu' nodes it
needs to delete in the provider.

The convention is to include one of the host's IP addresses onto the name when
registering it in Jenkins with a '+' symbol.

For example, a Jenkins slave, that exists with the name: "ubuntu+192.168.1.188"
would allow to have as many 'ubuntu' slaves but uniquely identifiable with an
IP that can be looked up on the provider's end to match it to the host.

The service will first attempt to map on the name, and failing to do that it
will try to use the IP to look it up.

It is up to whatever is registering the node in Jenkins to use this convention
if there is a chance of more than one host matching the same name.

About the name
--------------
The ancient Inca empire didn't use any form of slavery and used a taxation
mechanism that mandated public service for all citizens that could perform
labor. And thus, this service ensures that nodes will be up and running (and
will later be terminated) to do some work.

.. _LibCloud: https://libcloud.readthedocs.org/en/latest/compute/
