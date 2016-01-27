import logging
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from time import sleep
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
    storage = kw.get("storage")
    if available_sizes:
        size = available_sizes[0]
        image = [i for i in images if i.name == kw['image_name']][0]
        new_node = driver.create_node(name=name, image=image, size=size, ex_userdata=kw['script'], ex_keyname=kw['keyname'])

    if storage:
        logger.info("Creating %sgb of storage for: %s" % (storage, name))
        new_volume = driver.create_volume(storage, name)
        # wait for the new volume to become available
        logger.info("Waiting for volume %s to become available" % name)
        _wait_until_volume_available(new_volume, maybe_in_use=True)
        # wait for the new node to become available
        logger.info("Waiting for node %s to become available" % name)
        driver.wait_until_running([new_node])
        logger.info(" ... available")
        logger.info("Attaching volume %s..." % name)
        if driver.attach_volume(new_node, new_volume, '/dev/vdb') is not True:
            raise RuntimeError("Could not attached volume %s" % name)
        logger.info("Successfully attached volume %s" % name)


def _wait_until_volume_available(volume, maybe_in_use=False):
    """
    Wait until a StorageVolume's state is "available".
    Set "maybe_in_use" to True in order to wait even when the volume is
    currently in_use. For example, set this option if you're recycling
    this volume from an old node that you've very recently
    destroyed.
    """
    ok_states = ['creating']  # it's ok to wait if the volume is in this
    tries = 0
    if maybe_in_use:
        ok_states.append('in_use')
    logger.info('Volume %s is %s' % (volume.name, volume.state))
    while volume.state in ok_states:
        sleep(3)
        volume = get_volume(volume.name)
        logger.info(' ... %s' % volume.state)
        tries = tries + 1
        if tries > 10:
            logger.info("Maximum amount of tries reached..")
            break
    if volume.state != 'available':
        # OVH uses a non-standard state of 3 to indicate an available volume
        logger.info('Volume %s is %s (not available)' % (volume.name, volume.state))
        logger.info('The volume %s is not available, but will continue anyway...' % volume.name)
    return True


def get_volume(name):
    """ Return libcloud.compute.base.StorageVolume """
    driver = get_driver()
    volumes = driver.list_volumes()
    try:
        return [v for v in volumes if v.name == name][0]
    except IndexError:
        return None


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
            # also destroy any associated volumes
            destroy_volume(name)
            return

    raise CloudNodeNotFound


def destroy_volume(name):
    driver = get_driver()
    volume = get_volume(name)
    if volume:
        logger.info("Destroying volume %s" % name)
        driver.destroy_volume(volume)
