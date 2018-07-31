# Copyright 2017 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license


import random

import constants as ovnconst

from netaddr import IPAddress
from netaddr import IPNetwork
from netaddr.core import AddrFormatError


def get_port_ip(lsp, lrp=None):
    if not lsp.addresses:
        return None
    if 'router' in lsp.addresses[0]:
        return get_port_router_ip(lrp)
    elif 'dynamic' in lsp.addresses[0]:
        return get_port_dynamic_ip(lsp)
    return get_port_static_ip(lsp)


def get_port_static_ip(port):
    return _get_ip_from_addresses(port.addresses)


def get_port_dynamic_ip(port):
    return _get_ip_from_addresses(port.dynamic_addresses)


def get_port_router_ip(lrp):
    return lrp.networks[0].split('/')[0] if lrp and lrp.networks else None


def get_port_mac(port):
    return port.addresses[0].split()[0] if port.addresses else None


def _get_all_macs(ports, get_macs):
    return [str(get_macs(port)) for port in ports]


def random_unique_mac(ls_ports, router_ports):
    all_macs = set().union(
        _get_all_macs(ls_ports, lambda p: get_port_mac(p)),
        _get_all_macs(router_ports, lambda p: p['mac'])
    )

    for _ in range(99):
        mac = _random_mac()
        if mac not in all_macs:
            return mac

    raise Exception(
        'Unable to allocate an unused mac after 100 retries'
    )


def _random_mac():
    macparts = [0]
    macparts.extend([random.randint(0x00, 0xff) for i in range(5)])
    return ':'.join(map(lambda x: "%02x" % x, macparts))


def get_ip_from_cidr(cidr):
    return cidr.split('/')[0]


def get_mask_from_subnet(subnet):
    return subnet.cidr.split('/')[1]


def ip_in_cidr(ip, cidr):
    return IPAddress(ip) in IPNetwork(cidr)


def _get_ip_from_addresses(addresses):
    if not addresses:
        return None
    address_parts = addresses[0].split(' ')
    candidate = address_parts[1] if len(address_parts) > 1 else None
    return candidate if _is_valid_ip(candidate) else None


def _is_valid_ip(candidate):
    try:
        IPAddress(candidate)
    except AddrFormatError:
        return False
    return True


def get_network_exclude_ips(network):
    exclude_values = network.other_config.get(
        ovnconst.LS_OPTION_EXCLUDE_IPS, ''
    )
    # TODO: should we care about IP ranges? we do not use them, but
    # what if someone else will?
    # lets raise for now
    result = []
    for exclude_value in exclude_values.split():
        if ovnconst.LS_EXCLUDED_IP_DELIMITER in exclude_value:
            raise NotImplementedError(
                'Handling of ip ranges not yet implemented'
            )
        result.append(exclude_value)
    return result


def is_ip_available_in_network(network, ip):
    if any(
        ip == get_port_ip(port)
        for port in network.ports
    ):
        return False
    exclude_ips = get_network_exclude_ips(network)
    return ip not in exclude_ips


def diff_routes(new_rest_routes, db_routes):
    if new_rest_routes is None:
        new_rest_routes = []
    if db_routes is None:
        db_routes = []
    new_set = set([
        ':'.join((d['destination'], d['nexthop'])) for d in new_rest_routes
    ])
    old_set = set([':'.join((d.ip_prefix, d.nexthop)) for d in db_routes])
    added = new_set - old_set
    removed = old_set - new_set
    return (
        dict([(s.split(':')[0], s.split(':')[1]) for s in added]),
        dict([(s.split(':')[0], s.split(':')[1]) for s in removed]),
    )


def get_ip_with_mask(ip, cidr):
    mask = cidr.split('/')[1]
    return '{ip}/{netmask}'.format(ip=ip, netmask=mask)