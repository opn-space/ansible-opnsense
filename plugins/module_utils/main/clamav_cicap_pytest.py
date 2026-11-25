import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.clamav_general import \
    General as ClamavGeneral
from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.cicap import \
    General as CicapGeneral, Antivirus as CicapAntivirus
from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.clamav_cicap import \
    CLAMAV_GENERAL_MOD_ARGS, CICAP_GENERAL_MOD_ARGS, CICAP_ANTIVIRUS_MOD_ARGS


def _opt(selected: list, options: list) -> dict:
    return {o: {'value': o, 'selected': int(o in selected)} for o in options}


TYPES = ['TEXT', 'DATA', 'EXECUTABLE', 'ARCHIVE', 'GIF', 'JPEG', 'MSOFFICE']

# 'get' responses as ApiMutableModelControllerBase returns them: every field of
# the model, with its default from General.xml / Antivirus.xml
CLAMAV_PAGE = {
    'enabled': '1', 'fc_enabled': '1', 'enabletcp': '1', 'maxthreads': '10', 'maxqueue': '100',
    'idletimeout': '30', 'maxdirrecursion': '20', 'followdirsym': '0', 'followfilesym': '0',
    'disablecache': '0', 'scanpe': '1', 'scanelf': '1', 'detectbroken': '0', 'scanole2': '1',
    'ole2blockmarcros': '0', 'scanpdf': '1', 'scanswf': '1', 'scanxmldocs': '1', 'scanhwp3': '1',
    'scanmailfiles': '1', 'scanhtml': '1', 'scanarchive': '1', 'arcblockenc': '0',
    'maxscansize': '100M', 'maxfilesize': '25M', 'maxrecursion': '16', 'maxfiles': '10000',
    'logverbose': '0', 'fc_logverbose': '0', 'fc_databasemirror': 'mirror.example.org',
    'fc_timeout': '60', 'fc_malwareexpert': '0', 'fc_blurl': '0', 'fc_jurlbla': '0', 'fc_bofhland': '0',
}
CICAP_PAGE = {
    'enabled': '1', 'timeout': '300', 'maxkeepaliverequests': '100', 'keepalivetimeout': '600',
    'startservers': '3', 'maxservers': '10', 'minsparethreads': '10', 'maxsparethreads': '20',
    'threadsperchild': '10', 'maxrequestsperchild': '0', 'listenaddress': '::1', 'serveradmin': '',
    'servername': '', 'enable_accesslog': '1', 'localSquid': '1',
}
AV_PAGE = {
    'enable_clamav': '1', 'scanfiletypes': _opt(['ARCHIVE', 'EXECUTABLE'], TYPES), 'sendpercentdata': '5',
    'startsendpercentdataafter': '2M', 'allow204responses': '1', 'passonerror': '0', 'maxobjectsize': '5M',
}
PAGES = {ClamavGeneral: CLAMAV_PAGE, CicapGeneral: CICAP_PAGE, CicapAntivirus: AV_PAGE}
ARGS = {
    ClamavGeneral: CLAMAV_GENERAL_MOD_ARGS,
    CicapGeneral: CICAP_GENERAL_MOD_ARGS,
    CicapAntivirus: CICAP_ANTIVIRUS_MOD_ARGS,
}


def _entry(mocker, cls, declared: dict):
    mocker.patch.object(cls, 'search', return_value=dict(PAGES[cls]))
    m = mocker.MagicMock()
    m.check_mode = True
    # what AnsibleModule hands over: every argument, None where undeclared
    m.params = {**{k: None for k in ARGS[cls]}, 'debug': False, 'reload': False, **declared}
    e = cls(module=m, result={'changed': False, 'diff': {}}, session=mocker.MagicMock())
    e.check()
    return e


@pytest.mark.parametrize('cls', [ClamavGeneral, CicapGeneral, CicapAntivirus])
def test_every_argument_is_a_field(cls):
    assert sorted(ARGS[cls]) == sorted(cls.FIELDS_ALL)


@pytest.mark.parametrize('cls, declared, posted', [
    (ClamavGeneral, {'fc_enabled': False}, {'general': {'fc_enabled': 0}}),
    (CicapGeneral, {'local_squid': False, 'timeout': 600}, {'general': {'localSquid': 0, 'timeout': 600}}),
    (CicapAntivirus, {'scanfiletypes': ['GIF', 'ARCHIVE']}, {'antivirus': {'scanfiletypes': 'ARCHIVE,GIF'}}),
])
def test_only_declared_fields_are_posted(mocker, cls, declared, posted):
    e = _entry(mocker, cls, declared)
    e.update()
    assert e.r['changed']
    assert e._get_request_data() == posted


@pytest.mark.parametrize('cls, declared', [
    (ClamavGeneral, {'enabled': True, 'maxthreads': 10, 'maxscansize': '100M', 'disablecache': '0'}),
    (CicapGeneral, {'enabled': True, 'timeout': 300, 'listenaddress': '::1', 'local_squid': True}),
    (CicapAntivirus, {'enable_clamav': True, 'scanfiletypes': ['EXECUTABLE', 'ARCHIVE'], 'maxobjectsize': '5M'}),
])
def test_unchanged_reports_ok(mocker, cls, declared):
    e = _entry(mocker, cls, declared)
    e.update()
    assert not e.r['changed']


def test_undeclared_differing_field_is_left_alone(mocker):
    # the appliance runs a custom mirror; a play declaring only 'enabled' keeps it
    e = _entry(mocker, ClamavGeneral, {'enabled': True})
    e.update()
    assert not e.r['changed']
    assert 'fc_databasemirror' not in e.r['diff']['after']


def test_nothing_declared_posts_nothing(mocker):
    e = _entry(mocker, CicapGeneral, {})
    e.update()
    assert not e.r['changed']
    assert e._get_request_data() == {'general': {}}
