import logging
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
import libcloud.security
from pecan import conf

from mita.exceptions import CloudNodeNotFound

logger = logging.getLogger(__name__)

# FIXME
# At the time this example was written, https://nova-api.trystack.org:5443
# was using a certificate issued by a Certificate Authority (CA) which is
# not included in the default Ubuntu certificates bundle (ca-certificates).
# Note: Code like this poses a security risk (MITM attack) and that's the
# reason why you should never use it for anything else besides testing. You
# have been warned.
libcloud.security.VERIFY_SSL_CERT = False

OpenStack = get_driver(Provider.OPENSTACK)


def get_driver():
    driver = OpenStack(
        conf.provider.openstack.username,
        conf.provider.openstack.password,
        ex_force_auth_url=conf.provider.openstack.auth_url,
        ex_force_auth_version=conf.provider.openstack.auth_version,
        ex_tenant_name=conf.provider.openstack.tenant_name,
        ex_force_service_region=conf.provider.openstack.service_region,
    )
    return driver


def create_node(**kw):
    name = kw['name']
    driver = get_driver()
    images = driver.list_images()
    sizes = driver.list_sizes()
    available_sizes = [s for s in sizes if s.name == kw['size']]
    if available_sizes:
        size = available_sizes[0]
        image = [i for i in images if i.name == kw['image_name']][0]
        driver.create_node(name=name, image=image, size=size, ex_userdata=kw['script'], ex_keyname=kw['keyname'])


def destroy_node(**kw):
    """
    Relies on the fact that names **should be** unique. Along the chain we
    prevent non-unique names to be used/added.
    TODO: raise an exception if more than one node is matched to the name, that
    can be propagated back to the client.
    """
    driver = get_driver()
    name = kw['name']
    nodes = driver.list_nodes()
    for node in nodes:
        if node.name == name:
            driver.destroy_node(node)
            return

    raise CloudNodeNotFound
