#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/plugins/tree/master/www/c-icap

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.clamav_cicap import CICAP_ANTIVIRUS_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.cicap import Antivirus

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION: a settings page; only the arguments declared are compared and
# posted - every other field keeps the value the appliance holds.


def run_module():
    module_args = dict(
        **CICAP_ANTIVIRUS_MOD_ARGS,
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

    module_wrapper(Antivirus(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
