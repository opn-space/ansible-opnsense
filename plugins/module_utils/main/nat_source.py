from re import compile as re_compile, IGNORECASE

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.rule import \
    validate_values
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


# Synthetic outbound NAT rules are reported by search_rule with an identifier
# that is not a uuid - 'automatic_wan', 'automatic_isakmp_wan'. They do not exist
# in the configuration and cannot be set or deleted.
SYNTHETIC_RULE_ID = re_compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    flags=IGNORECASE,
)


class SNat(BaseModule):
    # OPNsense 26.7 stopped returning the rules from firewall/source_nat/get.
    #
    # SourceNatController gained an explicit getAction() that returns only the
    # 'general' node; before that it inherited ApiMutableModelControllerBase's,
    # which returned the whole model - so 'filter.snatrules.rule' resolved and
    # this module read the ruleset from one call. On 26.7 that path is absent and
    # the module fails with "Got invalid API_KEY_PATH: 'filter.snatrules.rule'".
    #
    # The rules moved to searchRuleAction/getRuleAction, which is the shape the
    # rest of the collection already calls the "new OPNsense API": a search for
    # the list, a detail call per entry. API_KEY_PATH becomes 'rule' because
    # getRuleAction returns getBase("rule", "snatrules.rule", $uuid), i.e.
    # {"rule": {...}}. The write path is unaffected - the request payload is
    # wrapped in the last segment of API_KEY_PATH, which was 'rule' before and
    # is 'rule' now.
    #
    # This is compatible with 26.1: searchRuleAction and getRuleAction exist
    # there too, and are what the GUI has always used.
    CMDS = {
        'add': 'add_rule',
        'del': 'del_rule',
        'set': 'set_rule',
        'search': 'search_rule',
        'detail': 'get_rule',
        'toggle': 'toggle_rule',
    }
    API_KEY_PATH = 'rule'
    API_MOD = 'firewall'
    API_CONT = 'source_nat'
    FIELDS_CHANGE = [
        'sequence', 'no_nat', 'interface', 'target', 'target_port', 'description',
        'ip_protocol', 'protocol', 'source_invert', 'source_net', 'source_port',
        'destination_invert', 'destination_net', 'destination_port', 'log', 'static_port',
    ]
    FIELDS_ALL = ['enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    FIELDS_TRANSLATE = {
        'ip_protocol': 'ipprotocol',
        'source_invert': 'source_not',
        'destination_invert': 'destination_not',
        'no_nat': 'nonat',
        'static_port': 'staticnatport',
    }
    FIELDS_TYPING = {
        'bool': ['enabled', 'log', 'source_invert', 'no_nat', 'destination_invert', 'static_port'],
        'list': [],
        'select': ['interface', 'ip_protocol', 'protocol'],
        'int': [],
    }
    INT_VALIDATIONS = {
        'sequence': {'min': 1, 'max': 99999},
    }
    EXIST_ATTR = 'rule'
    API_CMD_REL = 'apply'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.rule = {}

    def api_search_post(self, cnf: dict, data: dict = None) -> list:
        # Drop the synthetic rules OPNsense adds to searchRuleAction's output.
        #
        # With snat_mode 'automatic' or 'hybrid' the controller appends
        # getAutomaticOutboundNatRules() to the configured ones. Those entries
        # are display-only: getRuleAction cannot resolve their identifier, and a
        # declarative caller that treated them as existing rules would try to
        # delete them on every run.
        return [
            entry for entry in super().api_search_post(cnf=cnf, data=data)
            if SYNTHETIC_RULE_ID.match(str(entry.get('uuid', '')))
        ]

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['interface']):
                self.m.fail_json(
                    "You need to provide an 'interface' to create a source-nat rule!"
                )

            if is_unset(self.p['target']):
                self.m.fail_json(
                    "You need to provide an 'target' to create a source-nat rule!"
                )

        self._build_log_name()
        self.find(match_fields=self.p['match_fields'])

        if self.p['state'] == 'present':
            validate_values(module=self.m, cnf=self.p, error_func=self.m.fail_json, kind='nat')

        self._base_check()

    def _build_log_name(self) -> str:
        if self.p['description'] not in [None, '']:
            log_name = self.p['description']

        else:
            log_name = 'FROM '

            if self.p['source_invert']:
                log_name += 'NOT '

            log_name += f"{self.p['source_net']} <= PROTO {self.p['protocol']} => "

            if self.p['destination_invert']:
                log_name += 'NOT '

            log_name += f"{self.p['destination_net']}:{self.p['destination_port']} "
            log_name += f" =NAT=> {self.p['target']}:{self.p['target_port']}"

        return log_name
