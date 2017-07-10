# Copyright 2016 Red Hat, Inc.
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
from __future__ import absolute_import

from mock import Mock
from uuid import UUID
import json

from handlers.neutron_responses import responses
from handlers.neutron_responses import GET
from handlers.neutron_responses import SHOW
from handlers.neutron_responses import DELETE
from handlers.neutron_responses import POST
from handlers.neutron_responses import PUT

from handlers.neutron_responses import NETWORKS
from handlers.neutron_responses import PORTS
from handlers.neutron_responses import SUBNETS

from ovndb.ovn_north_mappers import NetworkMapper
from ovndb.ovn_north_mappers import PortMapper


NOT_RELEVANT = None

NETWORK_ID01 = UUID(int=1)
NETWORK_NAME1 = 'network_name_1'
PORT_ID07 = UUID(int=7)


class NetworkRow(object):
    def __init__(self, uuid, name):
        self.uuid = uuid
        self.name = name


class PortRow(object):
    def __init__(self, uuid, name, mac, device_id):
        self.uuid = uuid
        self.name = name
        self.addresses = [mac]
        self.external_ids = {PortMapper.REST_PORT_DEVICE_ID: device_id}


class TestNeutronResponse(object):
    def test_check_neutron_responses_required_by_engine_are_present(self):
        for method in [GET, SHOW, DELETE, POST]:
            for path in [NETWORKS, PORTS, SUBNETS]:
                assert responses()[path][method] is not None
        assert responses()[PORTS][PUT] is not None
        # This is a test call engine makes to check if provider is alive
        assert responses()[''][GET] is not None

    def test_show_network(self):
        nb_db = Mock()
        nb_db.get_network.return_value = {
            NetworkMapper.REST_NETWORK_ID: str(NETWORK_ID01),
            NetworkMapper.REST_NETWORK_NAME: NETWORK_NAME1,
        }
        response = responses()[NETWORKS][SHOW](
            nb_db, NOT_RELEVANT, NETWORK_ID01)

        response_json = json.loads(response)
        assert response_json['network']['id'] == str(NETWORK_ID01)
        assert response_json['network']['name'] == NETWORK_NAME1

    def test_show_port(self):
        nb_db = Mock()
        nb_db.get_port.return_value = {
            PortMapper.REST_PORT_ID: str(PORT_ID07),
            PortMapper.REST_PORT_NAME: 'port_name',
            PortMapper.REST_PORT_SECURITY_GROUPS: [],
        }

        response = responses()[PORTS][SHOW](nb_db, NOT_RELEVANT, PORT_ID07)

        response_json = json.loads(response)
        assert response_json['port']['id'] == str(PORT_ID07)
        assert response_json['port']['name'] == 'port_name'
        assert response_json['port']['security_groups'] == []

    def test_get_networks(self):
        nb_db = Mock()
        nb_db.list_networks.return_value = [{
            NetworkMapper.REST_NETWORK_ID: str(NETWORK_ID01),
            NetworkMapper.REST_NETWORK_NAME: NETWORK_NAME1,
        }]
        response = responses()[NETWORKS][GET](
            nb_db, NOT_RELEVANT, NOT_RELEVANT)

        response_json = json.loads(response)
        assert response_json['networks'][0]['id'] == str(NETWORK_ID01)
        assert response_json['networks'][0]['name'] == NETWORK_NAME1

    def test_get_ports(self):
        nb_db = Mock()
        nb_db.list_ports.return_value = [{
            PortMapper.REST_PORT_ID: str(PORT_ID07),
            PortMapper.REST_PORT_NAME: 'port_name',
            PortMapper.REST_PORT_SECURITY_GROUPS: [],
        }]
        response = responses()[PORTS][GET](nb_db, NOT_RELEVANT, NOT_RELEVANT)

        response_json = json.loads(response)
        assert response_json['ports'][0]['id'] == str(PORT_ID07)
        assert response_json['ports'][0]['name'] == 'port_name'
        assert response_json['ports'][0]['security_groups'] == []

    def test_delete_network(self):
        nb_db = Mock()

        responses()[NETWORKS][DELETE](nb_db, NOT_RELEVANT, PORT_ID07)

        nb_db.delete_network.assert_called_once_with(PORT_ID07)

    def test_delete_port(self):
        nb_db = Mock()

        responses()[PORTS][DELETE](nb_db, NOT_RELEVANT, PORT_ID07)

        nb_db.delete_port.assert_called_once_with(PORT_ID07)

    def test_post_network(self):
        nb_db = Mock()
        nb_db.add_network.return_value = {
            NetworkMapper.REST_NETWORK_ID: str(NETWORK_ID01),
            NetworkMapper.REST_NETWORK_NAME: NETWORK_NAME1,
            NetworkMapper.REST_TENANT_ID: ''
        }
        rest_input = '{"network":{"name":"network_name"}}'

        response = responses()[NETWORKS][POST](nb_db, rest_input, NOT_RELEVANT)

        response_json = json.loads(response.body)
        assert response_json['network']['id'] == str(NETWORK_ID01)
        assert response_json['network']['name'] == NETWORK_NAME1

        rest_json = json.loads(rest_input)
        nb_db.add_network.assert_called_once_with(rest_json['network'])

    def test_post_port(self):
        nb_db = Mock()
        nb_db.add_port.return_value = {
            PortMapper.REST_PORT_ID: str(PORT_ID07),
            PortMapper.REST_PORT_NAME: 'port_name',
            PortMapper.REST_PORT_DEVICE_ID: 'device_id',
            PortMapper.REST_PORT_DEVICE_OWNER: 'oVirt',
            PortMapper.REST_PORT_NETWORK_ID: str(NETWORK_ID01),
            PortMapper.REST_PORT_MAC_ADDRESS: 'mac'
        }
        rest_input = ('{"port":{"name":"port_name", "mac_address":"mac",'
                      '"device_id":"device_id"}}')

        response = responses()[PORTS][POST](nb_db, rest_input, NOT_RELEVANT)

        response_json = json.loads(response.body)
        assert response_json['port']['id'] == str(PORT_ID07)
        assert response_json['port']['name'] == 'port_name'
        assert response_json['port']['mac_address'] == 'mac'
        assert response_json['port']['device_id'] == 'device_id'
        assert response_json['port']['device_owner'] == 'oVirt'
        assert response_json['port']['network_id'] == str(NETWORK_ID01)

        rest_json = json.loads(rest_input)
        nb_db.add_port.assert_called_once_with(rest_json['port'])

    def test_put_port(self):
        nb_db = Mock()
        nb_db.update_port.return_value = {
            PortMapper.REST_PORT_ID: str(PORT_ID07),
        }
        response = responses()[PORTS][PUT](
            nb_db, '{"port" :{}}', str(PORT_ID07))
        response_json = json.loads(response.body)
        assert response_json['port']['id'] == str(PORT_ID07)
