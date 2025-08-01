import json
import logging
import time

from tests.common import config_reload
from tests.common.devices.sonic import SonicHost
from tests.common.helpers.parallel import parallel_run, reset_ansible_local_tmp
from tests.common.platform.device_utils import fanout_switch_port_lookup
from tests.common.reboot import REBOOT_TYPE_WARM, REBOOT_TYPE_FAST, REBOOT_TYPE_COLD
from tests.common.reboot import reboot
from tests.common.utilities import wait, wait_until
from . import constants
from ...helpers.multi_thread_utils import SafeThreadPoolExecutor

logger = logging.getLogger(__name__)


def reboot_dut(dut, localhost, cmd, reboot_with_running_golden_config=False):
    logging.info('Reboot DUT to recover')

    if 'warm' in cmd:
        reboot_type = REBOOT_TYPE_WARM
    elif 'fast' in cmd:
        reboot_type = REBOOT_TYPE_FAST
    else:
        reboot_type = REBOOT_TYPE_COLD

    if reboot_with_running_golden_config:
        gold_config_path = "/etc/sonic/running_golden_config.json"
        gold_config_stats = dut.stat(path=gold_config_path)
        if gold_config_stats["stat"]["exists"]:
            logging.info("Reboot DUT with the running golden config")
            dut.copy(
                src=gold_config_path,
                dest="/etc/sonic/config_db.json",
                remote_src=True,
                force=True
            )

    reboot(dut, localhost, reboot_type=reboot_type, safe_reboot=True, check_intf_up_ports=True)


def _recover_interfaces(dut, fanouthosts, result, wait_time):
    action = None
    for port in result['down_ports']:
        logging.warning("Restoring port: {}".format(port))

        pn = str(port).lower()
        if 'portchannel' in pn or 'vlan' in pn:
            action = 'config_reload'
            continue

        # If internal port is down, do 'config_reload' to recover.
        # Here we do lowercase string search as pn is converted to lowercase
        if '-ib' in pn or '-rec' in pn or '-bp' in pn:
            action = 'config_reload'
            continue

        fanout, fanout_port = fanout_switch_port_lookup(fanouthosts, dut.hostname, port)
        if fanout and fanout_port:
            fanout.shutdown(fanout_port)
            fanout.no_shutdown(fanout_port)
        if dut.facts["num_asic"] > 1:
            asic = dut.get_port_asic_instance(port)
            dut.asic_instance(asic.asic_index).startup_interface(port)
        else:
            dut.no_shutdown(port)
    wait(wait_time, msg="Wait {} seconds for interface(s) to restore.".format(wait_time))
    return action


def _recover_services(dut, result):
    status = result['services_status']
    services = [x for x in status if not status[x]]
    logging.warning("Service(s) down: {}".format(services))
    return 'reboot' if 'database' in services else 'config_reload'


@reset_ansible_local_tmp
def _neighbor_vm_recover_bgpd(node=None, results=None):
    """Function for restoring BGP on neighbor VMs using the parallel_run tool.

    Args:
        node (dict, optional): Neighbor host object. Defaults to None.
        results (Proxy to shared dict, optional): An instance of multiprocessing.Manager().dict(). Proxy to a dict
                shared by all processes for returning execution results. Defaults to None.
    """
    if node is None or results is None:
        logger.error('Missing kwarg "node" or "results"')
        return

    nbr_host = node['host']
    asn = node['conf']['bgp']['asn']
    result = {}

    # restore interfaces and portchannels
    intf_list = list(node['conf']['interfaces'].keys())
    result['restore_intfs'] = []
    for intf in intf_list:
        result['restore_intfs'].append(nbr_host.no_shutdown(intf))

    # start BGPd
    result['start_bgpd'] = nbr_host.start_bgpd()

    # restore BGP
    result['no_shut_bgp'] = nbr_host.no_shutdown_bgp(asn)

    # no shut bgp neighbors
    peers = node['conf'].get('bgp', {}).get('peers', {})
    neighbors = []
    for key, value in list(peers.items()):
        if key == 'asn':
            continue
        if isinstance(value, list):
            neighbors.extend(value)
    result['no_shut_bgp_neighbors'] = nbr_host.no_shutdown_bgp_neighbors(asn, neighbors)

    results[nbr_host.hostname] = result


