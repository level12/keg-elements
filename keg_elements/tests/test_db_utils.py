import sys
from decimal import Decimal

import _pytest
import pytest
import validators
import keg
import sqlalchemy as sa

import keg_elements.db.utils as dbutils
import kegel_app.model.entities as ents


def test_randemail():
    for length in range(0, 6):
        with pytest.raises(ValueError):
            dbutils.randemail(length)

    def not_so_rand_email(length, char):
        return dbutils.randemail(length, randomizer=lambda n, *args, **kwargs: char * n)

    assert not_so_rand_email(7, 'a') == 'a@a.aaa'
    assert not_so_rand_email(8, 'b') == 'b@bb.bbb'
    assert not_so_rand_email(9, 'c') == 'cc@cc.ccc'

    # Fuzzy testing for an extra dose of confidence
    for length in range(7, 50):
        email = dbutils.randemail(length)
        assert len(email) == length
        assert validators.email(email)

    # Get some confidence of randomness
    assert len(set(dbutils.randemail(50) for _ in range(5))) == 5, \
        'randemail not random (beware non-determinism; try again)'


class TestUpdateCollection(object):

    def setup_method(self, method):
        keg.db.db.session.remove()
        ents.Thing.delete_cascaded()
        ents.RelatedThing.delete_cascaded()

    def test_add(self):
        thing = ents.Thing.testing_create()
        assert not thing.related_things

        data = [{'name': 'test', 'is_enabled': True}]
        thing.update_collection('related_things', data)

        assert len(thing.related_things) == 1
        related = thing.related_things[0]
        assert related.name == 'test'
        assert related.is_enabled

    def test_edit(self):
        thing = ents.Thing.testing_create()
        related1_id = ents.RelatedThing.testing_create(thing=thing, name='a').id
        related2_id = ents.RelatedThing.testing_create(thing=thing, name='x').id

        data = [
            {'id': related1_id, 'name': 'b', 'is_enabled': False},
            {'id': related2_id, 'name': 'y', 'is_enabled': False},
        ]
        thing.update_collection('related_things', data)

        keg.db.db.session.flush()

        assert len(thing.related_things) == 2
        related1 = thing.related_things[0]
        assert related1.id == related1_id
        assert related1.name == 'b'
        assert not related1.is_enabled

        related2 = thing.related_things[1]
        assert related2.id == related2_id
        assert related2.name == 'y'
        assert not related2.is_enabled

    def test_append_id_none(self):
        thing = ents.Thing.testing_create()
        related = ents.RelatedThing.testing_create(thing=thing, name='a',
                                                   is_enabled=True)

        data = [
            {'is_enabled': False}
        ]
        thing.update_collection('related_things', data)

        assert len(thing.related_things) == 1
        related = thing.related_things[0]

        assert related.name is None
        assert not related.is_enabled

    def test_remove(self):
        thing = ents.Thing.testing_create()
        ents.RelatedThing.testing_create(thing=thing, name='a', is_enabled=True)
        assert len(thing.related_things) == 1

        data = []
        thing.update_collection('related_things', data)

        assert len(thing.related_things) == 0


