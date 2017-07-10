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
#
from __future__ import absolute_import

from auth import validate_token
from auth import Forbidden
from auth import TOKEN_HTTP_HEADER_FIELD_NAME
from handlers.selecting_handler import SelectingHandler
from handlers.neutron_responses import responses
from ovndb.ovn_north import OvnNorth


class NeutronHandler(SelectingHandler):

    def call_response_handler(self, response_handler, content, id):
        if not validate_token(self.headers.get(
                TOKEN_HTTP_HEADER_FIELD_NAME, '')):
            raise Forbidden()
        with OvnNorth() as ovn_north:
            return response_handler(ovn_north, content, id)

    @staticmethod
    def get_responses():
        return responses()
