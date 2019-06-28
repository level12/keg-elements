import keg_elements.testing as testing
from kegel_app.model import entities


def test_dont_care():
    assert testing.DontCare() == True  # noqa
    assert (testing.DontCare() == True) is True  # noqa
    assert (testing.DontCare() == False) is True  # noqa
    assert (testing.DontCare() == object) is True  # noqa
    assert (testing.DontCare() != object) is False  # noqa
    assert (testing.DontCare()() == object) is True  # noqa
    assert (testing.DontCare()['thing'] == object) is True  # noqa
    assert (testing.DontCare()[1] == object) is True  # noqa


class TestEntityBaseThing(testing.EntityBase):
    entity_cls = entities.Thing

    column_checks = [
        testing.ColumnCheck('name'),
        testing.ColumnCheck('color', required=False),
        testing.ColumnCheck('scale_check', required=False),
        testing.ColumnCheck('float_check', required=False),
        testing.ColumnCheck('units', required=False),
    ]


class TestEntityBaseAncillaryA(testing.EntityBase):
    entity_cls = entities.AncillaryA

    column_checks = [
        testing.ColumnCheck('thing_id', fk='things.id')
    ]


class TestEntityBaseAncillaryB(testing.EntityBase):
    entity_cls = entities.AncillaryB

    column_checks = [
        testing.ColumnCheck('thing_id', fk='things.id')
    ]


class TestEntityBaseUsesBothFkSet(testing.EntityBase):
    entity_cls = entities.UsesBoth

    column_checks = [
        testing.ColumnCheck('thing_id', fk={'ancillary_as.thing_id', 'ancillary_bs.thing_id'}),
        testing.ColumnCheck('ancillary_a_id', fk='ancillary_as.id'),
        testing.ColumnCheck('ancillary_b_id', fk='ancillary_bs.id'),
    ]


class TestEntityBaseUsesBothFkList(testing.EntityBase):
    entity_cls = entities.UsesBoth

    column_checks = [
        testing.ColumnCheck('thing_id', fk=['ancillary_as.thing_id', 'ancillary_bs.thing_id']),
        testing.ColumnCheck('ancillary_a_id', fk='ancillary_as.id'),
        testing.ColumnCheck('ancillary_b_id', fk='ancillary_bs.id'),
    ]


class TestEntityBaseUsesBothFkString(testing.EntityBase):
    entity_cls = entities.UsesBoth

    column_checks = [
        testing.ColumnCheck('thing_id', fk='ancillary_as.thing_id, ancillary_bs.thing_id'),
        testing.ColumnCheck('ancillary_a_id', fk='ancillary_as.id'),
        testing.ColumnCheck('ancillary_b_id', fk='ancillary_bs.id'),
    ]
