import pytest
import validators
import keg

from keg_elements.db.utils import randemail
import kegel_app.model.entities as ents


def test_randemail():
    for length in range(0, 6):
        with pytest.raises(ValueError):
            randemail(length)

    def not_so_rand_email(length, char):
        return randemail(length, randomizer=lambda n, *args, **kwargs: char * n)

    assert not_so_rand_email(7, 'a') == 'a@a.aaa'
    assert not_so_rand_email(8, 'b') == 'b@bb.bbb'
    assert not_so_rand_email(9, 'c') == 'cc@cc.ccc'

    # Fuzzy testing for an extra dose of confidence
    for length in range(7, 50):
        email = randemail(length)
        assert len(email) == length
        assert validators.email(email)

    # Get some confidence of randomness
    assert len(set(randemail(50) for _ in range(5))) == 5, \
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
