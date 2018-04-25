from flask import current_app

from keg_elements import sentry, testing


class TestFilterConfig:
    @classmethod
    def setup_class(cls):
        cls.sentry = sentry.SentryClient(dsn='https://test:test@sentry.io/test')

    def check_config_filtered_in_stack(self, stack, *keys):
        frames = stack['frames']
        instance_count = 0
        for frame in frames:
            scope = frame['vars']
            for key in keys:
                if key in scope:
                    instance_count += 1
                    assert scope[key] == '{ ... }'
        return instance_count

    def test_filtered_from_stack(self):
        def do_raise():
            config = current_app.config  # noqa
            try:
                foo = current_app.config  # noqa
                raise ValueError('Some error')
            except ValueError:
                self.sentry.captureException()

        with testing.SentryCapture() as cap:
            do_raise()
        assert len(cap.reports) == 1
        stack = cap.reports[0]['exception']['values'][0]['stacktrace']
        assert self.check_config_filtered_in_stack(stack, 'config', 'foo') == 2

    def test_filtering_serializer(self):
        serializer = sentry.ConfigTypeFilterSerializer(None)

        assert serializer.can(current_app.config)
        assert not serializer.can({})

        assert serializer.serialize(current_app.config) == '{ ... }'