class TestExceptionHelpers:
    def setup_method(self, _):
        ents.ConstraintTester.delete_cascaded()

    def test_validate_unique_exception_unnamed(self):
        ents.ConstraintTester.testing_create(unique1=1)
        with pytest.raises(Exception) as exc:
            ents.ConstraintTester.testing_create(unique1=1)
        assert dbutils.validate_unique_exc(exc.value) is True

        with pytest.raises(Exception) as exc:
            ents.ConstraintTester.testing_create(check=101)
        assert dbutils.validate_unique_exc(exc.value) is False

    def test_validate_unique_exception_named(self):
        ents.ConstraintTester.testing_create(unique2=1)
        with pytest.raises(Exception) as exc:
            ents.ConstraintTester.testing_create(unique2=1)
        assert dbutils.validate_unique_exc(exc.value, 'uq_constraint_tester_unique2') is True

    def test_validate_unique_msg_postgres(self):
        postgres_msg = (
            '(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint '
            '"uq_constraint_tester_unique2"'
        )
        assert dbutils._validate_unique_msg('postgresql', postgres_msg) is True
        assert dbutils._validate_unique_msg(
            'postgresql',
            postgres_msg,
            'uq_constraint_tester_unique2'
        ) is True

        assert dbutils._validate_unique_msg(
            'postgresql',
            postgres_msg,
            'uq_constraint_tester_unique1'
        ) is False
        assert dbutils._validate_unique_msg('mssql', postgres_msg) is False

    def test_validate_unique_msg_mssql(self):
        mssql_msg = (
            "Violation of UNIQUE constraint 'uq_constraint_tester_unique2'. "
            "Cannot insert duplicate key in object 'dbo.constraint_tester'. "
            'The duplicate key value is (1).'
        )
        assert dbutils._validate_unique_msg('mssql', mssql_msg) is True
        assert dbutils._validate_unique_msg(
            'mssql',
            mssql_msg,
            'uq_constraint_tester_unique2'
        ) is True

        assert dbutils._validate_unique_msg(
            'mssql',
            mssql_msg,
            'uq_constraint_tester_unique1'
        ) is False
        assert dbutils._validate_unique_msg('postgresql', mssql_msg) is False

    def test_validate_unique_msg_sqlite(self):
        sqlite_msg = '(sqlite3.IntegrityError) UNIQUE constraint failed: constraint_tester.unique2'
        assert dbutils._validate_unique_msg('sqlite', sqlite_msg) is True
        assert dbutils._validate_unique_msg(
            'sqlite',
            sqlite_msg,
            'uq_constraint_tester_unique2'
        ) is True

        assert dbutils._validate_unique_msg('postgresql', sqlite_msg) is False

    def test_validate_unique_msg_unsupported(self):
        sqlite_msg = '(sqlite3.IntegrityError) UNIQUE constraint failed: constraint_tester.unique2'
        with pytest.raises(ValueError) as exc:
            dbutils._validate_unique_msg('unknown', sqlite_msg)
        assert str(exc.value) == 'is_unique_exc() does not yet support dialect: unknown'

    @pytest.mark.skipif(sys.version_info.major < 3, reason='requires python 3')
    def test_raises_unique_exception(self):
        ents.ConstraintTester.testing_create(unique2=1)

        @dbutils.raises_unique_exc('uq_constraint_tester_unique2')
        def make_dup():
            ents.ConstraintTester.testing_create(unique2=1)

        make_dup()

        @dbutils.raises_unique_exc('uq_constraint_tester_unique2')
        def make_uq():
            ents.ConstraintTester.testing_create()

        with pytest.raises(_pytest.outcomes.Failed):
            make_uq()

        @dbutils.raises_unique_exc('uq_constraint_tester_unique2')
        def make_ck():
            ents.ConstraintTester.testing_create(check=101)

        with pytest.raises(AssertionError):
            make_ck()

    def test_is_check_constraint_sqlite(self):
        assert dbutils._is_check_const(
            'sqlite',
            '(sqlite3.IntegrityError) CHECK constraint failed: ck_constraint_tester_check',
            'ck_constraint_tester_check'
        ) is True

        assert dbutils._is_check_const(
            'sqlite',
            '(sqlite3.IntegrityError) UNIQUE constraint failed: constraint_tester.unique2',
            'ck_constraint_tester_check'
        ) is False

    def test_is_check_constraint_mssql(self):
        mssql_msg = (
            'The INSERT statement conflicted with the CHECK constraint '
            '"ck_constraint_tester_check".'
        )
        assert dbutils._is_check_const('mssql', mssql_msg, 'ck_constraint_tester_check') is True

        assert dbutils._is_check_const('mssql', mssql_msg, 'uq_constraint_tester_unique2') is False
        assert dbutils._is_check_const('sqlite', mssql_msg, 'ck_constraint_tester_check') is False

    def test_is_check_constraint_postgres(self):
        postgres_msg = (
            '(psycopg2.errors.CheckViolation) new row for relation "constraint_tester" violates '
            'check constraint "ck_constraint_tester_check"'
        )
        assert dbutils._is_check_const(
            'postgresql',
            postgres_msg,
            'ck_constraint_tester_check'
        ) is True

        assert dbutils._is_check_const(
            'postgresql',
            postgres_msg,
            'uq_constraint_tester_unique2'
        ) is False
        assert dbutils._is_check_const(
            'sqlite',
            postgres_msg,
            'ck_constraint_tester_check'
        ) is False

    def test_is_check_constraint_unsupported(self):
        sqlite_msg = '(sqlite3.IntegrityError) CHECK constraint failed: ck_constraint_tester_check'
        with pytest.raises(ValueError) as exc:
            dbutils._is_check_const('unknown', sqlite_msg, 'ck_constraint_tester_check')
        assert str(exc.value) == 'is_constraint_exc() does not yet support dialect: unknown'

    @pytest.mark.skipif(sys.version_info.major < 3, reason='requires python 3')
    def test_raises_check_exc(self):
        @dbutils.raises_check_exc('ck_constraint_tester_check')
        def make_fail():
            ents.ConstraintTester.testing_create(check=101)

        make_fail()

        @dbutils.raises_check_exc('ck_constraint_tester_check')
        def make_pass():
            ents.ConstraintTester.testing_create()

        with pytest.raises(_pytest.outcomes.Failed):
            make_pass()

        @dbutils.raises_check_exc('ck_constraint_tester_check')
        def make_uq():
            ents.ConstraintTester.testing_create(unique1=1)
            ents.ConstraintTester.testing_create(unique1=1)

        with pytest.raises(AssertionError):
            make_uq()


# Repeat parameter used to somewhat counteract the non-deterministic nature of the tested function
@pytest.mark.parametrize('repeat', range(1, 20))
@pytest.mark.parametrize('scale,prec,max', [
    (1, 1, Decimal('0.9')),
    (2, 1, Decimal('9.9')),
    (3, 3, Decimal('0.999')),
    (3, 2, Decimal('9.99')),
    (3, 1, Decimal('9.9')),
    (3, 0, Decimal('99.0')),
    (4, 4, Decimal('0.9999')),
    (4, 3, Decimal('9.999')),
    (4, 2, Decimal('99.99')),
    (4, 1, Decimal('99.9')),
    (4, 0, Decimal('99.0')),
])
def test_random_numeric(scale, prec, max, repeat):
    col = sa.Column(sa.Numeric(scale, prec))
    value = dbutils.random_numeric(col)
    assert value <= max
    assert value >= -max
