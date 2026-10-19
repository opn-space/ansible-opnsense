#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, opn-it
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/plugins/quagga.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf_area import Area

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/frr_ospf.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/frr_ospf.html'


def run_module():
    module_args = dict(
        id=dict(
            type='str', required=True, aliases=['area'],
            description='Area ID in dotted format like 0.0.0.1'
        ),
        type=dict(
            type='str', required=False, default='',
            choices=['', 'stub', 'stub no-summary', 'nssa', 'nssa no-summary'],
            description="Area type; '' is a normal area (os-frr 2.0; os-frr < 2.0 requires one of the others)",
        ),
        ranges=dict(
            type='list', elements='str', required=False, default=[],
            description='Networks summarized for this area (os-frr 2.0 and later)',
        ),
        prefix_list_in=dict(
            type='str', required=False, aliases=['prefix_in', 'pre_in'],
            description='Prefix-List filtering inbound (os-frr 2.0 and later)',
        ),
        prefix_list_out=dict(
            type='str', required=False, aliases=['prefix_out', 'pre_out'],
            description='Prefix-List filtering outbound (os-frr 2.0 and later)',
        ),
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

    module_wrapper(Area(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
