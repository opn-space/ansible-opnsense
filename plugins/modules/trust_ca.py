#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/core/blob/master/src/opnsense/mvc/app/controllers/OPNsense/Trust/Api/

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import OPN_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.trust import TRUST_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust import TrustCa

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION: imports an existing certificate authority (System - Trust), matched on its
# description. Changing 'crt' or 'prv' replaces the payload; the refid stays.


def run_module():
    module_args = dict(
        **TRUST_MOD_ARGS,
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

    module_wrapper(TrustCa(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
