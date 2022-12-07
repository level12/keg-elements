import datetime
from decimal import Decimal

from keg.db import db
import arrow
import freezegun
import pytest
import sqlalchemy as sa
import sqlalchemy_utils as sautils
import keg_elements.db.mixins as mixins
import keg_elements.db.columns as columns

import kegel_app.model.entities as ents


class TestDefaultColsMixin:

    def setup_method(self, fn):
        ents.Thing.delete_cascaded()

    @pytest.mark.skipif(db.engine.dialect.name != 'sqlite', reason='SQLite only test')
    def test_default_ordering(self):
        thing1 = ents.Thing.fake(id=6)
        thing2 = ents.Thing.fake(id=5)
        thing3 = ents.Thing.fake(id=7)

        assert ents.Thing.query.all() == [thing2, thing1, thing3]

    def test_utc_default(self):
        with freezegun.freeze_time('2020-01-01 13:01:01', tz_offset=4):
            thing = ents.Thing.fake()
        assert thing.created_utc.format() == '2020-01-01 17:01:01+00:00'
        assert thing.updated_utc.format() == '2020-01-01 17:01:01+00:00'

        with freezegun.freeze_time('2020-02-01 14:03:05', tz_offset=3):
            db.session.query(ents.Thing).filter_by(id=thing.id).update({})
            db.session.commit()
        assert thing.updated_utc.format() == '2020-02-01 17:03:05+00:00'


