import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.frr import \
    get_areas, area_to_id, area_to_uuid
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf_area import Area
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf3_area import Area as Area3
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf_interface import Interface
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf3_interface import \
    Interface as Interface3
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf_network import Network


class FailJson(Exception):
    pass


def _fail_json(msg, **kwargs):
    raise FailJson(msg)


AREA_UUID = 'a1b2c3d4-0000-4000-8000-000000000001'
AREAS = {AREA_UUID: {'enabled': '1', 'id': '0.0.0.0', 'type': {'': {'value': 'normal', 'selected': 1}}}}

# 'ospf' page shapes: os-frr 2.0 has areas and no 'passiveinterfaces'
OSPF_2 = {'enabled': '1', 'areas': {'area': AREAS}, 'interfaces': {'interface': []}}
OSPF_1 = {'enabled': '1', 'passiveinterfaces': {}, 'areas': {'area': []}, 'interfaces': {'interface': []}}
# 'ospf6' page shapes: os-frr 2.0 has areas and no 'networks'; os-frr 1.x has no areas
OSPF6_2 = {'enabled': '1', 'areas': {'area': AREAS}}
OSPF6_1 = {'enabled': '1', 'networks': {'network': []}}

# interface entries as the API returns them
_IF = {
    'uuid': 'i1', 'enabled': '1', 'interfacename': {'lan': {'value': 'LAN', 'selected': 1}},
    'cost': '', 'cost_demoted': '65535', 'carp_depend_on': {}, 'hellointerval': '', 'deadinterval': '',
    'retransmitinterval': '', 'transmitdelay': '', 'priority': '', 'networktype': {},
}
_IF_V2 = {**_IF, 'authtype': {}, 'authkey': '', 'authkey_id': '1'}
AREA_REL = {AREA_UUID: {'value': '0.0.0.0', 'selected': 1}}
IF_2 = {**_IF_V2, 'area': AREA_REL, 'passive': '1'}
IF_1 = {**_IF_V2, 'area': '0.0.0.0'}
IF3_2 = {**_IF, 'area': AREA_REL, 'passive': '0'}
IF3_1 = {**_IF, 'area': '0.0.0.0', 'passive': '0'}


def _instance(mocker, cls):
    mocker.patch.object(cls, '__init__', return_value=None)
    instance = cls()
    instance.m = mocker.MagicMock()
    instance.m.fail_json.side_effect = _fail_json
    instance.r = {'diff': {}}
    return instance


# --- helper

def test_get_areas():
    assert get_areas(OSPF_2) == AREAS
    assert not get_areas(OSPF_1)
    assert not get_areas(OSPF6_1)
    assert not get_areas(None)


def test_area_to_id():
    assert area_to_id(AREAS, AREA_UUID) == '0.0.0.0'
    assert area_to_id(AREAS, '0.0.0.1') == '0.0.0.1'
    assert area_to_id({}, '0.0.0.0') == '0.0.0.0'


def test_area_to_uuid(mocker):
    module = mocker.MagicMock()
    module.fail_json.side_effect = _fail_json
    assert area_to_uuid(module, AREAS, '0.0.0.0', 'frr_ospf_area') == AREA_UUID
    with pytest.raises(FailJson, match="Area '0.0.0.1' is not defined; create it with frr_ospf_area"):
        area_to_uuid(module, AREAS, '0.0.0.1', 'frr_ospf_area')


# --- interfaces and networks read the dotted ID on both versions

@pytest.mark.parametrize('cls, attr, page, entry', [
    (Interface, 'ospf_settings', OSPF_2, IF_2),
    (Interface, 'ospf_settings', OSPF_1, IF_1),
    (Interface3, 'ospf6_settings', OSPF6_2, IF3_2),
    (Interface3, 'ospf6_settings', OSPF6_1, IF3_1),
])
def test_interface_reads_dotted_area(mocker, cls, attr, page, entry):
    instance = _instance(mocker, cls)
    setattr(instance, attr, page)
    assert instance.simplify_existing(dict(entry))['area'] == '0.0.0.0'


def test_network_reads_dotted_area(mocker):
    network = _instance(mocker, Network)
    network.ospf_settings = OSPF_2
    entry = {'uuid': 'n1', 'enabled': '1', 'ipaddr': '10.0.0.0', 'netmask': '24',
             'area': {AREA_UUID: {'value': '0.0.0.0', 'selected': 1}}}
    assert network.simplify_existing(entry)['area'] == '0.0.0.0'


# --- writes send the UUID on os-frr 2.0 and the dotted ID before

