import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.translate import \
    get_selected_opt_list_idx, simplify_translate
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.ipsec_connection import Connection


def _versions(labels: list, selected: int) -> list:
    return [{'value': label, 'selected': int(i == selected)} for i, label in enumerate(labels)]


LABELS_26_1 = ['IKEv1+IKEv2', 'IKEv1', 'IKEv2']
# 26.7 renamed the labels; the positions (the stored values 0, 1, 2) did not move
LABELS_26_7 = ['IKEv1+IKEv2 (allows deprecated IKEv1)', 'IKEv1 (deprecated)', 'IKEv2']


@pytest.mark.parametrize('data, expected', [
    (_versions(LABELS_26_7, 0), 0),
    (_versions(LABELS_26_7, 2), 2),
    ({'0': {'value': 'IKEv1+IKEv2', 'selected': 0}, '1': {'value': 'IKEv1', 'selected': 1}}, '1'),
    (2, 2),  # re-applied
])
def test_get_selected_opt_list_idx(data, expected):
    assert get_selected_opt_list_idx(data) == expected


def _existing(version: list) -> dict:
    # a connection as connections/get returns it, every typed field present
    sel = lambda v: {v: {'value': v, 'selected': 1}}  # noqa: E731
    return {
        'uuid': '3290a9ae-ae3f-45cd-ba36-96fbabaae652', 'enabled': '1', 'description': 'ipsec-test-conn',
        'local_addrs': {'192.0.2.1': {'value': '192.0.2.1', 'selected': 1}},
        'remote_addrs': {'192.0.2.2': {'value': '192.0.2.2', 'selected': 1}},
        'pools': {}, 'proposals': {'default': {'value': 'default', 'selected': 1}},
        'unique': sel('no'), 'aggressive': '0', 'version': version, 'mobike': '1', 'encap': '0',
        'reauth_time': '', 'rekey_time': '', 'over_time': '', 'dpd_delay': '', 'dpd_timeout': '',
        'send_certreq': '1', 'send_cert': sel(''), 'keyingtries': '',
        'local_port': sel(''), 'remote_port': sel(''),
    }


@pytest.mark.parametrize('labels', [LABELS_26_1, LABELS_26_7])
@pytest.mark.parametrize('selected, expected', [(0, 'ikev1+2'), (1, 'ikev1'), (2, 'ikev2')])
def test_version_read_back_by_position(labels, selected, expected):
    # 26.7's new labels made every unchanged connection report 'changed' (#353 test run)
    simple = simplify_translate(
        existing=_existing(_versions(labels, selected)),
        typing=Connection.FIELDS_TYPING,
        translate=Connection.FIELDS_TRANSLATE,
        value_map=Connection.FIELDS_VALUE_MAPPING_RCV,
    )
    assert simple['version'] == expected
