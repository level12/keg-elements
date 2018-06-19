import flask
import raven
from raven.utils.serializer.base import Serializer
from raven.utils.serializer.manager import transform, SerializationManager


class ConfigTypeFilterSerializer(Serializer):
    """
    Sentry serializer for the Config type that will hide the contents
    """
    TYPES = (
        flask.config.Config,
    )

    def can(self, value):
        return isinstance(value, self.TYPES)

    def serialize(self, value, **kwargs):
        return '{ ... }'


class FilteringManager(SerializationManager):
    """
    This is used by sentry to find the available serializers to use when building a report.
    Typically we could register a serializer without subclassing this but because the built-in
    serializers take precedent to custom ones we could register and the Config type is a subclass
    of dict, we must insert our serializer before the built ins to force sentry to prefer it over
    the dict serializer.
    """

    def __init__(self, extra_serializers=tuple()):
        self.extra_serializers = extra_serializers
        super(FilteringManager, self).__init__()

    @property
    def serializers(self):
        for es in self.extra_serializers:
            yield es
        for s in SerializationManager.serializers.fget(self):
            yield s


class SentryClient(raven.base.Client):
    """
    A custom sentry client type that includes sanitization for the config type and features to ease
    testing of the reports that would be sent to the sentry API
    """

    # The following attributes are used for testing to capture reports that would be sent.
    # When __log_reports__ is True, any data that would be sent to sentry is stored in the
    # __report_log__ list.  See testing.SentryCapture for a helpful context manager that makes
    # use of these attributes
    __log_reports__ = False
    __report_log__ = []

    def __init__(self, *args, **kwargs):
        self.extra_serializers = kwargs.pop('extra_serializers', [ConfigTypeFilterSerializer])
        super(SentryClient, self).__init__(*args, **kwargs)

    def transform(self, data):
        # Called by sentry to convert data into a JSON friendly format that can be sent to their API
        return transform(
            data,
            list_max_length=self.list_max_length,
            string_max_length=self.string_max_length,
            manager=FilteringManager(self.extra_serializers)
        )

    def send(self, auth_header=None, **data):
        from keg import current_app

        if self.__log_reports__:
            # Report logging is enabled. Store the report in __report_log__
            self.__report_log__.append(data)
            return

        if flask.has_app_context() and current_app.config.get('TESTING'):
            # We are in a test. Don't pass on the report to Sentry.
            return

        # If we are not testing or we cannot determine that because we are not within an
        # app context, pass the report through
        return super(SentryClient, self).send(auth_header=auth_header, **data)  # pragma: no cover
