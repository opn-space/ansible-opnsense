from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip, is_network, is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.translate import \
    get_selected_list, simplify_translate
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class ReservationV4(BaseModule):
    FIELD_ID = 'ip'
    CMDS = {
        'add': 'add_reservation',
        'del': 'del_reservation',
        'set': 'set_reservation',
        'search': 'search_reservation',
        'detail': 'get_reservation',
    }
    API_KEY_PATH = 'reservation'
    API_MOD = 'kea'
    API_CONT = 'dhcpv4'
    API_CONT_REL = 'service'
    API_ATTR_OPTIONS = 'option_data'
    # The per-host DHCP options. Deliberately the same argument names
    # dhcp_subnet uses for the same options, so the two read alike - an option
    # set here overrides the one the subnet offers.
    #
    # It is a SUBSET of the subnet's on purpose: OPNsense's Kea model gives a
    # reservation no 'v6_only_preferred' and no 'option_data_autocollect', so
    # this module has neither 'v6_only_preferred' nor 'auto_options'. Offering
    # them would be offering a value the appliance drops.
    API_FIELDS_OPTIONS = [
        'gateway', 'routes', 'dns', 'domain', 'domain_search', 'ntp_servers',
        'time_servers', 'tftp_server', 'tftp_file',
    ]
    # The identity and the plain fields. The options are NOT here: they are
    # written by build_request() below, nested under option_data, and
    # _base_build_request() would otherwise also write them flat.
    FIELDS_ALL = [FIELD_ID, 'mac', 'hostname', 'description', 'subnet']
    FIELDS_CHANGE = ['mac', 'hostname', 'description', 'subnet']
    FIELDS_CHANGE.extend(API_FIELDS_OPTIONS)
    FIELDS_TYPING = {
        'select': ['subnet'],
        'list': ['dns', 'domain_search', 'gateway', 'ntp_servers', 'time_servers'],
    }
    FIELDS_TRANSLATE = {
        'ip': 'ip_address',
        'mac': 'hw_address',
    }
    FIELDS_TRANSLATE_SPECIAL = {
        'dns': 'domain_name_servers',
        'domain': 'domain_name',
        'gateway': 'routers',
        'routes': 'static_routes',
        'tftp_server': 'tftp_server_name',
        'tftp_file': 'boot_file_name',
    }
    # Both shapes of the raw option data, because the appliance answers in two:
    # a get/detail call nests them under 'option_data', a search call flattens
    # them into dotted keys. Either way they are re-read below under this
    # module's own names, so the raw ones must not reach the diff.
    API_FIELDS_IGNORE = [
        'option_data',
        'option_data.boot_file_name',
        'option_data.classless_static_route',
        'option_data.domain_name',
        'option_data.domain_name_servers',
        'option_data.domain_search',
        'option_data.ntp_servers',
        'option_data.routers',
        'option_data.static_routes',
        'option_data.tftp_server_name',
        'option_data.time_servers',
    ]
    API_FIELDS_IGNORE.extend(API_FIELDS_OPTIONS)
    EXIST_ATTR = 'reservation'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.reservation = {}
        self.existing_reservations = None
        self.existing_subnets = None

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['mac']):
                self.m.fail_json(
                    "You need to provide a 'mac' if you want to create a reservation!"
                )

            if is_unset(self.p['subnet']) or not is_network(self.p['subnet']):
                self.m.fail_json('The provided subnet is invalid!')

            if not is_ip(self.p['ip']):
                self.m.fail_json('The provided IP is invalid!')

        self._base_check()

        if self.p['state'] == 'present':
            self._search_subnets()
            if not self._find_subnet():
                self.m.fail_json('Provided subnet not found!')

    def simplify_existing(self, entry: dict) -> dict:
        simple = simplify_translate(
            existing=entry,
            typing=self.FIELDS_TYPING,
            translate=self.FIELDS_TRANSLATE,
            ignore=self.API_FIELDS_IGNORE,
        )

        if self.API_ATTR_OPTIONS in entry:
            # get/details call
            opts = entry[self.API_ATTR_OPTIONS]
            return {
                **simple,
                'dns': get_selected_list(opts[self.FIELDS_TRANSLATE_SPECIAL['dns']], remove_empty=True),
                'domain_search': get_selected_list(opts['domain_search'], remove_empty=True),
                'gateway': get_selected_list(opts[self.FIELDS_TRANSLATE_SPECIAL['gateway']], remove_empty=True),
                'routes': opts[self.FIELDS_TRANSLATE_SPECIAL['routes']],
                'domain': opts[self.FIELDS_TRANSLATE_SPECIAL['domain']],
                'ntp_servers': get_selected_list(opts['ntp_servers'], remove_empty=True),
                'time_servers': get_selected_list(opts['time_servers'], remove_empty=True),
                'tftp_server': opts[self.FIELDS_TRANSLATE_SPECIAL['tftp_server']],
                'tftp_file': opts[self.FIELDS_TRANSLATE_SPECIAL['tftp_file']],
            }

        # search-call :'(
        return {
            **simple,
            'dns': entry[f"option_data.{self.FIELDS_TRANSLATE_SPECIAL['dns']}"],
            'domain_search': entry['option_data.domain_search'],
            'gateway': entry[f"option_data.{self.FIELDS_TRANSLATE_SPECIAL['gateway']}"],
            'routes': entry[f"option_data.{self.FIELDS_TRANSLATE_SPECIAL['routes']}"],
            'domain': entry[f"option_data.{self.FIELDS_TRANSLATE_SPECIAL['domain']}"],
            'ntp_servers': entry['option_data.ntp_servers'],
            'time_servers': entry['option_data.time_servers'],
            'tftp_server': entry[f"option_data.{self.FIELDS_TRANSLATE_SPECIAL['tftp_server']}"],
            'tftp_file': entry[f"option_data.{self.FIELDS_TRANSLATE_SPECIAL['tftp_file']}"],
        }

    def build_request(self) -> dict:
        raw_request = self._base_build_request(ignore_fields=self.API_FIELDS_OPTIONS)

        raw_request[self.API_KEY_PATH][self.API_ATTR_OPTIONS] = {
            self.FIELDS_TRANSLATE_SPECIAL['dns']: self.RESP_JOIN_CHAR.join(self.p['dns']),
            self.FIELDS_TRANSLATE_SPECIAL['gateway']: self.RESP_JOIN_CHAR.join(self.p['gateway']),
            self.FIELDS_TRANSLATE_SPECIAL['routes']: self.p['routes'],
            self.FIELDS_TRANSLATE_SPECIAL['domain']: self.p['domain'],
            self.FIELDS_TRANSLATE_SPECIAL['tftp_server']: self.p['tftp_server'],
            self.FIELDS_TRANSLATE_SPECIAL['tftp_file']: self.p['tftp_file'],
            'ntp_servers': self.RESP_JOIN_CHAR.join(self.p['ntp_servers']),
            'time_servers': self.RESP_JOIN_CHAR.join(self.p['time_servers']),
            'domain_search': self.RESP_JOIN_CHAR.join(self.p['domain_search']),
        }

        return raw_request

    def _find_subnet(self) -> bool:
        for s in self.existing_subnets:
            if s['subnet'] == self.p['subnet']:
                self.p['subnet'] = s['uuid']
                self.reservation['subnet'] = s['uuid']
                return True

        return False

    def _search_subnets(self):
        self.existing_subnets = self.s.get(cnf={
            **self.call_cnf, **{'command': 'searchSubnet'}
        })['rows']