@pytest.mark.parametrize('cls, attr, page, sent', [
    (Interface, 'ospf_settings', OSPF_2, AREA_UUID),
    (Interface, 'ospf_settings', OSPF_1, '0.0.0.0'),
    (Interface3, 'ospf6_settings', OSPF6_2, AREA_UUID),
    (Interface3, 'ospf6_settings', OSPF6_1, '0.0.0.0'),
    (Network, 'ospf_settings', OSPF_2, AREA_UUID),
    (Network, 'ospf_settings', OSPF_1, '0.0.0.0'),
])
def test_request_area(mocker, cls, attr, page, sent):
    instance = _instance(mocker, cls)
    setattr(instance, attr, page)
    instance.p = {'state': 'present', 'area': '0.0.0.0'}
    seen = {}
    mocker.patch.object(cls, '_base_build_request', side_effect=lambda: seen.update(area=instance.p['area']) or {})
    instance.build_request()
    assert seen['area'] == sent
    assert instance.p['area'] == '0.0.0.0'


def test_request_undefined_area_on_os_frr_2(mocker):
    interface = _instance(mocker, Interface)
    interface.ospf_settings = OSPF_2
    interface.p = {'state': 'present', 'area': '0.0.0.1'}
    mocker.patch.object(Interface, '_base_build_request', return_value={})
    with pytest.raises(FailJson, match='create it with frr_ospf_area'):
        interface.build_request()


# --- OSPFv2 interface passive

@pytest.mark.parametrize('page, passive, fails', [
    (OSPF_2, True, False),
    (OSPF_1, True, True),
    (OSPF_1, False, False),
])
def test_interface_passive(mocker, page, passive, fails):
    interface = _instance(mocker, Interface)
    mocker.patch.object(Interface, '_base_check', return_value=None)
    interface.ospf_settings = page
    interface.p = {'state': 'present', 'area': '0.0.0.0', 'auth_type': None, 'auth_key': None,
                   'passive': passive}
    if fails:
        with pytest.raises(FailJson, match='frr_ospf_general passive_ints on os-frr < 2.0'):
            interface.check()

    else:
        interface.check()


def test_interface_reads_passive_on_both(mocker):
    interface = _instance(mocker, Interface)
    interface.ospf_settings = OSPF_2
    assert interface.simplify_existing(dict(IF_2))['passive'] is True
    interface.ospf_settings = OSPF_1
    assert 'passive' not in interface.simplify_existing(dict(IF_1))


# --- area modules

@pytest.fixture
def area(mocker):
    instance = _instance(mocker, Area)
    mocker.patch.object(Area, '_base_check', return_value=None)
    mocker.patch.object(Area, 'find_single_link', return_value=None)
    instance.existing_prefixes = {}
    instance.p = {'state': 'present', 'id': '0.0.0.1', 'type': 'stub', 'ranges': [],
                  'prefix_list_in': None, 'prefix_list_out': None}
    return instance


def test_area_os_frr_1_plain(area):
    area.ospf_settings = OSPF_1
    area.check()


@pytest.mark.parametrize('field, value', [('ranges', ['10.0.0.0/16']), ('prefix_list_in', 'pl1')])
def test_area_os_frr_2_fields_on_os_frr_1(area, field, value):
    area.ospf_settings = OSPF_1
    area.p[field] = value
    with pytest.raises(FailJson, match=f'{field} on an OSPF area needs os-frr 2.0'):
        area.check()


def test_area_os_frr_2_fields_on_os_frr_2(area):
    area.ospf_settings = OSPF_2
    area.p['ranges'] = ['10.0.0.0/16']
    area.p['prefix_list_in'] = 'pl1'
    area.check()


def test_area_reads_both(mocker):
    instance = _instance(mocker, Area)
    simple = instance.simplify_existing({'uuid': AREA_UUID, 'enabled': '1', 'id': '0.0.0.1',
                                         'type': {'stub': {'value': 'stub', 'selected': 1}}})
    assert simple['type'] == 'stub'
    assert 'ranges' not in simple
    simple = instance.simplify_existing({'uuid': AREA_UUID, 'enabled': '1', 'id': '0.0.0.1',
                                         'type': {'': {'value': 'normal', 'selected': 1}},
                                         'ranges': '10.0.0.0/16,10.1.0.0/16',
                                         'linkedPrefixlistIn': {}, 'linkedPrefixlistOut': {}})
    assert simple['ranges'] == ['10.0.0.0/16', '10.1.0.0/16']


def test_ospf3_area_on_os_frr_1(mocker):
    instance = _instance(mocker, Area3)
    with pytest.raises(FailJson, match='os-frr < 2.0 has no OSPFv3 area records'):
        instance._search_path_handling({'ospf6': OSPF6_1})


def test_ospf3_area_on_os_frr_2(mocker):
    instance = _instance(mocker, Area3)
    instance.ATTR_AK_PATH_SPLIT_CHAR = '.'
    assert instance._search_path_handling({'ospf6': OSPF6_2}) == AREAS
