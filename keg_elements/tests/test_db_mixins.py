import datetime

from keg.db import db
import arrow
import pytest
import six
import sqlalchemy as sa
import sqlalchemy_utils as sautils
import keg_elements.db.mixins as mixins
import keg_elements.db.columns as columns

import kegel_app.model.entities as ents


class TestDefaultColsMixin:

    def setup_method(self, fn):
        ents.Thing.delete_cascaded()

    def test_default_odering(self):
        thing1 = ents.Thing.testing_create(id=6)
        thing2 = ents.Thing.testing_create(id=5)
        thing3 = ents.Thing.testing_create(id=7)

        assert ents.Thing.query.all() == [thing2, thing1, thing3]


class TestMethodsMixin:

    def setup_method(self, fn):
        ents.Thing.delete_cascaded()

    def test_add(self):
        ents.Thing.add(name='name', color='color', scale_check=1)
        assert ents.Thing.query.count() == 1

        row = ents.Thing.query.first()

        assert row.name == 'name'
        assert row.color == 'color'
        assert row.scale_check == 1

    def test_delete(self):
        thing = ents.Thing.testing_create()
        assert ents.Thing.query.count() == 1

        ents.Thing.delete(thing.id)
        assert ents.Thing.query.count() == 0

        assert ents.Thing.query.get(1) is None
        assert ents.Thing.delete(1) is False

    def test_delete_cascaded(self):
        ents.Thing.testing_create()
        assert ents.Thing.query.count() == 1

        ents.Thing.delete_cascaded()
        assert ents.Thing.query.count() == 0

    def test_edit(self):
        thing1 = ents.Thing.testing_create()

        ents.Thing.edit(thing1.id, name='edited')
        assert thing1.name == 'edited'

        with pytest.raises(AttributeError):
            ents.Thing.edit(name='edited')

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

        with pytest.raises(sa.exc.IntegrityError):
            ents.MultiplePrimaryKeys.add_or_edit({'name': 'other', 'id': 1})

        with pytest.raises(sa.exc.IntegrityError):
            ents.MultiplePrimaryKeys.add_or_edit({'name': 'other', 'other_pk': 1})

        ents.MultiplePrimaryKeys.add_or_edit({'name': 'other', 'id': 1, 'other_pk': 1})
        assert obj.name == 'other'

    def test_get_by(self):

        def returns_none_when_count_is_zero():
            assert ents.Thing.get_by(id=1) is None

        def returns_object_when_one_exists():
            thing = ents.Thing.testing_create()

            assert ents.Thing.get_by(id=thing.id) == thing

        def raises_when_multiple_exists():
            ents.Thing.testing_create(name='foo')
            ents.Thing.testing_create(name='foo')

            with pytest.raises(sa.orm.exc.MultipleResultsFound):
                ents.Thing.get_by(name='foo')

        returns_none_when_count_is_zero()
        returns_object_when_one_exists()
        raises_when_multiple_exists()

    def test_get_where(self):
        thing1 = ents.Thing.testing_create(name='thing1', color='black')
        ents.Thing.testing_create(name='thing2', color='black', scale_check=10)
        thing3 = ents.Thing.testing_create(name='thing3', color='orange', scale_check=10)

        assert ents.Thing.get_where(ents.Thing.name == 'thing1') == thing1
        assert ents.Thing.get_where(ents.Thing.name == 'thing5') is None
        assert (ents.Thing.get_where(ents.Thing.color == 'orange',
                                     ents.Thing.scale_check == 10) == thing3)

        with pytest.raises(sa.orm.exc.MultipleResultsFound):
            ents.Thing.get_where(ents.Thing.color == 'black')

    def test_pairs_takes_name_and_value_and_retuns_list_of_tuples(self):
        thing1 = ents.Thing.testing_create(name='A', color='orange')
        thing2 = ents.Thing.testing_create(name='B', color='black')

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
        obj = ents.Thing.testing_create()

        expected = {'id', 'name', 'color', 'scale_check', 'updated_utc', 'created_utc'}
        assert set(obj.to_dict().keys()) == expected
        assert set(obj.to_dict(exclude={'id'}).keys()) == expected - {'id'}

        hybrids, exclude = (['name_and_color'],
                            ['name', 'scale_check', 'color', 'updated_utc', 'created_utc'])
        dictionary = obj.to_dict(hybrids=hybrids, exclude=exclude)

        assert dictionary == {
            'id': obj.id,
            'name_and_color': obj.name_and_color
        }

    def test_random_data_for_column(self):
        func = mixins.MethodsMixin.random_data_for_column

        assert type(func(sa.Column(sa.Unicode), 0, 0)) == six.text_type
        assert type(func(sa.Column(sa.String), 0, 0)) == six.text_type
        assert type(func(sa.Column(sa.Integer), 0, 0)) == int
        assert type(func(sa.Column(sa.Boolean), 0, 0)) == bool
        assert type(func(sa.Column(sa.Numeric), 0, 0)) == float
        assert type(func(sa.Column(sa.Date), 0, 0)) == datetime.date
        assert type(func(sa.Column(sa.DateTime), 0, 0)) == datetime.datetime
        assert type(func(sa.Column(sautils.ArrowType), 0, 0)) == arrow.Arrow
        assert isinstance(func(sa.Column(sautils.EmailType), 0, 0), six.text_type)
        assert isinstance(func(sa.Column(columns.TimeZoneType), 0, 0), str)

        with pytest.raises(ValueError):
            assert type(func(sa.Column(sa.LargeBinary), 0, 0))
