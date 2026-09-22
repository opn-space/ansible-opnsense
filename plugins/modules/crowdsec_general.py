#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/plugins/tree/master/security/crowdsec

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.crowdsec_general import General

except MODULE_EXCEPTIONS:
    module_dependency_error()


def run_module():
    # Every default below is the model's own default, taken from
    # security/crowdsec/.../models/OPNsense/CrowdSec/General.xml. A
    # GeneralModule posts the WHOLE page on every run, so a default that
    # disagreed with the model would silently rewrite a field the caller never
    # declared.
    module_args = dict(
        agent_enabled=dict(
            type='bool', required=False, default=True,
            description='Whether the CrowdSec agent parses the logs and decides'
        ),
        lapi_enabled=dict(
            type='bool', required=False, default=True,
            description='Whether the local API runs on this appliance'
        ),
        firewall_bouncer_enabled=dict(
            type='bool', required=False, default=True,
            description='Whether the firewall bouncer maintains the block tables. '
                        'It creates the aliases crowdsec_blocklists and crowdsec6_blocklists '
                        'for itself at filter-reload time'
        ),
        lapi_manual_configuration=dict(
            type='bool', required=False, default=False,
            description='Whether the local API connection is configured by hand'
        ),
        lapi_listen_address=dict(
            type='str', required=False, default='127.0.0.1', aliases=['lapi_address'],
            description='The address the local API listens on - an IP, without a netmask'
        ),
        lapi_listen_port=dict(
            type='int', required=False, default=8080, aliases=['lapi_port'],
            description='The port the local API listens on'
        ),
        rules_enabled=dict(
            type='bool', required=False, default=True,
            description='Whether the bouncer installs its own firewall rules'
        ),
        rules_log=dict(
            type='bool', required=False, default=False,
            description='Whether the bouncer logs what its rules block'
        ),
        rules_tag=dict(
            type='str', required=False, default='',
            description='Optional tag added to the rules the bouncer installs. '
                        'Alphanumeric, at most 63 characters'
        ),
        enroll_key=dict(
            type='str', required=False, default='', no_log=True,
            description='The enrollment key that registers this instance with the CrowdSec console. '
                        'Alphanumeric, at most 63 characters'
        ),
        crowdsec_firewall_verbose=dict(
            type='bool', required=False, default=False,
            description='Whether the firewall bouncer logs verbosely'
        ),
        **OPN_MOD_ARGS,
        **RELOAD_MOD_ARG,
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        }
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module_wrapper(General(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
