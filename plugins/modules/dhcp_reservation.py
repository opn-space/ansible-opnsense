#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2025, Pascal Rath <contact+opnsense@OXL.at>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/core/kea.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.dhcp_reservation_v4 import ReservationV4

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/dhcp.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/dhcp.html'


def run_module():
    module_args = dict(
        ip=dict(
            type='str', required=True, aliases=['ip_address'],
            description='IP address to offer to the client',
        ),
        mac=dict(
            type='str', required=False, aliases=['mac_address'],
            description='MAC/Ether address of the client in question',
        ),
        subnet=dict(
            type='str', required=False,
            description='Subnet this reservation belongs to',
        ),
        hostname=dict(
            type='str', required=False,
            description='Offer a hostname to the client',
        ),
        description=dict(type='str', required=False, aliases=['desc']),
        # Per-host DHCP options. Same argument names, aliases and defaults as
        # dhcp_subnet uses for the same options, so an inventory reads alike
        # whether an option is offered to a whole subnet or to one host - and
        # an option set here overrides the subnet's.
        #
        # There is deliberately no 'auto_options' and no 'v6_only_preferred':
        # OPNsense's Kea model gives a reservation neither, so offering them
        # would be offering a value the appliance discards.
        gateway=dict(
            type='list', elements='str', required=False, aliases=['gw', 'routers'], default=[],
            description='Default gateways to offer to this client',
        ),
        routes=dict(
            type='str', required=False, aliases=['static_routes'], default='',
            description='Static routes that the client should install in its routing cache, '
                        'defined as dest-ip1,router-ip1;dest-ip2,router-ip2',
        ),
        dns=dict(
            type='list', elements='str', required=False, aliases=['dns_servers', 'dns_srv'], default=[],
            description='DNS servers to offer to this client',
        ),
        domain=dict(
            type='str', required=False, aliases=['domain_name', 'dom_name', 'dom'], default='',
            description='The domain name to offer to this client, overriding the one its subnet offers',
        ),
        domain_search=dict(
            type='list', elements='str', required=False, aliases=['dom_search'], default=[],
            description="Specifies a 'search list' of Domain Names to be used by the client to locate "
                        'not-fully-qualified domain names.',
        ),
        ntp_servers=dict(
            type='list', elements='str', required=False, aliases=['ntp_srv', 'ntp'], default=[],
            description='Specifies a list of IP addresses indicating NTP (RFC 5905) servers available to the client.',
        ),
        time_servers=dict(
            type='list', elements='str', required=False, aliases=['time_srv'], default=[],
            description='Specifies a list of RFC 868 time servers available to the client.',
        ),
        tftp_server=dict(
            type='str', required=False, aliases=['tftp', 'tftp_srv', 'tftp_server_name'], default='',
            description='TFTP server address or fqdn',
        ),
        tftp_file=dict(
            type='str', required=False, aliases=['tftp_boot_file', 'boot_file_name'], default='',
            description='TFTP Boot filename to request',
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

    module_wrapper(ReservationV4(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
