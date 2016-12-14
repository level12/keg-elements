from keg.db import db

import kegel_app.model.entities as ents
import pytz


class TestColumns(object):

    def test_testing_create_for_timezone_columns(self):
        obj = ents.ColumnTester.testing_create()
        assert obj.time_zone in pytz.common_timezones

        obj.time_zone = 'other'
        assert obj.time_zone == 'other'
        assert obj.__mapper__.columns.time_zone.type.length == 255

    def test_encrypted_null(self):
        ents.ColumnTester.delete_cascaded()
        obj = ents.ColumnTester.testing_create(encrypted1=None, encrypted2=None)
        assert obj.encrypted1 is None
        assert obj.encrypted2 is None
        results = db.session.execute('select * from column_tester').fetchall()
        assert results[0].encrypted1 is None
        assert results[0].encrypted2 is None

    def test_store_encrypted(self):
        ents.ColumnTester.delete_cascaded()
        obj = ents.ColumnTester.testing_create(encrypted1='Foo', encrypted2='Bar')
        assert obj.encrypted1 == 'Foo'
        assert obj.encrypted2 == 'Bar'
        results = db.session.execute('select * from column_tester').fetchall()
        assert 'Foo' not in results[0].encrypted1
        assert len(results[0].encrypted1) == 64
        assert 'Bar' not in results[0].encrypted2
        assert len(results[0].encrypted2) == 64

    def test_load_encrypted(self):
        ents.ColumnTester.delete_cascaded()
        db.session.execute('''
        insert into column_tester (encrypted1, encrypted2) values
            ('8858927315c990890a2f621f6da8bd132e19d8e21e51493c8ec4d36299036c24',
            'ab5bfc5d35f04500aac1cccbca3ac7176324bc6149c0a2b9eeba0fe1b8609283')
        ''')
        obj = ents.ColumnTester.query.one()
        assert obj.encrypted1 == 'foo'
        assert obj.encrypted2 == 'bar'