class TestMethodsMixin:

    def setup_method(self, fn):
        ents.Thing.delete_cascaded()
        ents.MultiplePrimaryKeys.delete_cascaded()

    def test_add(self):
        ents.Thing.add(name='name', color='color', scale_check=1)
        assert ents.Thing.query.count() == 1

        row = ents.Thing.query.first()

        assert row.name == 'name'
        assert row.color == 'color'
        assert row.scale_check == 1

    def test_insert(self):
        ret_id = ents.Thing.insert(name='name', color='color', scale_check=1)
        assert ents.Thing.query.count() == 1

        row = ents.Thing.query.first()

        if db.engine.dialect.name != 'sqlite':
            assert row.id == ret_id
        assert row.name == 'name'
        assert row.color == 'color'
        assert row.scale_check == 1

    def test_insert_values_dict(self):
        ents.Thing.insert(values={'name': 'name'}, color='color', scale_check=1)
        row = ents.Thing.query.first()

        assert row.name == 'name'
        assert row.color == 'color'
        assert row.scale_check == 1

    def test_insert_multiple_pk(self):
        ret_id = ents.MultiplePrimaryKeys.insert(name='name', id=54, other_pk=5)
        assert ents.MultiplePrimaryKeys.query.count() == 1

        row = ents.MultiplePrimaryKeys.query.first()

        if db.engine.dialect.name != 'sqlite':
            assert (54, 5) == ret_id
        assert row.name == 'name'

    def test_delete(self):
        thing = ents.Thing.fake()
        assert ents.Thing.query.count() == 1

        ents.Thing.delete(thing.id)
        assert ents.Thing.query.count() == 0

        assert ents.Thing.query.get(1) is None
        assert ents.Thing.delete(1) is False

    def test_delete_cascaded(self):
        ents.Thing.fake()
        assert ents.Thing.query.count() == 1

        ents.Thing.delete_cascaded()
        assert ents.Thing.query.count() == 0

    def test_edit(self):
        thing1 = ents.Thing.fake()

        ents.Thing.edit(_oid=thing1.id, name='edited')
        assert thing1.name == 'edited'

        with pytest.raises(AttributeError):
            ents.Thing.edit(name='edited')

    def test_update(self):
        thing1 = ents.Thing.fake()

        ents.Thing.update(thing1.id, name='edited', color='silver')
        db.session.commit()
        db.session.refresh(thing1)

        assert thing1.name == 'edited'
        assert thing1.color == 'silver'

    def test_update_values_dict(self):
        thing1 = ents.Thing.fake()

        ents.Thing.update(thing1.id, values={'name': 'edited'}, color='silver')
        db.session.commit()
        db.session.refresh(thing1)

        assert thing1.name == 'edited'
        assert thing1.color == 'silver'

    def test_update_multiple_pk(self):
        row = ents.MultiplePrimaryKeys.fake(id=55, other_pk=6, name='foo')
        ents.MultiplePrimaryKeys.update((55, 6), name='bar')
        db.session.commit()
        db.session.refresh(row)

        assert row.name == 'bar'

    def test_from_dict(self):
        # Testing create uses `from_dict` so create objects by hand
        related = ents.RelatedThing(name='something')
        db.session.add(related)

        related.from_dict({
            'key_not_present': 'blah'
        })
        assert related.name == 'something'

        related.from_dict({'name': 'blah'})
        assert related.name == 'blah'

        related.from_dict({'thing': {'name': 'thing_name'}})
        assert related.thing.name == 'thing_name'

        related.thing.from_dict({'manys': [{'name': 'many_1'}, {'name': 'many_2'}]})
        assert ents.ManyToManyThing.query.count() == 2
        assert len(related.thing.manys) == 2

    def test_add_edit(self):
        obj = ents.MultiplePrimaryKeys.add_or_edit({
            'name': 'something', 'id': 1, 'other_pk': 1})

        assert obj.name == 'something'
        assert obj.id == 1
        assert obj.other_pk == 1

        with pytest.raises(sa.exc.InvalidRequestError, match='Incorrect number of values'):
            ents.MultiplePrimaryKeys.add_or_edit({'name': 'other', 'id': 1})

        with pytest.raises(sa.exc.InvalidRequestError, match='Incorrect number of values'):
            ents.MultiplePrimaryKeys.add_or_edit({'name': 'other', 'other_pk': 1})

        ents.MultiplePrimaryKeys.add_or_edit({'name': 'other', 'id': 1, 'other_pk': 1})
        assert obj.name == 'other'

    def test_get_by(self):

        def returns_none_when_count_is_zero():
            assert ents.Thing.get_by(id=1) is None

        def returns_object_when_one_exists():
            thing = ents.Thing.fake()

            assert ents.Thing.get_by(id=thing.id) == thing

        def raises_when_multiple_exists():
            ents.Thing.fake(name='foo')
            ents.Thing.fake(name='foo')

            with pytest.raises(sa.orm.exc.MultipleResultsFound):
                ents.Thing.get_by(name='foo')

        returns_none_when_count_is_zero()
        returns_object_when_one_exists()
        raises_when_multiple_exists()

    def test_get_where(self):
        thing1 = ents.Thing.fake(name='thing1', color='black')
        ents.Thing.fake(name='thing2', color='black', scale_check=10)
        thing3 = ents.Thing.fake(name='thing3', color='orange', scale_check=10)

        assert ents.Thing.get_where(ents.Thing.name == 'thing1') == thing1
        assert ents.Thing.get_where(ents.Thing.name == 'thing5') is None
        assert (ents.Thing.get_where(ents.Thing.color == 'orange',
                                     ents.Thing.scale_check == 10) == thing3)

        with pytest.raises(sa.orm.exc.MultipleResultsFound):
            ents.Thing.get_where(ents.Thing.color == 'black')

    def test_pairs_takes_name_and_value_and_returns_list_of_tuples(self):
        thing1 = ents.Thing.fake(name='A', color='orange')
        thing2 = ents.Thing.fake(name='B', color='black')

        expected = [(thing1.id, 'A'), (thing2.id, 'B')]
        assert ents.Thing.pairs('id', 'name') == expected

        expected = [(thing2.id, 'B'), (thing1.id, 'A')]
        assert ents.Thing.pairs('id', 'name',
                                order_by=[ents.Thing.name.desc()]) == expected

        expected = [(thing2.id, 'B')]
        query = ents.Thing.query.filter_by(name='B')
        result = ents.Thing.pairs('id', 'name', query=query)
        assert result == expected

        expected = [thing1.id, thing2.id]
        assert ents.Thing.pairs('id', 'name',
                                items=lambda obj: obj.id) == expected

    def test_to_dict(self):
        obj = ents.Thing.fake()

        expected = {'id', 'name', 'color', 'scale_check', 'float_check', 'updated_utc',
                    'created_utc', 'units', 'status', 'date_check', 'float_check_prop'}
        assert set(obj.to_dict().keys()) == expected
        assert set(obj.to_dict(exclude={'id'}).keys()) == expected - {'id'}

        hybrids = ['name_and_color']
        exclude = ['name', 'scale_check', 'float_check', 'color', 'updated_utc', 'created_utc',
                   'units', 'status', 'date_check']
        dictionary = obj.to_dict(hybrids=hybrids, exclude=exclude)

        assert dictionary == {
            'id': obj.id,
            'name_and_color': obj.name_and_color,
            'float_check_prop': obj.float_check_prop,
        }

    def test_random_data_for_column(self):
        func = mixins.MethodsMixin.random_data_for_column

        assert type(func(sa.Column(sa.Unicode), None)) == str
        assert type(func(sa.Column(sa.String), None)) == str
        assert type(func(sa.Column(sa.Integer), None)) == int
        assert type(func(sa.Column(sa.Boolean), None)) == bool
        assert type(func(sa.Column(sa.Numeric(1, 1)), None)) == Decimal
        assert type(func(sa.Column(sa.Numeric), None)) == float
        assert type(func(sa.Column(sa.Float), None)) == float
        assert type(func(sa.Column(sa.Date), None)) == datetime.date
        assert type(func(sa.Column(sa.DateTime), None)) == datetime.datetime
        assert type(func(sa.Column(sautils.ArrowType), None)) == arrow.Arrow
        assert isinstance(func(sa.Column(sautils.EmailType), None), str)
        assert isinstance(func(sa.Column(columns.TimeZoneType), None), str)

        with pytest.raises(ValueError):
            assert type(func(sa.Column(sa.LargeBinary), None))

    def test_check_kwargs_in_fake(self):
        ents.Thing.fake(name='a')

        with pytest.raises(AssertionError) as excinfo:
            ents.Thing.fake(foo=1, bar=2, _baz=3, name='b')
        assert str(excinfo.value) == \
            'Unknown column or relationship names in kwargs: [\'bar\', \'foo\']'

        ents.Thing.fake(foo=1, bar=2, _baz=3, name='b', _check_kwargs=False)

    def test_check_kwargs_in_edit(self):
        thing = ents.Thing.fake(name='a')
        with pytest.raises(AssertionError) as excinfo:
            ents.Thing.edit(thing.id, fieldshouldnotexist='foo')
        assert str(excinfo.value) == \
            'Unknown column or relationship names in kwargs: [\'fieldshouldnotexist\']'

        ents.Thing.edit(thing.id, fieldshouldnotexist='foo', _check_kwargs=False)

    def test_check_kwargs_in_add(self):
        with pytest.raises(AssertionError) as excinfo:
            ents.Thing.add(name='kwargs-in-add', fieldshouldnotexist='foo')
        assert str(excinfo.value) == \
            'Unknown column or relationship names in kwargs: [\'fieldshouldnotexist\']'

        db.session.remove()
        ents.Thing.add(name='kwargs-in-add', fieldshouldnotexist='foo', _check_kwargs=False)

    def test_testing_create_flush_and_commit(self):
        obj = ents.Thing.fake(_flush=False, _commit=False)
        assert sa.inspect(obj).pending
        db.session.rollback()
        assert sa.inspect(obj).transient

        obj = ents.Thing.fake(_flush=True, _commit=False)
        assert sa.inspect(obj).persistent
        db.session.rollback()
        assert sa.inspect(obj).transient

        obj = ents.Thing.fake(_flush=False, _commit=True)
        assert sa.inspect(obj).persistent
        db.session.rollback()
        assert sa.inspect(obj).persistent

    def test_override_random_data_generation(self):
        obj = ents.Thing.fake()
        assert obj.color == 'blue'
        assert obj.scale_check == Decimal('12.3456')

    def test_related_object_created(self):
        obj = ents.RelatedThing.fake()
        assert obj.thing

    def test_related_object_respects_id(self):
        thing = ents.Thing.fake()
        obj = ents.RelatedThing.fake(thing_id=thing.id)
        assert obj.thing is thing

    def test_related_object_respects_relationship_attr(self):
        thing = ents.Thing.fake()
        obj = ents.RelatedThing.fake(thing=thing)
        assert obj.thing is thing

    def test_related_object_bad_attributes(self):
        class MyObject(mixins.MethodsMixin):
            pass

        with pytest.raises(Exception, match='expects "thing" on class MyObject'):
            MyObject.testing_set_related({}, ents.Thing)

    def test_related_object_takes_overrides(self):
        class MyObject(mixins.MethodsMixin):
            foo = None
            bar = None

        kwargs = {}
        MyObject.testing_set_related(
            kwargs, ents.Thing, _relationship_name='foo', _relationship_field='bar'
        )
        assert isinstance(kwargs['foo'], ents.Thing)

        thing = ents.Thing.fake()
        kwargs = {'foo': thing}
        MyObject.testing_set_related(
            kwargs, ents.Thing, _relationship_name='foo', _relationship_field='bar'
        )
        assert kwargs['foo'] is thing

        kwargs = {'bar': thing.id}
        MyObject.testing_set_related(
            kwargs, ents.Thing, _relationship_name='foo', _relationship_field='bar'
        )
        assert kwargs['bar'] == thing.id
        assert 'foo' not in kwargs


