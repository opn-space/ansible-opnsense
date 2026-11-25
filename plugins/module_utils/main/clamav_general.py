from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.declared import declared_only


class General(GeneralModule):
    CMDS = {
        'set': 'set',
        'search': 'get',
    }
    API_KEY_PATH = 'general'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'clamav'
    API_CONT = 'general'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'enabled', 'fc_enabled', 'enabletcp', 'followdirsym', 'followfilesym', 'scanpe', 'scanelf',
        'detectbroken', 'scanole2', 'ole2blockmarcros', 'scanpdf', 'scanswf', 'scanxmldocs',
        'scanhwp3', 'scanmailfiles', 'scanhtml', 'scanarchive', 'arcblockenc', 'logverbose',
        'fc_logverbose', 'fc_malwareexpert', 'fc_blurl', 'fc_jurlbla', 'fc_bofhland', 'maxthreads',
        'maxqueue', 'idletimeout', 'maxdirrecursion', 'maxrecursion', 'maxfiles', 'disablecache',
        'maxscansize', 'maxfilesize', 'fc_databasemirror', 'fc_timeout',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TYPING = {
        'bool': [
            'enabled', 'fc_enabled', 'enabletcp', 'followdirsym', 'followfilesym', 'scanpe',
            'scanelf', 'detectbroken', 'scanole2', 'ole2blockmarcros', 'scanpdf', 'scanswf',
            'scanxmldocs', 'scanhwp3', 'scanmailfiles', 'scanhtml', 'scanarchive', 'arcblockenc',
            'logverbose', 'fc_logverbose', 'fc_malwareexpert', 'fc_blurl', 'fc_jurlbla',
            'fc_bofhland',
        ],
        'int': [
            'maxthreads', 'maxqueue', 'idletimeout', 'maxdirrecursion', 'maxrecursion', 'maxfiles',
        ],
    }
    TIMEOUT = 60.0

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        declared_only(self)
        self._base_check()
