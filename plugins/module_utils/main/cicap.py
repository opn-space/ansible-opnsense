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
    API_MOD = 'cicap'
    API_CONT = 'general'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'enabled', 'enable_accesslog', 'local_squid', 'timeout', 'maxkeepaliverequests',
        'keepalivetimeout', 'startservers', 'maxservers', 'minsparethreads', 'maxsparethreads',
        'threadsperchild', 'maxrequestsperchild', 'listenaddress', 'serveradmin', 'servername',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TRANSLATE = {
        'local_squid': 'localSquid',
    }
    FIELDS_TYPING = {
        'bool': [
            'enabled', 'enable_accesslog', 'local_squid',
        ],
        'int': [
            'timeout', 'maxkeepaliverequests', 'keepalivetimeout', 'startservers', 'maxservers',
            'minsparethreads', 'maxsparethreads', 'threadsperchild', 'maxrequestsperchild',
        ],
    }
    TIMEOUT = 60.0

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        declared_only(self)
        self._base_check()


class Antivirus(GeneralModule):
    CMDS = {
        'set': 'set',
        'search': 'get',
    }
    API_KEY_PATH = 'antivirus'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'cicap'
    API_CONT = 'antivirus'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'enable_clamav', 'allow204responses', 'passonerror', 'sendpercentdata',
        'startsendpercentdataafter', 'maxobjectsize', 'scanfiletypes',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TYPING = {
        'bool': [
            'enable_clamav', 'allow204responses', 'passonerror',
        ],
        'int': [
            'sendpercentdata',
        ],
        'list': [
            'scanfiletypes',
        ],
    }
    TIMEOUT = 60.0

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        declared_only(self)
        self._base_check()
