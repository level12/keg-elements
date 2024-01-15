from unittest import mock

import flask
import pytest

from keg_elements import sentry


class TestSentryFilter:
    def test_repr_process(self):
        f = sentry.SentryEventFilter()

        conf = flask.config.Config(__file__)
        assert f.repr_process(conf, {}) == '<Filtered Config>'
        assert f.repr_process(dict(), {}) is NotImplemented
        assert f.repr_process(1, {}) is NotImplemented
        assert f.repr_process('', {}) is NotImplemented

    def test_filter_by_key(self):
        event = {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {
                                'secret_key': '1234',
                                'safe': 'abc'
                            }
                        },
                        {
                            'module': 'foo.baz',
                            'vars': {
                                'password': '4321',
                                'unchanged': 'def'
                            }
                        },

                    ]
                },
                'token': 1
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {
                                'secret_key': '<Filtered str>',
                                'safe': 'abc'
                            }
                        },
                        {
                            'module': 'foo.baz',
                            'vars': {
                                'password': '<Filtered str>',
                                'unchanged': 'def'
                            }
                        },

                    ]
                },
                'token': '<Filtered int>'
            }
        }

    def test_filter_by_module(self):
        event = {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.app',
                            'vars': {
                                'unchanged': 'xyz',
                            }
                        },
                        {
                            'module': 'cryptography',
                            'vars': {
                                'secret_key': '1234',
                                'safe': 'abc'
                            }
                        },
                        {
                            'module': 'passlib.submodule',
                            'vars': {
                                'password': '4321',
                                'unchanged': 'def'
                            }
                        },
                        {
                            'module': 'foo.libs',
                            'vars': {
                                'password': '4321',
                                'unchanged': 'def'
                            }
                        },
                    ]
                },
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.app',
                            'vars': {
                                'unchanged': 'xyz'
                            }
                        },
                        {
                            'module': 'cryptography',
                            'vars': {}
                        },
                        {
                            'module': 'passlib.submodule',
                            'vars': {}
                        },
                        {
                            'module': 'foo.libs',
                            'vars': {}
                        },

                    ]
                },
            }
        }

    def test_filter_modules_no_stacktrace(self):
        event = {
            'exception': {
                'values': [
                    {
                        'foo': 'bar'
                    }
                ]
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'exception': {
                'values': [
                    {
                        'foo': 'bar',
                        'stacktrace': {
                            'frames': []
                        }
                    }
                ]
            }
        }

    def test_filter_by_module_multiple_exceptions(self):
        event = {
            'exception': {
                'values': [
                    {
                        'stacktrace': {
                            'frames': [
                                {
                                    'module': 'foo.app',
                                    'vars': {
                                        'unchanged': 'xyz',
                                    }
                                },
                                {
                                    'module': 'cryptography',
                                    'vars': {
                                        'safe': 'abc'
                                    }
                                },
                            ]
                        },
                    },
                    {
                        'stacktrace': {
                            'frames': [
                                {
                                    'module': 'foo.bar',
                                    'vars': {
                                        'unchanged': 'abc',
                                    }
                                },
                                {
                                    'module': 'keg_elements.crypto.encrypt',
                                    'vars': {
                                        'safe': 'abc'
                                    }
                                },
                            ]
                        },
                    },

                ]
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'exception': {
                'values': [
                    {
                        'stacktrace': {
                            'frames': [
                                {
                                    'module': 'foo.app',
                                    'vars': {
                                        'unchanged': 'xyz'
                                    }
                                },
                                {
                                    'module': 'cryptography',
                                    'vars': {}
                                },
                            ]
                        }
                    },
                    {
                        'stacktrace': {
                            'frames': [
                                {
                                    'module': 'foo.bar',
                                    'vars': {
                                        'unchanged': 'abc',
                                    }
                                },
                                {
                                    'module': 'keg_elements.crypto.encrypt',
                                    'vars': {}
                                },
                            ]
                        },
                    },
                ]

            }
        }

    def test_filter_request(self):
        event = {
            'request': {
                'cookies': {
                    '_xsrf': 'foo',
                    'session': 'ol9auwkerjevt1bzvopg9vri311o5snc.naif3fmfext6l2shp6kr78zkwn'
                },
                'env': {
                    'REMOTE_ADDR': '127.0.0.1',
                    'SERVER_NAME': '127.0.0.1',
                    'SERVER_PORT': '5000'
                },
                'headers': {
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Cookie': 'session=ol9auwkerjevt1bzvopg9vri311o5snc.naif3fmfext6l2shp6kr78zkwn',
                    'Dnt': '1',
                    'Host': 'localhost:5000',
                    'Upgrade-Insecure-Requests': '1',
                },
                'method': 'GET',
                'query_string': '',
                'url': 'http://localhost:5000/error'
            }
        }
        filtered = sentry.SentryEventFilter().before_send(event, {})
        assert filtered == {
            'request': {
                'cookies': {
                    '_xsrf': '<Filtered str>',
                    'session': '<Filtered str>'
                },
                'env': {
                    'REMOTE_ADDR': '127.0.0.1',
                    'SERVER_NAME': '127.0.0.1',
                    'SERVER_PORT': '5000'
                },
                'headers': {
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Cookie': '<Filtered str>',
                    'Dnt': '1',
                    'Host': 'localhost:5000',
                    'Upgrade-Insecure-Requests': '1',
                },
                'method': 'GET',
                'query_string': '',
                'url': 'http://localhost:5000/error'
            }
        }

    def test_filter_by_config_value(self, monkeypatch):
        monkeypatch.setitem(flask.current_app.config, 'STRING', '1234567890')
        monkeypatch.setitem(flask.current_app.config, 'BYTES1', b'\xF0\x0B\xAA')
        monkeypatch.setitem(flask.current_app.config, 'BYTES2', b'hello world')
        monkeypatch.setitem(flask.current_app.config, 'IGNORED', 'ignored')
        monkeypatch.setitem(flask.current_app.config, 'EMPTY', '')
        monkeypatch.setitem(flask.current_app.config, 'NONE', None)

        class Filter(sentry.SentryEventFilter):
            sanitized_config_keys = [
                'STRING',
                'BYTES1',
                'BYTES2',
                'EMPTY',
                'NONE',
                'UNSET',
            ]

        event = {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {
                                'string1': '**1234567890**',
                                'string2': '__31323334353637383930__',
                                'string3': '**MTIzNDU2Nzg5MA==**',
                                'string4': '**MTIzNDU2Nzg5MA**',
                                'bytes1_1': '**F00BAA**',
                                'bytes1_2': '**8Auq**',
                                'bytes1_3': '**%F0%0B%AA**',
                                'bytes2_1': '**hello world**',
                                'bytes2_2': '**hello+world**',
                                'bytes2_3': '**aGVsbG8gd29ybGQ=**',
                                'multiple': '**1234567890**hello world**',
                                'ignored': '**ignored**',
                                'url': 'http://localhost?var1=hello+world&var2=%F0%0B%AA',
                                'empty': '',
                                'none': None,
                            }
                        },
                    ]
                },
            }
        }
        filtered = Filter().before_send(event, {})
        assert filtered == {
            'exception': {
                'stacktrace': {
                    'frames': [
                        {
                            'module': 'foo.bar',
                            'vars': {
                                'string1': '**<Filtered str>**',
                                'string2': '__<Filtered str>__',
                                'string3': '**<Filtered str>**',
                                'string4': '**<Filtered str>**',
                                'bytes1_1': '**<Filtered str>**',
                                'bytes1_2': '**<Filtered str>**',
                                'bytes1_3': '**<Filtered str>**',
                                'bytes2_1': '**<Filtered str>**',
                                'bytes2_2': '**<Filtered str>**',
                                'bytes2_3': '**<Filtered str>**',
                                'multiple': '**<Filtered str>**<Filtered str>**',
                                'ignored': '**ignored**',
                                'url': 'http://localhost?var1=<Filtered str>&var2=<Filtered str>',
                                'empty': '',
                                'none': None,
                            }
                        },
                    ]
                },
            }
        }


