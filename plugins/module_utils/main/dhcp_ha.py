from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule


class HA(GeneralModule):
    """
    The 'ha' node of OPNsense's Kea DHCPv4 model, which is what turns two Kea
    servers into one highly-available pair instead of two servers answering the
    same DISCOVERs from the same pools.

    It is a sibling of dhcp_general rather than part of it: API_KEY_PATH is
    fixed per class, the two nodes are 'dhcpv4.general' and 'dhcpv4.ha', and
    OPNsense's setAction only writes the nodes a request actually carries - so
    two modules can each own their own node without overwriting the other's.
    """
    CMDS = {
        'set': 'set',
        'search': 'get'
    }
    API_KEY_PATH = 'dhcpv4.ha'
    API_KEY_PATH_REQ = API_KEY_PATH
    API_MOD = 'kea'
    API_CONT = 'dhcpv4'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'enabled', 'this_server_name', 'max_unacked_clients',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    FIELDS_TYPING = {
        'bool': ['enabled'],
        'int': ['max_unacked_clients'],
    }
    INT_VALIDATIONS = {
        'max_unacked_clients': {'min': 0, 'max': 65535},
    }

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)
