import flask

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
