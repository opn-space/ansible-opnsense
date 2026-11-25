#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/core/tree/master/src/opnsense/mvc/app/controllers/OPNsense/Trust/Api

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import \
        module_multi_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.multi import build_multi_mod_args
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import OPN_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.trust import TRUST_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust import TrustCert

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION: mass-manage imported certificates - one search for all entries


def run_module():
    entry_multi_args = build_multi_mod_args(
        mod_args=TRUST_MOD_ARGS,
        aliases=['certificates', 'certs'],
        not_required=['description'],
    )

    module_args = dict(
        **entry_multi_args,
        **OPN_MOD_ARGS,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_one_of=[
            ('multi', 'multi_purge', 'multi_control.purge_all'),
        ],
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        }
    )

    module_multi_wrapper(
        module=module,
        result=result,
        obj=TrustCert,
        kind='cert',
        entry_args=entry_multi_args,
    )
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
