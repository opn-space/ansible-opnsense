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
    API_KEY_PATH = 'ospf6.interfaces.interface'
    API_MOD = 'quagga'
    API_CONT = 'ospf6settings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'interface', 'area', 'passive', 'cost', 'cost_demoted', 'carp_depend_on',
        'hello_interval', 'dead_interval', 'retransmit_interval', 'transmit_delay',
        'priority', 'network_type',
    ]
    FIELDS_ALL = ['enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    INT_VALIDATIONS = {
        'cost': {'min': 0, 'max': 4294967295},
        'hello_interval': {'min': 0, 'max': 4294967295},
        'dead_interval': {'min': 0, 'max': 4294967295},
        'retransmit_interval': {'min': 0, 'max': 4294967295},
        'transmit_delay': {'min': 0, 'max': 4294967295},
        'priority': {'min': 0, 'max': 4294967295},
        'cost_demoted': {'min': 1, 'max': 65535},
    }
    FIELDS_TRANSLATE = {
        'interface': 'interfacename',
        'hello_interval': 'hellointerval',
        'dead_interval': 'deadinterval',
        'retransmit_interval': 'retransmitinterval',
        'transmit_delay': 'transmitdelay',
        'network_type': 'networktype',
    }
    FIELDS_TYPING = {
        'bool': ['enabled', 'passive'],
        'select': ['interface', 'carp_depend_on', 'network_type', 'area'],
    }
    EXIST_ATTR = 'int'
    SEARCH_ADDITIONAL = {
        # the whole page: its areas, and its shape (os-frr 2.0 has no 'networks')
        'ospf6_settings': 'ospf6',
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.int = {}
        self.ospf6_settings = None

    @property
    def os_frr_2(self) -> bool:
        return isinstance(self.ospf6_settings, dict) and 'networks' not in self.ospf6_settings

    def simplify_existing(self, existing: dict) -> dict:
        simple = self._base_simplify_existing(existing)
        if 'area' in simple:
            simple['area'] = area_to_id(get_areas(self.ospf6_settings), simple['area'])

        return simple

    def build_request(self) -> dict:
        area = self.p['area']
        if self.os_frr_2 and self.p['state'] == 'present':
            self.p['area'] = area_to_uuid(self.m, get_areas(self.ospf6_settings), area, 'frr_ospf3_area')

        request = self._base_build_request()
        self.p['area'] = area
        return request

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['area']):
                self.m.fail_json(
                    'To create a OSPFv3 interface you need to provide its area!'
                )

        self._base_check()
