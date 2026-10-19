from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


# An area record. os-frr 1.x has id and type; os-frr 2.0 adds the area ranges
# and prefix-list filters that used to live on the OSPF network, and makes the
# interface and network 'area' a relation to this record.
class Area(BaseModule):
    FIELD_ID = 'id'
    CMDS = {
        'add': 'addArea',
        'del': 'delArea',
        'set': 'setArea',
        'search': 'get',
        'toggle': 'toggleArea',
    }
    API_KEY_PATH = 'ospf.areas.area'
    API_MOD = 'quagga'
    API_CONT = 'ospfsettings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = ['type', 'ranges', 'prefix_list_in', 'prefix_list_out']
    FIELDS_ALL = [FIELD_ID, 'enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_OS_FRR_2 = ['ranges', 'prefix_list_in', 'prefix_list_out']
    FIELDS_OPTIONAL = FIELDS_OS_FRR_2
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
        'existing_prefixes': 'ospf.prefixlists.prefixlist',
        # the whole page, read for its shape: os-frr 2.0 has no 'passiveinterfaces'
        'ospf_settings': 'ospf',
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.area = {}
        self.existing_prefixes = None
        self.ospf_settings = None

    @property
    def os_frr_2(self) -> bool:
        return isinstance(self.ospf_settings, dict) and 'passiveinterfaces' not in self.ospf_settings

    def check(self) -> None:
        self._base_check()

        if self.p['state'] != 'present':
            return

        if not self.os_frr_2:
            used = [f for f in self.FIELDS_OS_FRR_2 if not is_unset(self.p[f])]
            if len(used) > 0:
                self.m.fail_json(
                    f"{', '.join(used)} on an OSPF area needs os-frr 2.0; "
                    'on os-frr < 2.0 they belong to frr_ospf_network'
                )

            return

        self.find_single_link(field='prefix_list_in', existing=self.existing_prefixes)
        self.find_single_link(field='prefix_list_out', existing=self.existing_prefixes)

    def get_existing(self) -> list:
        existing = []

        for entry in self._base_get_existing():
            for field in ['prefix_list_in', 'prefix_list_out']:
                if entry.get(field) not in [None, ''] and entry[field] in self.existing_prefixes:
                    entry[field] = self.existing_prefixes[entry[field]]['name']

            existing.append(entry)

        return existing
