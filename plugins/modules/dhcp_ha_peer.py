#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/core/kea.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.dhcp_ha_peer import HAPeer

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/dhcp.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/dhcp.html'


def run_module():
    module_args = dict(
        name=dict(
            type='str', required=True, aliases=['peer'],
            description='Name of this peer. Kea matches the node against this list by name, so on '
                        'a pair that leaves dhcp_ha.this_server_name empty these must be the two '
                        'appliances\' hostnames.',
        ),
        role=dict(
            type='str', required=False, default='primary', choices=['primary', 'standby'],
            description='Whether this peer leads the relationship or stands by for it. Exactly '
                        'one primary and one standby make a pair.',
        ),
        url=dict(
            type='str', required=False, default='', aliases=['peer_url'],
            description='The Kea control agent of that peer, e.g. http://10.0.0.2:8000',
        ),
        ipv=dict(type='int', required=False, default=4, choices=[4, 6], aliases=['ip_version']),
        **RELOAD_MOD_ARG,
        **STATE_MOD_ARG,
        **OPN_MOD_ARGS,
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

    if module.params['ipv'] == 6:
        module.fail_json('DHCPv6 is not yet supported!')

    module_wrapper(HAPeer(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
