from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip_or_network, is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class Network(BaseModule):
    CMDS = {
        'add': 'addNetwork',
        'del': 'delNetwork',
        'set': 'setNetwork',
        'search': 'get',
        'toggle': 'toggleNetwork',
    }
    API_KEY_PATH = 'ospf.networks.network'
    API_MOD = 'quagga'
    API_CONT = 'ospfsettings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = ['ip', 'mask', 'area', 'area_range', 'prefix_list_in', 'prefix_list_out']
    FIELDS_ALL = ['enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'ip': 'ipaddr',
        'mask': 'netmask',
        'area_range': 'arearange',
        'prefix_list_in': 'linkedPrefixlistIn',
        'prefix_list_out': 'linkedPrefixlistOut',
    }
    # os-frr 2.0 moved area ranges and the prefix-list filters from the network
    # onto the area (ospf.areas.area: ranges, linkedPrefixlistIn/Out).
    FIELDS_OPTIONAL = ['area_range', 'prefix_list_in', 'prefix_list_out']
    FIELDS_TYPING = {
        'bool': ['enabled'],
        'select': ['prefix_list_in', 'prefix_list_out'],
    }
    INT_VALIDATIONS = {
        'mask': {'min': 0, 'max': 32},
    }
    EXIST_ATTR = 'net'
    SEARCH_ADDITIONAL = {
        'existing_prefixes': 'ospf.prefixlists.prefixlist',
        # the whole page, read for its shape: os-frr 2.0 has no 'passiveinterfaces'
        'ospf_settings': 'ospf',
    }
    FIELDS_MOVED_TO_AREA = ['area_range', 'prefix_list_in', 'prefix_list_out']

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.net = {}
        self.existing_prefixes = None
        self.ospf_settings = None

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['area']):
                self.m.fail_json(
                    'To create a OSPF network you need to provide an area!'
                )

            if not is_ip_or_network(f"{self.p['ip']}/{self.p['mask']}", strict=True):
                self.m.fail_json(
                    'The combination of the provided ip and network mask is invalid: '
                    f"'{self.p['ip']}/{self.p['mask']}'!"
                )

        self._base_check()

        if self.p['state'] == 'present' and self.ospf_settings is not None and \
                'passiveinterfaces' not in self.ospf_settings:
            moved = [f for f in self.FIELDS_MOVED_TO_AREA if not is_unset(self.p[f])]
            if len(moved) > 0:
                self.m.fail_json(
                    f"os-frr 2.0 moved {', '.join(moved)} from the OSPF network to the area; "
                    'declare it with frr_ospf_area'
                )

            return

        if self.p['state'] == 'present':
            self.find_single_link(
                field='prefix_list_in',
                existing=self.existing_prefixes,
            )
            self.find_single_link(
                field='prefix_list_out',
                existing=self.existing_prefixes,
            )

    def get_existing(self) -> list:
        existing = []

        for entry in self._base_get_existing():
            if entry.get('prefix_list_in') not in [None, ''] and \
                    entry['prefix_list_in'] in self.existing_prefixes:
                entry['prefix_list_in'] = self.existing_prefixes[entry['prefix_list_in']]['name']

            if entry.get('prefix_list_out') not in [None, ''] and \
                    entry['prefix_list_out'] in self.existing_prefixes:
                entry['prefix_list_out'] = self.existing_prefixes[entry['prefix_list_out']]['name']

            existing.append(entry)

        return existing