class TestSentryMonitorUtils:
    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_job_normal(self, m_sentry_checkin):
        m_sentry_checkin.return_value = 'foo123'

        with sentry.sentry_monitor_job('monitor-key', do_ping=True) as monitor:
            pass

        assert m_sentry_checkin.call_count == 2
        first_call = m_sentry_checkin.call_args_list[0].kwargs
        assert first_call == dict(monitor_slug='monitor-key-testenv', status='in_progress')
        second_call = m_sentry_checkin.call_args_list[1].kwargs
        assert second_call['monitor_slug'] == 'monitor-key-testenv'
        assert second_call['status'] == 'ok'
        assert second_call['check_in_id'] == 'foo123'
        assert second_call['duration']
        assert monitor.checkin_id == 'foo123'

    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_job_sentry_exception(self, m_sentry_checkin):
        m_sentry_checkin.side_effect = Exception('something wrong'), 'foo123'
        with pytest.raises(Exception, match='something wrong'):
            with sentry.sentry_monitor_job('monitor-key', do_ping=True):
                pass

        assert m_sentry_checkin.call_count == 2
        first_call = m_sentry_checkin.call_args_list[0].kwargs
        assert first_call == dict(monitor_slug='monitor-key-testenv', status='in_progress')
        second_call = m_sentry_checkin.call_args_list[1].kwargs
        assert second_call['monitor_slug'] == 'monitor-key-testenv'
        assert second_call['status'] == 'error'

    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_job_override_final_ping(self, m_sentry_checkin):
        m_sentry_checkin.return_value = 'foo123'

        with sentry.sentry_monitor_job('monitor-key', do_ping=True) as monitor:
            monitor.ping_error()

        assert m_sentry_checkin.call_count == 2
        first_call = m_sentry_checkin.call_args_list[0].kwargs
        assert first_call == dict(monitor_slug='monitor-key-testenv', status='in_progress')
        second_call = m_sentry_checkin.call_args_list[1].kwargs
        assert second_call['monitor_slug'] == 'monitor-key-testenv'
        assert second_call['status'] == 'error'
        assert second_call['check_in_id'] == 'foo123'
        assert second_call['duration']

    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_job_no_ping(self, m_sentry_checkin):
        with sentry.sentry_monitor_job('monitor-key', do_ping=False):
            pass

        assert m_sentry_checkin.call_count == 0

    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_job_exception(self, m_sentry_checkin):
        m_sentry_checkin.return_value = 'foo123'

        with pytest.raises(Exception):
            with sentry.sentry_monitor_job('monitor-key', do_ping=True):
                raise ValueError('foo')

        assert m_sentry_checkin.call_count == 2
        first_call = m_sentry_checkin.call_args_list[0].kwargs
        assert first_call == dict(monitor_slug='monitor-key-testenv', status='in_progress')
        second_call = m_sentry_checkin.call_args_list[1].kwargs
        assert second_call['monitor_slug'] == 'monitor-key-testenv'
        assert second_call['status'] == 'error'
        assert second_call['check_in_id'] == 'foo123'
        assert second_call['duration']

    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_config_applied(self, m_sentry_checkin):
        config_data = {
            'jobs': {
                'monitor-key': {
                    'key': 'value',
                }
            }
        }
        sentry.SentryMonitor.apply_config(config_data)
        m_sentry_checkin.assert_called_once_with(
            monitor_slug='monitor-key-testenv',
            status='ok',
            monitor_config={'key': 'value'},
        )

    @mock.patch.dict('flask.current_app.config', {
        'SENTRY_ENVIRONMENT': 'testenv'
    })
    @mock.patch(
        'keg_elements.sentry.sentry_sdk.crons.api.capture_checkin', autospec=True, spec_set=True
    )
    def test_config_error(self, m_sentry_checkin):
        m_sentry_checkin.return_value = None

        config_data = {
            'jobs': {
                'monitor-key': {
                    'key': 'value',
                }
            }
        }
        with pytest.raises(sentry.SentryMonitorConfigError):
            sentry.SentryMonitor.apply_config(config_data)
