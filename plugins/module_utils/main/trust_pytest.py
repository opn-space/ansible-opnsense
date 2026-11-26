import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust import \
    pem, TrustCa, TrustCert


class FailJson(Exception):
    pass


def _fail_json(msg, **kwargs):
    raise FailJson(msg)


CRT = '-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----'
PRV = '-----BEGIN PRIVATE KEY-----\nMIIE\n-----END PRIVATE KEY-----'
UUID = '6a0c1a1e-0000-4000-8000-000000000001'

# a 'get' merged onto its 'search' row, as BaseLogic.search() returns it
EXISTING = {
    'uuid': UUID, 'refid': '6650a1b2c3d4e', 'descr': 'Site CA',
    'action': {'internal': {'value': 'Create', 'selected': 1}},
    'crt_payload': CRT + '\r\n', 'prv_payload': PRV + '\n',
}


def _module(mocker, params: dict):
    m = mocker.MagicMock()
    m.fail_json.side_effect = _fail_json
    m.check_mode = True
    m.params = {'state': 'present', 'debug': False, 'crt': None, 'prv': None, **params}
    return m


def _entry(mocker, cls, params: dict, existing: list):
    mocker.patch.object(cls, '_call_search', return_value=existing)
    return cls(module=_module(mocker, params), result={'changed': False, 'diff': {}}, session=mocker.MagicMock())


def test_pem():
    assert pem(f'  {CRT}\r\n') == CRT
    assert pem(' -----BEGIN X-----  \n  abc \n-----END X-----\n\n') == '-----BEGIN X-----\nabc\n-----END X-----'
    assert pem(None) == ''


@pytest.mark.parametrize('cls', [TrustCa, TrustCert])
def test_simplify_is_idempotent(mocker, cls):
    e = _entry(mocker, cls, {'description': 'Site CA', 'crt': CRT}, [])
    simple = e.simplify_existing(EXISTING)
    assert simple == {
        'uuid': UUID, 'refid': '6650a1b2c3d4e', 'description': 'Site CA', 'crt': CRT, 'prv': PRV,
    }
    assert e.simplify_existing(simple) == simple


@pytest.mark.parametrize('cls, ak, action', [
    (TrustCa, 'ca', 'existing'),
    (TrustCert, 'cert', 'import'),
])
def test_create_posts_an_import(mocker, cls, ak, action):
    e = _entry(mocker, cls, {'description': 'Site CA', 'crt': CRT + '\n', 'prv': PRV}, [])
    e.check()
    assert not e.exists
    assert e._get_request_data() == {ak: {
        'descr': 'Site CA', 'action': action, 'crt_payload': CRT, 'prv_payload': PRV,
    }}
    assert e.r['diff']['after']['prv'] == e.VALUE_NO_LOG
    assert 'action' not in e.r['diff']['after']


@pytest.mark.parametrize('cls', [TrustCa, TrustCert])
def test_unchanged_reports_ok(mocker, cls):
    e = _entry(mocker, cls, {'description': 'Site CA', 'crt': CRT, 'prv': PRV}, [EXISTING])
    e.check()
    assert e.exists
    e.update()
    assert not e.r['changed']
    assert PRV not in str(e.r['diff'])


@pytest.mark.parametrize('cls', [TrustCa, TrustCert])
def test_changed_payload_replaces_it(mocker, cls):
    other = CRT.replace('MIIB', 'MIIC')
    e = _entry(mocker, cls, {'description': 'Site CA', 'crt': other}, [EXISTING])
    e.check()
    e.update()
    assert e.r['changed']


@pytest.mark.parametrize('cls', [TrustCa, TrustCert])
def test_undeclared_key_is_kept(mocker, cls):
    # existing key, none declared: not compared, not posted
    e = _entry(mocker, cls, {'description': 'Site CA', 'crt': CRT}, [EXISTING])
    e.check()
    e.update()
    assert not e.r['changed']
    assert 'prv_payload' not in e._get_request_data()[cls.API_KEY_PATH]


def test_changed_key_replaces_it(mocker):
    e = _entry(mocker, TrustCert, {'description': 'Site CA', 'crt': CRT, 'prv': PRV.replace('MIIE', 'MIIF')}, [EXISTING])
    e.check()
    e.update()
    assert e.r['changed']


def test_present_needs_crt(mocker):
    e = _entry(mocker, TrustCert, {'description': 'VPN user'}, [])
    with pytest.raises(FailJson, match="You need to supply 'crt' to import cert 'VPN user'"):
        e.check()


def test_absent_needs_no_crt(mocker):
    e = _entry(mocker, TrustCa, {'description': 'Site CA', 'state': 'absent'}, [EXISTING])
    e.check()
    assert e.exists
    assert e.call_cnf['params'] == [UUID]


def test_multi_process_without_reload_argument(mocker):
    # trust_cert_multi declares no `reload`: a changed run must not KeyError
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.multi import MultiModule
    mm = MultiModule.__new__(MultiModule)
    mm.p = {'multi': [{'description': 'x'}], 'multi_purge': []}
    mm.r = {'changed': True}
    mm.cache_existing = False
    mm.meta_entry = mocker.MagicMock()
    mm.s = mocker.MagicMock()
    mm.m = mocker.MagicMock()
    mm._is_multi_purge = lambda: False
    mm._is_multi_crud = lambda: True
    mm._create_update = lambda: None
    mm._purge_unconfigured = lambda: None
    mm.process()
    mm.meta_entry.reload.assert_not_called()
