import base64
import contextlib
import re
import urllib.parse

import flask
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration as SentryLogging
from sentry_sdk.integrations.flask import FlaskIntegration as SentryFlask

try:
    import requests
except ImportError:
    requests = None

try:
    import yaml
except ImportError:
    yaml = None


class SentryEventFilter:
    """Filter used with Sentry SDK to prevent secrets from being uploaded in exception reports.

    Filtering may happen based on:
    - variable name (e.g. password, key, token)
    - module (e.g. cryptography, itsdangerous)
    - config keys (e.g. SECRET_KEY)

    If you subclass or override, and you are using the install_sentry method to set up Sentry
    SDK, you must pass your event filter instance to install_sentry.

    Types, variable names, and module sets can be provided in the constructor to extend filtering
    on the defaults.
    """

    # Filter out any variables having a type in the following tuple
    sanitized_types = (flask.config.Config,)

    # Filter out values anywhere in the event JSON with a key containing any of the following
    # strings or regular expressions.
    sanitized_var_names = [
        'token',
        'password',
        'secret',
        'passwd',
        'authorization',
        'sentry_dsn',
        'xsrf',
        re.compile('.*key$'),
    ]

    # Filter out all local variables from the stacktrace contained within any of the modules listed.
    # This includes all submodules. Values may be strings or compiled regular expressions.
    sanitized_modules = [
        'keg_elements.crypto',
        'bcrypt',
        'cryptography',
        'encryption',
        'itsdangerous',
        'passlib',
        'PyNaCl',
        'secretstorage',
    ]

    # Filter out all instances of the values stored in the config dict under these keys.
    sanitized_config_keys = [
        'SECRET_KEY',
    ]

    def __init__(
            self,
            types=frozenset(),
            var_names=frozenset(),
            modules=frozenset()
    ):
        self.sanitized_types = tuple(set(self.sanitized_types) | set(types))
        self.sanitized_var_names = set(self.sanitized_var_names) | set(var_names)
        self.sanitized_modules = set(self.sanitized_modules) | set(modules)

        self._variable_regexes = {self._var_to_re(key) for key in self.sanitized_var_names}
        self._module_regexes = {self._module_to_re(mod) for mod in self.sanitized_modules}
        self._config_values = self._config_value_representations()

    def _var_to_re(self, key):
        if isinstance(key, str):
            return re.compile(r'.*{}.*'.format(re.escape(key)), re.IGNORECASE)
        return key

    def _module_to_re(self, module):
        if isinstance(module, str):
            return re.compile(r'^{}(?:\.|$).*'.format(re.escape(module)))
        return module

    def _config_value_representations(self):
        if not flask.current_app:
            return []

        reps = []
        for key in self.sanitized_config_keys:
            base_value = flask.current_app.config.get(key)
            if not base_value:
                continue

            if not isinstance(base_value, (str, bytes)):
                base_value = str(base_value)

            if isinstance(base_value, str):
                bytes_value = base_value.encode(errors='ignore')
                str_value = base_value
            else:
                bytes_value = base_value
                str_value = base_value.decode(errors='ignore')

            reps.extend([
                str_value,
                repr(base_value),
                urllib.parse.quote(bytes_value),
                urllib.parse.quote_plus(bytes_value),
                base64.b64encode(bytes_value).decode(),
                base64.b64encode(bytes_value).rstrip(b'=').decode(),
                base64.b16encode(bytes_value).decode(),
            ])

        return reps

    def repr_process(self, obj, hints):
        if isinstance(obj, self.sanitized_types):
            return f'<Filtered {obj.__class__.__name__}>'
        return NotImplemented

    def should_exclude_var(self, k):
        for key in self._variable_regexes:
            if key.match(k):
                return True
        return False

    def _filter_repr(self, v):
        return f'<Filtered {v.__class__.__name__}>'

    def _filter_value(self, key, value):
        if self.should_exclude_var(key):
            return self._filter_repr(value)
        if isinstance(value, str):
            for conf_val in self._config_values:
                value = value.replace(conf_val, self._filter_repr(conf_val))
        return self._filter_recur(value)

    def _filter_recur(self, obj):
        if isinstance(obj, dict):
            return {
                k: self._filter_value(k, v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._filter_recur(v) for v in obj]
        return obj

    def should_exclude_module(self, m):
        for mod in self._module_regexes:
            if mod.match(m):
                return True
        return False

    def _get_exceptions(self, event):
        try:
            exception = event['exception']
        except KeyError:
            return None

        if isinstance(exception, dict) and 'values' in exception:
            return exception['values']

        return [exception]

    def _filter_modules(self, event):
        exceptions = self._get_exceptions(event)
        if exceptions is None:
            # Event does not appear to include any exception stack traces
            return event

        stacks = []
        for exc in exceptions:
            try:
                stacks.append(exc['stacktrace']['frames'])
            except KeyError:
                # If we cannot process the stack trace, clear everything to minimize the chances of
                # leaking sensitive data in case of an unrecognized event schema
                exc['stacktrace'] = {'frames': []}

        for stack in stacks:
            sanitize_subcalls = False
            for frame in stack:
                module = frame.get('module')
                if sanitize_subcalls or module is None or self.should_exclude_module(module):
                    frame['vars'] = {}
                    # Sanitize any stack frames resulting from calls after entering a sanitized
                    # module. Since the sanitized module may process sensitive data using stdlib
                    # functions or functions from other external libraries.
                    sanitize_subcalls = True
        return event

    def _filter_request(self, event):
        try:
            request_dict = event['request']
        except KeyError:
            return event

        request_dict['cookies'] = {
            k: self._filter_repr(v) for k, v in request_dict.get('cookies', {}).items()
        }
        request_dict['headers'] = {
            k: (self._filter_repr(v) if 'cookie' in k.lower() else v)
            for k, v in request_dict.get('headers', {}).items()
        }

        return event

    def before_send(self, event, hints):
        event = self._filter_recur(event)
        event = self._filter_modules(event)
        event = self._filter_request(event)

        return event


def install_sentry(app, integrations, release=None, event_filter=None, **kwargs):
    """Init Sentry SDK with helpful defaults and an event filter."""
    sentry_dsn = app.config.get('SENTRY_DSN')
    if sentry_dsn is None:
        return

    event_filter = event_filter or SentryEventFilter()
    sentry_sdk.serializer.add_global_repr_processor(event_filter.repr_process)

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            SentryLogging(event_level=None),
            SentryFlask(),
            *integrations
        ],
        before_send=event_filter.before_send,
        release=release,
        environment=app.config.get('SENTRY_ENVIRONMENT'),
        with_locals=True,
        send_default_pii=True,  # include user details
        **kwargs
    )


