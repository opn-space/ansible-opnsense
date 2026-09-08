from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_unset


class HAPeer(BaseModule):
    """
    One member of the Kea HA relationship. Every node of a pair carries the
    SAME peer list - it is what each Kea uses to find the other - and each node
    picks itself out of that list by name, so the names are shared
    configuration and only the identity is per node.
    """
    FIELD_ID = 'name'
    CMDS = {
        'add': 'add_peer',
        'del': 'del_peer',
        'set': 'set_peer',
        'search': 'search_peer',
        'detail': 'get_peer',
    }
    API_KEY_PATH = 'peer'
    API_MOD = 'kea'
    API_CONT = 'dhcpv4'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = ['role', 'url']
    FIELDS_ALL = [FIELD_ID]
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TYPING = {
        # the API returns the role as a select-list, not as a plain value
        'select': ['role'],
    }
    EXIST_ATTR = 'peer'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.peer = {}
        self.existing_peers = None

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['url']):
                self.m.fail_json("You need to provide an 'url' if you want to create a Kea HA peer!")

        self._base_check()
