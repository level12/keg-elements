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
        obj = ents.ColumnTester.testing_create(encrypted1=None, encrypted2=None, encrypted3=None)
        assert obj.encrypted1 is None
        assert obj.encrypted2 is None
        assert obj.encrypted3 is None
        results = db.session.execute('select * from column_tester').fetchall()
        assert results[0].encrypted1 is None
        assert results[0].encrypted2 is None
        assert results[0].encrypted3 is None

    def test_store_encrypted(self):
        ents.ColumnTester.delete_cascaded()
        obj = ents.ColumnTester.testing_create(encrypted1='Foo', encrypted2='Bar', encrypted3='Baz')
        assert obj.encrypted1 == 'Foo'
        assert obj.encrypted2 == 'Bar'
        assert obj.encrypted3 == 'Baz'
        results = db.session.execute('select * from column_tester').fetchall()
        assert 'Foo' not in results[0].encrypted1
        assert 'Bar' not in results[0].encrypted2
        assert results[0].encrypted3 == 'Onm'

    def test_load_encrypted(self):
        ents.ColumnTester.delete_cascaded()
        db.session.execute('''
        insert into column_tester (encrypted1, encrypted2, encrypted3) values
            ('gAAAAABYVFHtgRTQJyzkIF5bQ0TiLA3Dm0kfDF5pvSLrZUBrpZiq_f3g3-jUUj8vPmTw2Uf3SW3u73fJNO9ER46xpW9_41IdaQ==',
            'gAAAAABYVFHtbibu6P-oroQ7UYj7g5oiZPqsbeAmxNAIz3wiEjc236bP7c2Ubsf1-S-ANt2r2WNQytxIfwxoE9VyNQmtihCCwA==',
            'Onm'
            )
        ''')
        obj = ents.ColumnTester.query.one()
        assert obj.encrypted1 == 'Foo'
        assert obj.encrypted2 == 'Bar'
        assert obj.encrypted3 == 'Baz'