def _neighbor_vm_recover_config(node=None, results=None):
    if isinstance(node["host"], SonicHost):
        config_reload(node["host"], is_dut=False)
    return results


def neighbor_vm_restore(duthost, nbrhosts, tbinfo, result=None):
    logger.info("Restoring neighbor VMs for {}".format(duthost))
    mg_facts = duthost.get_extended_minigraph_facts(tbinfo)
    vm_neighbors = mg_facts['minigraph_neighbors']
    if vm_neighbors:
        if result and "check_item" in result:
            if result["check_item"] == "neighbor_macsec_empty":
                unhealthy_nbrs = []
                for name, host in list(nbrhosts.items()):
                    if name in result["unhealthy_nbrs"]:
                        unhealthy_nbrs.append(host)
                parallel_run(_neighbor_vm_recover_config, (), {}, unhealthy_nbrs, timeout=300)
                logger.debug('Results of restoring neighbor VMs: {}'.format(unhealthy_nbrs))
        else:
            results = parallel_run(_neighbor_vm_recover_bgpd, (), {}, list(nbrhosts.values()), timeout=300)
            logger.debug('Results of restoring neighbor VMs: {}'.format(json.dumps(dict(results))))
    return 'config_reload'  # May still need to do a config reload


def _recover_with_command(dut, cmd, wait_time):
    dut.command(cmd)
    wait(wait_time, msg="Wait {} seconds for system to be stable.".format(wait_time))


def re_announce_routes(ptfhost, localhost, topo_name, ptf_ip, neighbor_number):
    def _check_exabgp():
        # Get pid of exabgp processes
        exabgp_pids = []
        output = ptfhost.shell("ps aux | grep exabgp/http_api |grep -v grep |  awk '{print $2}'",
                               module_ignore_errors=True)
        if output['rc'] != 0:
            logger.warning("cmd to fetch exabgp pid returned with error: {}".format(output["stderr"]))
            return False
        for line in output["stdout_lines"]:
            if len(line.strip()) == 0:
                continue
            exabgp_pids.append(line.strip())
        # Each bgp neighbor has 2 exabgp process, one is for v4 and another is for v6
        if len(exabgp_pids) != neighbor_number * 2:
            logger.info("pids number for exabgp processes is incorrect, expected: {}, actual: {}"
                        .format(neighbor_number * 2, len(exabgp_pids)))
            return False
        # Check whether all sockets for exabgp are created
        output = ptfhost.shell("ss -nltp | grep -E \"{}\""
                               .format("|".join(["pid={}".format(pid) for pid in exabgp_pids])),
                               module_ignore_errors=True)
        return output["rc"] == 0 and len(output["stdout_lines"]) == neighbor_number * 2

    def _op_routes(action):
        try:
            localhost.announce_routes(topo_name=topo_name, ptf_ip=ptf_ip, action=action, path="../ansible/")
            time.sleep(5)
        except Exception as e:
            logger.error("Failed to {} routes with error: {}".format(action, e))

    ptfhost.shell("supervisorctl restart exabgpv4:*", module_ignore_errors=True)
    ptfhost.shell("supervisorctl restart exabgpv6:*", module_ignore_errors=True)
    # Wait exabgp to be ready
    if not wait_until(120, 5, 0, _check_exabgp):
        logger.error("Not all exabgp process are running")

    _op_routes("withdraw")
    _op_routes("announce")
    return None


