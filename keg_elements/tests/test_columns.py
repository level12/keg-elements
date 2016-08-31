import kegel_app.model.entities as ents
import pytz


class TestColumns(object):

    def test_testing_create_for_timezone_columns(self):
        obj = ents.ColumnTester.testing_create()
        assert obj.time_zone in pytz.common_timezones

        obj.time_zone = 'other'
        assert obj.time_zone == 'other'
        assert obj.__mapper__.columns.time_zone.type.length == 255