class TestSoftDeleteMixin:

    def setup_method(self, _):
        ents.SoftDeleteTester.delete_cascaded()
        ents.HardDeleteParent.delete_cascaded()
        db.session.remove()

    def test_delete_sets_field(self):
        sdt1 = ents.SoftDeleteTester.fake()

        assert sdt1.deleted_utc is None
        assert ents.SoftDeleteTester.delete(sdt1.id)
        assert sdt1.deleted_utc is not None

    def test_manual_delete_raises_error(self):
        sdt1 = ents.SoftDeleteTester.fake()

        db.session.delete(sdt1)

        with pytest.raises(mixins.HardDeleteProhibitedError):
            db.session.commit()

        db.session.rollback()

    def test_delete_without_id_returns_none(self):
        assert not ents.SoftDeleteTester.delete(1234)

    def test_delete_cascaded_still_works(self):
        ents.SoftDeleteTester.fake()

        assert ents.SoftDeleteTester.query.count() == 1

        ents.SoftDeleteTester.delete_cascaded()
        assert ents.SoftDeleteTester.query.count() == 0

    def test_testing_create_allows_is_deleted_flag(self):
        sdt1 = ents.SoftDeleteTester.fake()
        assert sdt1.deleted_utc is None

        sdt1 = ents.SoftDeleteTester.fake(_is_deleted=True)
        assert sdt1.deleted_utc is not None

    def test_deleting_the_parent_deletes_the_child(self):
        sdt1 = ents.SoftDeleteTester.fake()
        assert sdt1.hdp == ents.HardDeleteParent.query.one()

        with pytest.raises(mixins.HardDeleteProhibitedError):
            sdt1.hdp.delete(sdt1.hdp_id)


