from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import is_unset


def pem(value: str) -> str:
    # OPNsense stores the payload as posted - compare and post one spelling
    if is_unset(value):
        return ''

    return '\n'.join(line.strip() for line in str(value).strip().splitlines())


class _Trust(BaseModule):
    # System - Trust (OPNsense >= 24.7): imports only, never generates.
    # OPNsense links a certificate to its issuing CA itself (Cert::linkCaRefs,
    # by issuer DN) on every add and set, so there is no CA parameter to post.
    FIELD_ID = 'description'
    CMDS = {
        'add': 'add',
        'del': 'del',
        'set': 'set',
        'search': 'search',
        'detail': 'get',
    }
    API_MOD = 'trust'
    FIELDS_CHANGE = ['crt', 'prv']
    FIELDS_ALL = ['description', 'action', 'crt', 'prv']
    FIELDS_TRANSLATE = {
        'description': 'descr',
        'crt': 'crt_payload',
        'prv': 'prv_payload',
    }
    FIELDS_TYPING = {}
    FIELDS_DIFF_NO_LOG = ['prv']
    FIELDS_DIFF_EXCLUDE = ['action']
    TIMEOUT = 30.0  # 'system trust configure' runs on add/set
    # 'action' is a volatile field defaulting to 'internal': a set without it
    # would generate a new certificate instead of importing ours
    IMPORT_ACTION = None

    def __init__(
            self, module: AnsibleModule, result: dict, multi: dict = None,
            session: Session = None, fail: dict = None,
    ):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail, multi=multi)
        setattr(self, self.EXIST_ATTR, {})

    def check(self) -> None:
        if self.p['state'] == 'present':
            if is_unset(self.p['crt']):
                self.m.fail_json(f"You need to supply 'crt' to import {self.API_CONT} '{self.p['description']}'!")

            self.p['crt'] = pem(self.p['crt'])
            self.p['action'] = self.IMPORT_ACTION

            if is_unset(self.p['prv']):
                # not declared: neither compared nor posted, the appliance keeps its key
                self.FIELDS_CHANGE = [f for f in self.FIELDS_CHANGE if f != 'prv']
                self.FIELDS_ALL = [f for f in self.FIELDS_ALL if f != 'prv']

            else:
                self.p['prv'] = pem(self.p['prv'])

        self._base_check()

    def simplify_existing(self, existing: dict) -> dict:
        # also applied to already simplified entries (multi cache)
        return {
            'uuid': existing.get('uuid'),
            'refid': existing.get('refid', ''),
            'description': existing.get('descr', existing.get('description', '')),
            'crt': pem(existing.get('crt_payload', existing.get('crt', ''))),
            'prv': pem(existing.get('prv_payload', existing.get('prv', ''))),
        }


class TrustCa(_Trust):
    API_CONT = 'ca'
    API_KEY_PATH = 'ca'
    EXIST_ATTR = 'ca'
    IMPORT_ACTION = 'existing'


class TrustCert(_Trust):
    API_CONT = 'cert'
    API_KEY_PATH = 'cert'
    EXIST_ATTR = 'cert'
    IMPORT_ACTION = 'import'
