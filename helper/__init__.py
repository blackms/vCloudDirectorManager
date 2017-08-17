__author__ = 'alessio.rocchi'
import time
from threading import Thread


def config_section_map(config_object, section):
    dict1 = {}
    options = config_object.options(section)
    for option in options:
        try:
            dict1[option] = config_object.get(section, option)
        except KeyError:
            dict1[option] = None
    return dict1


def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result

    return timed


def threaded(fn):
    def run(*k, **kw):
        _t = Thread(target=fn, args=k, kwargs=kw)
        _t.start()
        return _t
    return run


def calculate_free_ips(global_variable):
    import itertools
    from netaddr import IPSet, IPAddress
    global_variable.free_ip_lock = True
    global_variable.app.logger.debug('Calculating free ips...')
    networks = {}
    for ip in list(itertools.chain(*[ip_ for ip_ in global_variable.used_ips])):
        net = '{network}.0/24'.format(network='.'.join(ip.split('.')[0:3]))
        if net not in networks.keys():
            networks[net] = IPSet([net])
        if IPAddress(ip) in networks[net]:
            networks[net].remove(IPAddress(ip))
        for x in xrange(0, 11):
            networks[net].remove(
                IPAddress(
                    '{network}.{last_oct}'.format(network='.'.join(ip.split('.')[0:3]),
                                                  last_oct=x)
                )
            )
    global_variable.free_ips = {key: [x for x in value] for key, value in networks.items()}
    global_variable.free_ip_lock = False
    return True


def wait_for_task(task, global_variable):
    import requests
    from vcloudlib.schema.vcd.v1_5.schemas.vcloud import taskType
    headers = global_variable.vcs.get_vcloud_headers()
    req = requests.get(task.href, headers=headers, verify=global_variable.vcs.verify)
    vcloud_task = taskType.parseString(req.content)
    while vcloud_task.status == 'running':
        time.sleep(2)
        req = requests.get(task.href, headers=headers, verify=global_variable.vcs.verify)
        vcloud_task = taskType.parseString(req.content)
    return


def get_less_used_network(num_of_requested_ip, global_variable, config_obj):
    """
    Get the network with more IP available.

    :return: Network
    """
    # identify less used network
    while global_variable.free_ip_lock is True:
        time.sleep(1)
    free_ip = global_variable.free_ips
    less_used_network = sorted(free_ip, key=lambda k: len(free_ip[k]), reverse=True)[0]
    # network must have enough IPs
    if len(global_variable.free_ips[less_used_network]) < num_of_requested_ip + int(
            config_section_map(config_obj, 'vcloud')['min_spare_ip']):
        return None
    ip_list = global_variable.free_ips[less_used_network][:num_of_requested_ip]
    pvdc_external_networks = global_variable.vcs.get_network()
    from ipaddress import IPv4Address, IPv4Network

    external_network = filter(lambda x: IPv4Address(x.gateway) in IPv4Network(less_used_network), pvdc_external_networks)
    return {'object': external_network[0],
            'iplist': ip_list}

