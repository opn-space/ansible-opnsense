from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.frr import \
    get_areas, area_to_id, area_to_uuid
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class Interface(BaseModule):
    CMDS = {
        'add': 'addInterface',
        'del': 'delInterface',
        'set': 'setInterface',
        'search': 'get',
        'toggle': 'toggleInterface',
    }
    API_KEY_PATH = 'ospf.interfaces.interface'
    API_MOD = 'quagga'
    API_CONT = 'ospfsettings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'interface', 'area', 'auth_type', 'auth_key', 'auth_key_id', 'cost',
        'hello_interval', 'dead_interval', 'retransmit_interval', 'transmit_delay',
        'priority', 'network_type', 'carp_depend_on', 'cost_demoted', 'passive',
    ]
    FIELDS_ALL = ['enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    INT_VALIDATIONS = {
        'cost': {'min': 1, 'max': 65535},
        'hello_interval': {'min': 0, 'max': 4294967295},
        'dead_interval': {'min': 0, 'max': 4294967295},
        'retransmit_interval': {'min': 0, 'max': 4294967295},
        'transmit_delay': {'min': 0, 'max': 4294967295},
        'priority': {'min': 0, 'max': 4294967295},
        'cost_demoted': {'min': 1, 'max': 65535},
        'auth_key_id': {'min': 1, 'max': 255},
    }
    FIELDS_TRANSLATE = {
        'interface': 'interfacename',
        'hello_interval': 'hellointerval',
        'dead_interval': 'deadinterval',
        'retransmit_interval': 'retransmitinterval',
        'transmit_delay': 'transmitdelay',
        'network_type': 'networktype',
        'auth_type': 'authtype',
        'auth_key': 'authkey',
        'auth_key_id': 'authkey_id',
    }
    # 'passive' exists on the interface from os-frr 2.0 on (before: frr_ospf_general passive_ints)
    FIELDS_OPTIONAL = ['passive']
    FIELDS_TYPING = {
        'bool': ['enabled', 'passive'],
        'select': ['interface', 'carp_depend_on', 'network_type', 'auth_type', 'area'],
    }
    EXIST_ATTR = 'int'
    SEARCH_ADDITIONAL = {
        # the whole page: its areas, and its shape (os-frr 2.0 has no 'passiveinterfaces')
        'ospf_settings': 'ospf',
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.int = {}
        self.ospf_settings = None

    @property
    def os_frr_2(self) -> bool:
        return isinstance(self.ospf_settings, dict) and 'passiveinterfaces' not in self.ospf_settings

    def simplify_existing(self, existing: dict) -> dict:
        simple = self._base_simplify_existing(existing)
        if 'area' in simple:
            simple['area'] = area_to_id(get_areas(self.ospf_settings), simple['area'])

        return simple

    def build_request(self) -> dict:
        area = self.p['area']
        if self.os_frr_2 and self.p['state'] == 'present':
            self.p['area'] = area_to_uuid(self.m, get_areas(self.ospf_settings), area, 'frr_ospf_area')

        request = self._base_build_request()
        self.p['area'] = area
        return request

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['area']):
                self.m.fail_json(
                    'To create a OSPF interface you need to provide its area!'
                )

            if not is_unset(self.p['auth_type']) and is_unset(self.p['auth_key']):
                self.m.fail_json(
                    'You need to provide an authentication-key if you enable authentication!'
                )

        self._base_check()

        if self.p['state'] == 'present' and self.p['passive'] and \
                isinstance(self.ospf_settings, dict) and not self.os_frr_2:
            self.m.fail_json('Use frr_ospf_general passive_ints on os-frr < 2.0')
