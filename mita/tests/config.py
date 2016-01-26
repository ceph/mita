from pecan.hooks import TransactionHook
from textwrap import dedent

from mita import models

# Server Specific Configurations
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'mita.controllers.root.RootController',
    'modules': ['mita'],
    'debug': False,
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        )
    ],
}

logging = {
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'mita': {'level': 'DEBUG', 'handlers': ['console']},
        'pecan': {'level': 'DEBUG', 'handlers': ['console']},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
        '__force_dict__': True
        }
    }
}

nodes = {
    'precise-slave': {
        'script': dedent("""#!/bin/bash
        curl -L "http://172.18.181.11/setup/slave/?token=727999lw61w7dewfwe27&executors=1&labels=amd64+precise+trusty+wheezy+jessie+x86_64&nodename=precise__%s" | bash
        """),
        'keyname': 'jenkins-build',
        'image_name': 'Ubuntu Trusty (2014.04) cloudimg',
        'size': 'm3.xlarge',
        'labels': ['amd64', 'x86_64', 'precise', 'trusty', 'wheezy', 'jessie'],
        'provider': 'openstack'
    },
    'wheezy-slave': {
        'script': dedent("""#!/bin/bash
        curl -L "http://172.18.181.11/setup/slave/?token=727999lw61w7dewfwe27&executors=1&labels=amd64+precise+trusty+wheezy+jessie+x86_64&nodename=wheezy__%s" | bash
        """),
        'keyname': 'jenkins-build',
        'image_name': 'Ubuntu Trusty (2014.04) cloudimg',
        'size': 'm3.xlarge',
        'labels': ['amd64', 'x86_64', 'precise', 'trusty', 'wheezy', 'jessie'],
        'provider': 'openstack'
    },
    'rhel6-slave': {
        'script': dedent("""#!/bin/bash
        curl -L "http://172.18.181.11/setup/slave/?token=727999lw61w7dewfwe27&executors=2&labels=rhel6.5+amd64+rhel6+rhel+rhel6-pbuild+rhel-pbuild+x86_64&nodename=rhel6__%s" | bash"""),
        'keyname': 'jenkins-build',
        'image_name': 'centos-6.5-20140117.0.x86_64.qcow2',
        'size': 'm3.xlarge',
        'labels': ['amd64', 'x86_64', 'rhel6', 'rhel6.5'],
        'provider': 'openstack'
    },
    'rhel7-slave': {
        'script': dedent("""#!/bin/bash
        curl -L "http://172.18.181.11/setup/slave/?token=727999862a610c74363&executors=2&labels=amd64+rhel7+amd64+x86_64&nodename=rhel7__%s" | bash"""),
        'keyname': 'jenkins-build',
        'image_name': 'CentOS-7.1-x86_64-GenericCloud-1503',
        'size': 'm3.xlarge',
        'labels': ['amd64', 'x86_64', 'rhel7'],
        'provider': 'openstack'
    },
    'centos7-slave': {
        'script': dedent("""#!/bin/bash
        curl -L "http://172.18.181.11/setup/slave/?token=727999862a610c74363&executors=2&labels=amd64+centos7+amd64+x86_64&nodename=centos7__%s" | bash"""),
        'keyname': 'jenkins-build',
        'image_name': 'CentOS-7.1-x86_64-GenericCloud-1503',
        'size': 'm3.xlarge',
        'labels': ['amd64', 'x86_64', 'centos7'],
        'provider': 'openstack'
    },
    '__force_dict__': True

}

provider = {
    'openstack': {
        'username': 'adeza',
        'password': 'if1JT151Hll1r7',
        'auth_url': 'http://public.osop.example.com:5000',
        'auth_version': '2.0_password',
        'service_region': 'Public',
        'tenant_name': 'ci',
    }
}

jenkins = {
    'url': 'http://jenkins.example.com',
    'user': 'alfredodeza',
    'token': '111111e62ae10cee3631e580de6f3e27',
}

sqlalchemy = {
    # You may use SQLite for testing
    'url': 'sqlite:///tmp/test.db',
    # When you set up PostreSQL, it will look more like:
    #'url': 'postgresql+psycopg2://USER:PASSWORD@DB_HOST/DB_NAME',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}
