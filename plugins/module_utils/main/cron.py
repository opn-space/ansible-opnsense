from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.main import \
    is_unset
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class CronJob(BaseModule):
    FIELD_ID = 'description'
    CMDS = {
        'add': 'add_job',
        'del': 'del_job',
        'set': 'set_job',
        'search': 'get',
        'toggle': 'toggle_job', # test
    }
    API_KEY_PATH = 'job.jobs.job'
    API_MOD = 'cron'
    API_CONT = 'settings'
    API_CONT_REL = 'service'
    FIELDS_CHANGE = [
        'minutes', 'hours', 'days', 'months',
        'weekdays', 'command', 'who', 'parameters'
    ]
    FIELDS_TYPING = {
        'bool': ['enabled'],
        'select': ['command'],
        'int': ['minutes', 'hours', 'days', 'months', 'weekdays'],
    }
    FIELDS_ALL = ['description', 'enabled']
    FIELDS_ALL.extend(FIELDS_CHANGE)
    EXIST_ATTR = 'cron'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.cron = {}
        self.available_commands = []

    def check(self) -> None:
        if self.p['state'] == 'present' and is_unset(self.p['command']):
            self.m.fail_json("You need to provide a 'command' if you want to create a cron-job!")

        self.find(match_fields=[self.FIELD_ID])

        if self.p['state'] == 'present':
            if self.p['command'] is not None and len(self.available_commands) > 0 and \
                    self.p['command'] not in self.available_commands:
                self.m.fail_json(
                    'Got unsupported command! '
                    f"Available ones are: {', '.join(self.available_commands)}"
                )

        self._base_check()

    def _build_all_available_cmds(self, raw_cmds: dict):
        if len(self.available_commands) == 0:
            for cmd in raw_cmds.keys():
                if cmd not in self.available_commands:
                    self.available_commands.append(cmd)

    def simplify_existing(self, existing: dict) -> dict:
        # 'origin' is KEPT. It used to be popped here, which is what made it
        # invisible to callers - it is neither missing from the API nor gated by
        # FIELDS_ALL, it was simply deleted from every entry on the way out.
        #
        # OPNsense's plugins register cron jobs of their own and refuse to delete
        # them: del_job answers HTTP 500 "Cannot delete this automatically
        # registered cron job." origin is what tells them apart - 'cron' for
        # anything created through the API or the GUI, the registering plugin's
        # name otherwise - so without it a declarative caller cannot tell a job it
        # may delete from one the appliance owns, and fails the run the first time
        # both are present.
        #
        # It stays out of FIELDS_ALL, which drives the outgoing request and the
        # diff rather than the read, so nothing writes it and nothing compares it.
        # The model's default is already correct for anything this module creates.
        simple = self._base_simplify_existing(existing)
        self._build_all_available_cmds(existing['command'])
        return simple
