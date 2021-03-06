# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015 Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

from metaswitch.clearwater.cluster_manager.plugin_base import SynchroniserPluginBase
from metaswitch.clearwater.etcd_shared.plugin_utils import run_command
import subprocess
import logging

_log = logging.getLogger("cassandra_failed_plugin")

class CassandraFailedPlugin(SynchroniserPluginBase):

    # This plugin has a different set of parameters to all of the
    # other SynchroniserPluginBase subclasses.  This is currently
    # necessary as mark_node_failed does not yet plumb through the
    # information needed to run a normal plugin.
    def __init__(self, key, ip):
        self._key = key
        self._ip = ip

    def key(self):  # pragma: no coverage
        return self._key

    def on_cluster_changing(self, cluster_view):  # pragma: no coverage
        pass

    def on_joining_cluster(self, cluster_view):  # pragma: no coverage
        pass

    def on_new_cluster_config_ready(self, cluster_view):  # pragma: no coverage
        pass

    def on_stable_cluster(self, cluster_view):  # pragma: no coverage
        pass

    def on_leaving_cluster(self, cluster_view):

        # Cassandra commands need to be run in the signaling network
        # namespace in split network systems.
        #
        # This function means that there are now two ways of running a
        # command in the signaling namespace - this function, and the
        # namespace parameter to run_command.  This plugin does not have
        # access to the signaling namespace name, so we use this function
        # as a tactical workaround.
        def in_sig_namespace(command):
            prefix = "/usr/share/clearwater/bin/run-in-signaling-namespace "
            return prefix + command

        # We must remove the node from the cassandra cluster. Get the node's ID
        # from nodetool status, then remove it with nodetool remove
        try:
            status_command = "nodetool status | grep " + self._ip
            output = subprocess.check_output(in_sig_namespace(status_command),
                                             shell=True,
                                             stderr=subprocess.STDOUT)
            _log.debug("Nodetool status succeeded and printed output {!r}".
                       format(output))
        except subprocess.CalledProcessError:  # pragma: no coverage
            _log.debug("hit error")

        if output != "":
            # Pull the UUID from the output
            for value in output.split():
                if "-" in value:
                    remove_command = "nodetool removenode " + value
                    run_command(in_sig_namespace(remove_command))
                    break
