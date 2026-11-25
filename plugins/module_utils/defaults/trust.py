from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
    STATE_ONLY_MOD_ARG


TRUST_MOD_ARGS = dict(
    description=dict(
        type='str', required=True, aliases=['desc', 'descr'],
        description='Unique description the object is matched on',
    ),
    crt=dict(
        type='str', required=False, aliases=['certificate'],
        description='The certificate in PEM format. Required for state=present',
    ),
    prv=dict(
        type='str', required=False, aliases=['private_key'], no_log=True,
        description='The private key in PEM format. Left unset, the key the appliance holds is kept',
    ),
    **STATE_ONLY_MOD_ARG,
)