class SentryMonitorError(Exception):
    pass


class SentryMonitorConfigError(Exception):
    pass


class SentryMonitor:
    """Sentry allows monitoring scheduled job execution, and exposes this feature in its
    API. SentryMonitor wraps usage.

    Init the class with the Sentry org name, "base" monitor key, and the environment to
    tie the monitor to in Sentry.

    Note: environment is not yet well-supported. At the time of this writing, there is no
    support for removing a single environment. So, monitors will currently be single-env,
    and each monitor key is given a suffix of the env name.

    Config YAML format::

        jobs:
            my-cron-job:
                checkin_margin: 1 # in minutes
                schedule_type: crontab
                schedule: '30 2 * * *'
                max_runtime: 1 # in minutes
                timezone: Etc/UTC
            other-stats-run:
                checkin_margin: 1
                schedule_type: interval
                schedule: [6, minute]
                max_runtime: 1
                timezone: Etc/UTC


    """
    def __init__(self, org: str, key: str, env: str):
        if requests is None:
            raise Exception('requests library required for Sentry monitoring')

        self.org = org
        self.key = key
        self.env = env
        self.dsn = flask.current_app.config.get('SENTRY_DSN')
        self.checkin_id = None
        self.status = None

    @classmethod
    def read_config(cls, path):
        """Safe-load YAML from the file at ``path``."""
        if yaml is None:
            raise Exception('pyyaml library required for Sentry monitoring')
        with open(path, 'rb') as f:
            return yaml.safe_load(f)

    @classmethod
    def apply_config(cls, org: str, config_data: dict):
        """Runs monitor config on Sentry API for each job in config data."""
        env = flask.current_app.config.get('SENTRY_ENVIRONMENT')
        return_data = {}
        error_data = {}
        for key, monitor_config in config_data.get('jobs', {}).items():
            # monitor gets created via the check-in, which requires status
            config_data = {
                'monitor_config': monitor_config,
                'status': 'ok',
                'environment': env,
            }
            monitor = SentryMonitor(org, key, env)
            try:
                return_data[key] = monitor.make_request(config_data)
                if not return_data[key].get('id'):
                    error_data[key] = return_data[key]
            except SentryMonitorError as exc:
                error_data[key] = str(exc)

        if error_data:
            raise SentryMonitorConfigError(error_data)

        return return_data

    @property
    def monitor_key(self):
        return f'{self.key}-{self.env}'.lower()

    @property
    def url(self):
        mkey = self.monitor_key
        base = f'https://sentry.io/api/0/organizations/{self.org}/monitors/{mkey}/checkins/'
        if self.checkin_id:
            return f'{base}{self.checkin_id}/'
        return base

    def make_request(self, payload):
        method = requests.put if self.checkin_id else requests.post
        resp = method(
            self.url,
            json=payload,
            headers={
                'Authorization': f'DSN {self.dsn}',
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            raise SentryMonitorError(f'{resp.status_code}: {resp.content}')
        return resp.json()

    def ping_status(self, status):
        self.status = status
        data = self.make_request({'status': status, 'environment': self.env})
        if 'id' in data:
            # Store the ID so further status updates in this "session" are tied to the same
            # checkin. Prevents issues with overlap of job runs.
            self.checkin_id = data['id']
        return data

    def ping_ok(self):
        return self.ping_status('ok')

    def ping_error(self):
        return self.ping_status('error')

    def ping_in_progress(self):
        return self.ping_status('in_progress')


@contextlib.contextmanager
def sentry_monitor_job(org: str, key: str, env: str = None, do_ping: bool = False):
    """Context manager for running in_progress, then ok status pings on a Sentry monitor.

    Sentry will not be pinged unless the ``do_ping`` kwarg is True (default is False).

    ``env`` will default to ``SENTRY_ENVIRONMENT`` config value if not specified.

    Context manager returns the ``SentryMonitor`` instance. The wrapped code may ping a
    different ending status (such as if an error result should occur without an
    exception). Exceptions will result in an error status."""
    env = env or flask.current_app.config.get('SENTRY_ENVIRONMENT')
    if not do_ping:
        yield
    else:
        monitor = SentryMonitor(org, key, env)
        monitor.ping_in_progress()
        try:
            yield monitor
            if monitor.status == 'in_progress':
                # Code wrapped in context may have manually pinged another status
                monitor.ping_ok()
        except Exception:
            monitor.ping_error()
            raise
