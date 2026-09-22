from re import match as regex_match

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.validate import \
    is_ip


# Supported as of the os-crowdsec plugin 1.0.12
class General(GeneralModule):
    CMDS = {
        'set': 'set',
        'search': 'get',
    }
    # The controller is an ApiMutableModelControllerBase with
    # $internalModelName = 'general', so crowdsec/general/get answers
    # {"general": {...}} - a flat page, one level deep. Measured on 26.7.3_11
    # with os-crowdsec installed; it is NOT nested under the plugin name the way
    # ids/settings/get nests its page under "ids".
    API_KEY_PATH = 'general'
    API_MOD = 'crowdsec'
    API_CONT = 'general'
    # crowdsec/service/reconfigure, and it has to be that one: the plugin
    # OVERRIDES reconfigureAction() to run the configd action `crowdsec
    # reconfigure` after the default reconfigure, which is what renders
    # config.yaml and config-firewall-bouncer.yaml. Any other apply writes the
    # page and leaves the daemon on its old files.
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'agent_enabled', 'lapi_enabled', 'firewall_bouncer_enabled',
        'lapi_manual_configuration', 'lapi_listen_address', 'lapi_listen_port',
        'rules_enabled', 'rules_log', 'rules_tag', 'enroll_key',
        'crowdsec_firewall_verbose',
    ]
    FIELDS_ALL = FIELDS_CHANGE
    # The model is flat - no ArrayField and no OptionField - so the argument
    # names are the field names and there is nothing to translate or unwrap.
    FIELDS_TYPING = {
        'bool': [
            'agent_enabled', 'lapi_enabled', 'firewall_bouncer_enabled',
            'lapi_manual_configuration', 'rules_enabled', 'rules_log',
            'crowdsec_firewall_verbose',
        ],
        'int': ['lapi_listen_port'],
    }
    INT_VALIDATIONS = {
        'lapi_listen_port': {'min': 1, 'max': 65535},
    }
    # The model's own pattern for rules_tag and enroll_key.
    STR_PATTERN = r'^[0-9a-zA-Z]{1,63}$'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None):
        GeneralModule.__init__(self=self, m=module, r=result, s=session)

    def check(self) -> None:
        # Validated here rather than through STR_VALIDATIONS, and the guard is
        # the point. validate_str_fields() is called with allow_empty=False, so
        # it FAILS an unset field outright - and rules_tag and enroll_key are
        # empty on every appliance that has not set them, which is every stock
        # one. That is exactly the defect this collection carried in
        # unbound_general's dns64_prefix: a GeneralModule posts the whole page,
        # so a settings page nobody could declare was a settings page nobody
        # could leave alone.
        for field in ['rules_tag', 'enroll_key']:
            if not is_unset(self.p[field]) and \
                    regex_match(self.STR_PATTERN, str(self.p[field])) is None:
                self.m.fail_json(
                    f"Value of field '{field}' is not valid - "
                    f"must match the regex '{self.STR_PATTERN}'"
                )

        if not is_unset(self.p['lapi_listen_address']) and \
                not is_ip(self.p['lapi_listen_address']):
            self.m.fail_json(
                "Value of field 'lapi_listen_address' is not valid - "
                "must be an IP address without a netmask"
            )

        self._base_check()
