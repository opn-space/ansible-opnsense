#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2025, Pascal Rath <contact+opnsense@OXL.at>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/plugins/quagga.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import single_get

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/frr_diagnostic.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/frr_diagnostic.html'

# Every route and neighbour-list view in Quagga's DiagnosticsController is a
# grid search, and its action is named accordingly: searchBgproute4Action,
# searchGeneralroute4Action, searchOspfrouteAction and so on. OPNsense routes
# `search_bgproute4` onto those; the bare `bgproute4` this module used to
# request has no action of any name and answers
# `{"errorMessage":"Endpoint not found"}`.
#
# They answer a grid rather than FRR's own output:
# {"current": 1, "rowCount": 0, "rows": [], "total": 0, "subtitle": "..."}
# - the rows being what a caller wants, and `subtitle` carrying the routerId
# and localAS the GUI prints above the table.
#
# Checked against the controller in net/frr rather than against the docs page,
# on stable/26.1, stable/26.7 and master, which agree.
SEARCH_TARGETS = [
    'bgproute4', 'bgproute6',
    'generalroute4', 'generalroute6',
    'ospfneighbor', 'ospfroute',
    'ospfv3database', 'ospfv3route',
]

# `bgproute`, `generalroute` and `ospfv3neighbor` were offered here and have no
# controller action under any name - neither bare nor `search_`-prefixed - so
# every call made with them answered 404.


def run_module():
    module_args = dict(
        target=dict(
            type='str', required=True,
            choices=[
                'bgpneighbors', 'bgproute4', 'bgproute6', 'bgpsummary',
                'generalroute4', 'generalroute6', 'generalrunningconfig',
                'ospfdatabase', 'ospfinterface', 'ospfneighbor', 'ospfoverview', 'ospfroute',
                'ospfv3database', 'ospfv3interface', 'ospfv3overview',
                'ospfv3route',
            ],
            description='What information to query'
        ),
        **OPN_MOD_ARGS,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    target = module.params['target']

    non_json = ['generalrunningconfig']

    if target in non_json:
        params = []

    else:
        # Straight quotes. This was written with typographic ones (U+201D),
        # which reach the appliance percent-encoded as %E2%80%9D and are
        # ignored - the calls that worked returned JSON because that is what
        # the controller does anyway.
        params = ['$format="json"']

    command = f'search_{target}' if target in SEARCH_TARGETS else target

    info = single_get(
        module=module,
        cnf={
            'module': 'quagga',
            'controller': 'diagnostics',
            'command': command,
            'params': params,
        }
    )

    if 'response' in info:
        info = info['response']

        if isinstance(info, str):
            info = info.strip()

    module.exit_json(data=info)


def main():
    run_module()


if __name__ == '__main__':
    main()
