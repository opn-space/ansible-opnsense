import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf_general import General
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf_network import \
    Network as OspfNetwork
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf3_network import \
    Network as Ospf3Network


class FailJson(Exception):
    pass


def _fail_json(msg, **kwargs):
    raise FailJson(msg)


# GET quagga/ospfsettings/get -> 'ospf', os-frr 2.0_1 (measured, 26.7.7)
OSPF_GENERAL_2 = {
    'enabled': '0', 'carp_demote': '0', 'routerid': '', 'costreference': '',
    'logadjacencychanges': '0', 'originate': '0', 'originatealways': '0', 'originatemetric': '',
    'areas': {'area': []}, 'networks': {'network': []}, 'neighbors': {'neighbor': []},
    'interfaces': {'interface': []}, 'prefixlists': {'prefixlist': []},
    'routemaps': {'routemap': []}, 'redistributions': {'redistribution': []},
}

# os-frr 1.55: the same page plus 'passiveinterfaces' (InterfaceField, multiple)
OSPF_GENERAL_1 = {
    **OSPF_GENERAL_2,
    'passiveinterfaces': {
        'lan': {'value': 'LAN', 'selected': 1},
        'wan': {'value': 'WAN', 'selected': 0},
    },
}


def _instance(mocker, cls):
    mocker.patch.object(cls, '__init__', return_value=None)
    instance = cls()
    instance.m = mocker.MagicMock()
    instance.m.fail_json.side_effect = _fail_json
    instance.r = {'diff': {}}
    return instance


@pytest.fixture
def general(mocker):
    instance = _instance(mocker, General)
    mocker.patch.object(General, '_base_check', return_value=None)
    return instance


@pytest.fixture
def ospf_network(mocker):
    instance = _instance(mocker, OspfNetwork)
    mocker.patch.object(OspfNetwork, '_base_check', return_value=None)
    mocker.patch.object(OspfNetwork, 'find_single_link', return_value=None)
    instance.existing_prefixes = {}
    instance.ospf_settings = None
    instance.p = {
        'state': 'present', 'ip': '10.0.0.0', 'mask': 24, 'area': '0.0.0.0',
        'area_range': '', 'prefix_list_in': '', 'prefix_list_out': '',
    }
    return instance


def test_general_reads_os_frr_2(general):
    simple = general.simplify_existing(OSPF_GENERAL_2)
    assert 'passive_ints' not in simple
    assert simple['enabled'] is False


def test_general_reads_os_frr_1(general):
    simple = general.simplify_existing(OSPF_GENERAL_1)
    assert 'passive_ints' in simple


@pytest.mark.parametrize('passive_ints, fails', [([], False), (None, False), (['lan'], True)])
def test_general_passive_ints_on_os_frr_2(general, passive_ints, fails):
    general.settings = general.simplify_existing(OSPF_GENERAL_2)
    general.p = {'passive_ints': passive_ints}
    if fails:
        with pytest.raises(FailJson, match='frr_ospf_interface passive'):
            general.check()

    else:
        general.check()


def test_general_passive_ints_on_os_frr_1(general):
    general.settings = general.simplify_existing(OSPF_GENERAL_1)
    general.p = {'passive_ints': ['lan']}
    general.check()


def test_network_reads_os_frr_2(ospf_network):
    entry = {'uuid': 'u1', 'enabled': '1', 'ipaddr': '10.0.0.0', 'netmask': '24', 'area': '0.0.0.0'}
    simple = ospf_network.simplify_existing(entry)
    assert simple['ip'] == '10.0.0.0'
    assert 'area_range' not in simple
    assert 'prefix_list_in' not in simple


@pytest.mark.parametrize('field', ['area_range', 'prefix_list_in', 'prefix_list_out'])
def test_network_moved_fields_on_os_frr_2(ospf_network, field):
    ospf_network.ospf_settings = OSPF_GENERAL_2
    ospf_network.p[field] = 'x'
    with pytest.raises(FailJson, match=f'moved {field} .*frr_ospf_area'):
        ospf_network.check()


def test_network_without_moved_fields_on_os_frr_2(ospf_network):
    ospf_network.ospf_settings = OSPF_GENERAL_2
    ospf_network.check()


def test_network_moved_fields_on_os_frr_1(ospf_network):
    ospf_network.ospf_settings = OSPF_GENERAL_1
    ospf_network.p['area_range'] = '10.0.0.0/16'
    ospf_network.check()


def test_ospf3_network_endpoints_removed_on_os_frr_2(mocker):
    network = _instance(mocker, Ospf3Network)
    with pytest.raises(FailJson, match='removed OSPFv3 router-level networks'):
        network._search_path_handling({'ospf6': {'enabled': '0', 'areas': {'area': []}}})


def test_ospf3_network_reads_os_frr_1(mocker):
    network = _instance(mocker, Ospf3Network)
    network.ATTR_AK_PATH_SPLIT_CHAR = '.'
    data = {'ospf6': {'networks': {'network': {'u1': {'ipaddr': 'fd00::'}}}}}
    assert network._search_path_handling(data) == {'u1': {'ipaddr': 'fd00::'}}
