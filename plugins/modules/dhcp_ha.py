#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/core/kea.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        EN_ONLY_MOD_ARG, OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.dhcp_ha import HA

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/dhcp.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/dhcp.html'


def run_module():
    module_args = dict(
        this_server_name=dict(
            type='str', required=False, default='', aliases=['server_name'],
            description='Which entry of the peer list is THIS node. Left empty - which is the '
                        'default and usually what you want - Kea uses this appliance\'s own '
                        'hostname instead, so a peer list naming both nodes by hostname needs no '
                        'per-node value at all. That matters on a pair: the whole OPNsense.Kea '
                        'section is replicated by the HA configuration sync, so a value set here '
                        'on the master is copied onto the backup and would give both nodes the '
                        'same identity.',
        ),
        max_unacked_clients=dict(
            type='int', required=False, default=2, aliases=['unacked_clients'],
            description='How many clients may go unanswered by the peer before this node decides '
                        'the peer is down and starts serving its share of the pool.',
        ),
        ipv=dict(type='int', required=False, default=4, choices=[4, 6], aliases=['ip_version']),
        **EN_ONLY_MOD_ARG,
        **RELOAD_MOD_ARG,
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

    module_wrapper(HA(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
