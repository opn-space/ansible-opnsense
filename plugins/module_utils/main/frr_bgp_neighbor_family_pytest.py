import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_bgp_neighbor import Neighbor


def _api_entry() -> dict:
    # every field the module reads, in the API's names
    entry = {'uuid': 'n1'}
    selects = Neighbor.FIELDS_TYPING['select'] + Neighbor.FIELDS_TYPING['list']
    for field in Neighbor.FIELDS_ALL:
        api = Neighbor.FIELDS_TRANSLATE.get(field, field)
        if field in selects:
            entry[api] = {}

        elif field in Neighbor.FIELDS_TYPING['bool']:
            entry[api] = '0'

        else:
            entry[api] = ''

    return entry


# os-frr 1.x: 'multiprotocol', no 'family'
ENTRY_1 = {k: v for k, v in _api_entry().items() if k != 'family'}
ENTRY_1['multiprotocol'] = '1'
# os-frr 2.0: 'family', no 'multiprotocol'
ENTRY_2 = {k: v for k, v in _api_entry().items() if k != 'multiprotocol'}
ENTRY_2['family'] = {'ipv4': {'value': 'IPv4', 'selected': 1}, 'ipv6': {'value': 'IPv6', 'selected': 1}}


@pytest.fixture
def neighbor(mocker):
    mocker.patch.object(Neighbor, '__init__', return_value=None)
    mocker.patch.object(Neighbor, '_base_check', return_value=None)
    mocker.patch.object(Neighbor, '_find_links', return_value=None)
    instance = Neighbor()
    instance.m = mocker.MagicMock()
    instance.p = {'state': 'present', 'ip': '192.0.2.1', 'local_ip': None}
    return instance


@pytest.mark.parametrize('family, multi_protocol, want_family, want_mp', [
    (None, None, ['ipv4'], False),
    (None, False, ['ipv4'], False),
    (None, True, ['ipv4', 'ipv6'], True),
    ([], None, ['ipv4'], False),
    (['ipv4'], None, ['ipv4'], False),
    (['ipv6'], None, ['ipv6'], True),
    (['ipv4', 'ipv6'], None, ['ipv4', 'ipv6'], True),
])
def test_family_and_multi_protocol_in_step(neighbor, family, multi_protocol, want_family, want_mp):
    neighbor.p['family'] = family
    neighbor.p['multi_protocol'] = multi_protocol
    neighbor.check()
    assert neighbor.p['family'] == want_family
    assert neighbor.p['multi_protocol'] is want_mp


def test_reads_os_frr_1(neighbor):
    simple = neighbor.simplify_existing(dict(ENTRY_1))
    assert simple['multi_protocol'] is True
    assert 'family' not in simple


def test_reads_os_frr_2(neighbor):
    simple = neighbor.simplify_existing(dict(ENTRY_2))
    assert simple['family'] == ['ipv4', 'ipv6']
    assert 'multi_protocol' not in simple
