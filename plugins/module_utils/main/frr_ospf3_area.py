from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


# An OSPFv3 area record - new in os-frr 2.0, which makes the OSPFv3 interface
# 'area' a relation to it. os-frr 1.x has no OSPFv3 area records at all.
class Area(BaseModule):
    FIELD_ID = 'id'
    CMDS = {
        'add': 'addArea',
        'del': 'delArea',
        'set': 'setArea',
        'search': 'get',
        'toggle': 'toggleArea',
    }
    API_KEY_PATH = 'ospf6.areas.area'
    API_MOD = 'quagga'
    API_CONT = 'ospf6settings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = ['type', 'ranges', 'prefix_list_in', 'prefix_list_out']
    FIELDS_ALL = [FIELD_ID, 'enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'prefix_list_in': 'linkedPrefixlistIn',
        'prefix_list_out': 'linkedPrefixlistOut',
    }
    FIELDS_TYPING = {
        'bool': ['enabled'],
        'list': ['ranges'],
        'select': ['type', 'prefix_list_in', 'prefix_list_out'],
    }
    EXIST_ATTR = 'area'
    SEARCH_ADDITIONAL = {
        'existing_prefixes': 'ospf6.prefixlists.prefixlist',
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.area = {}
        self.existing_prefixes = None

    def check(self) -> None:
        self._base_check()

        if self.p['state'] != 'present':
            return

        self.find_single_link(field='prefix_list_in', existing=self.existing_prefixes)
        self.find_single_link(field='prefix_list_out', existing=self.existing_prefixes)

    def _search_path_handling(self, data: dict, ak_path: str = None) -> dict:
        if ak_path is None and isinstance(data, dict) and 'ospf6' in data and \
                'areas' not in data['ospf6']:
            self.m.fail_json(
                'os-frr < 2.0 has no OSPFv3 area records; set the area on frr_ospf3_interface'
            )

        return BaseModule._search_path_handling(self, data=data, ak_path=ak_path)

    def get_existing(self) -> list:
        existing = []

        for entry in self._base_get_existing():
            for field in ['prefix_list_in', 'prefix_list_out']:
                if entry.get(field) not in [None, ''] and entry[field] in self.existing_prefixes:
                    entry[field] = self.existing_prefixes[entry[field]]['name']

            existing.append(entry)

        return existing