class TestLookupMixin:
    def setup_method(self):
        ents.LookupTester.delete_cascaded()

    def _labels_in_list(labels, rows):
        row_labels = [row.label for row in rows]
        for label in labels:
            if label not in row_labels:
                return False

        return True

    def test_list_active(self):
        a = ents.LookupTester.fake(label='a', deleted_utc=None)
        b = ents.LookupTester.fake(label='b', deleted_utc=None)
        c = ents.LookupTester.fake(label='c', deleted_utc=None)
        d = ents.LookupTester.fake(label='d', deleted_utc=arrow.now())
        e = ents.LookupTester.fake(label='e', deleted_utc=arrow.now())

        rows = ents.LookupTester.list_active()
        assert [a, b, c] == rows

        rows = ents.LookupTester.list_active(order_by=ents.LookupTester.label.desc())
        assert [c, b, a] == rows

        rows = ents.LookupTester.list_active(include_ids=d.id)
        assert [a, b, c, d] == rows

        rows = ents.LookupTester.list_active(include_ids=(d.id, e.id))
        assert [a, b, c, d, e] == rows

    def test_pairs_active(self):
        a = ents.LookupTester.fake(label='a', deleted_utc=None)
        b = ents.LookupTester.fake(label='b', deleted_utc=None)
        c = ents.LookupTester.fake(label='c', deleted_utc=None)
        d = ents.LookupTester.fake(label='d', deleted_utc=arrow.now())
        e = ents.LookupTester.fake(label='e', deleted_utc=arrow.now())

        def make_pairs(*records):
            return [(record.id, record.label) for record in records]

        pairs = ents.LookupTester.pairs_active()
        assert make_pairs(a, b, c) == pairs

        pairs = ents.LookupTester.pairs_active(order_by=ents.LookupTester.label.desc())
        assert make_pairs(c, b, a) == pairs

        pairs = ents.LookupTester.pairs_active(include_ids=d.id)
        assert make_pairs(a, b, c, d) == pairs

        pairs = ents.LookupTester.pairs_active(include_ids=(d.id, e.id))
        assert make_pairs(a, b, c, d, e) == pairs

    def test_get_by_label(self):
        a = ents.LookupTester.fake(label='a', deleted_utc=None)
        b = ents.LookupTester.fake(label='b', deleted_utc=None)

        assert ents.LookupTester.get_by_label('a') == a
        assert ents.LookupTester.get_by_label('b') == b

    def test_get_by_code(self):
        a = ents.LookupTester.fake(label='a', code='foo', deleted_utc=None)
        ents.LookupTester.fake(label='b', deleted_utc=None)

        assert ents.LookupTester.get_by_code('foo') == a

    def test_repr(self):
        a = ents.LookupTester.fake(label='a', deleted_utc=None)
        assert str(a) == '<LookupTester {}:a>'.format(a.id)