def adaptive_recover(ptfhost, dut, localhost, fanouthosts, nbrhosts, tbinfo, check_results, wait_time):
    outstanding_action = None
    for result in check_results:
        if result['failed']:
            if result['check_item'] == 'interfaces':
                action = _recover_interfaces(dut, fanouthosts, result, wait_time)
            elif result['check_item'] == 'services':
                action = _recover_services(dut, result)
            elif result['check_item'] == 'bgp':
                # If there is only default route missing issue, only need to re-announce routes to recover
                # Currently only support single asic
                if (dut.facts["num_asic"] == 1 and
                    ("no_v4_default_route" in result['bgp'] and len(result['bgp']) == 1 or
                     "no_v6_default_route" in result['bgp'] and len(result['bgp']) == 1 or
                    ("no_v4_default_route" in result['bgp'] and "no_v6_default_route" in result['bgp'] and
                     len(result['bgp']) == 2))):
                    action = re_announce_routes(ptfhost, localhost, tbinfo["topo"]["name"], tbinfo["ptf_ip"],
                                                len(nbrhosts))
                else:
                    action = neighbor_vm_restore(dut, nbrhosts, tbinfo, result)
            elif result['check_item'] == "neighbor_macsec_empty":
                action = neighbor_vm_restore(dut, nbrhosts, tbinfo, result)
            elif result['check_item'] in ['processes', 'mux_simulator']:
                action = 'config_reload'
            else:
                action = 'reboot'

            # Any action can override no action or 'config_reload'.
            # 'reboot' is last resort and cannot be overridden.
            if action and (not outstanding_action or outstanding_action == 'config_reload'):
                outstanding_action = action

            logging.warning("Restoring {} with proposed action: {}, final action: {}"
                            .format(result, action, outstanding_action))

    if outstanding_action:
        method = constants.RECOVER_METHODS[outstanding_action]
        wait_time = method['recover_wait']
        if method["reload"]:
            running_golden_config_file_check = dut.shell("[ -f /etc/sonic/running_golden_config.json ]",
                                                         module_ignore_errors=True)
            if running_golden_config_file_check.get('rc') == 0:
                config_source = 'running_golden_config'
            else:
                config_source = 'config_db'
            config_reload(dut, config_source=config_source,
                          safe_reload=True, check_intf_up_ports=True, wait_for_bgp=True)
        elif method["reboot"]:
            reboot_dut(dut, localhost, method["cmd"], reboot_with_running_golden_config=True)
        else:
            _recover_with_command(dut, method['cmd'], wait_time)


def recover(ptfhost, dut, localhost, fanouthosts, nbrhosts, tbinfo, check_results, recover_method):
    logger.warning("Try to recover %s using method %s" % (dut.hostname, recover_method))

    method = constants.RECOVER_METHODS[recover_method]
    wait_time = method['recover_wait']
    if method["adaptive"]:
        adaptive_recover(ptfhost, dut, localhost, fanouthosts, nbrhosts, tbinfo, check_results, wait_time)
    elif method["reload"]:
        running_golden_config_file_check = dut.shell("[ -f /etc/sonic/running_golden_config.json ]",
                                                     module_ignore_errors=True)
        if running_golden_config_file_check.get('rc') == 0:
            config_source = 'running_golden_config'
        else:
            config_source = 'config_db'
        config_reload(dut, config_source=config_source,
                      safe_reload=True, check_intf_up_ports=True, wait_for_bgp=True)
    elif method["reboot"]:
        reboot_dut(dut, localhost, method["cmd"])
    else:
        _recover_with_command(dut, method['cmd'], wait_time)


def recover_chassis(duthosts):
    logger.warning(f"Try to recover chassis {[dut.hostname for dut in duthosts]} using config reload")
    with SafeThreadPoolExecutor(max_workers=8) as executor:
        for duthost in duthosts:
            running_golden_config_file_check = duthost.shell("[ -f /etc/sonic/running_golden_config.json ]",
                                                             module_ignore_errors=True)
            if running_golden_config_file_check.get('rc') == 0:
                config_source = 'running_golden_config'
            else:
                config_source = 'minigraph'
            executor.submit(config_reload, duthost, config_source=config_source,
                            safe_reload=True, override_config=True,
                            check_intf_up_ports=True, wait_for_bgp=True)
