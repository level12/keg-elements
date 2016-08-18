import kegel_app.model.entities as ents


class TestMethodsMixin:

    def setup_method(self, fn):
        ents.Thing.delete_all()

    def test_add(self):
        ents.Thing.add(name='name', color='color', scale_check=1)
        assert ents.Thing.query.count() == 1

        row = ents.Thing.query.first()

        assert row.name == 'name'
        assert row.color == 'color'
        assert row.scale_check == 1

    def test_delete_all(self):
        ents.Thing.add(name='something', color='blah', scale_check=1)
        assert ents.Thing.query.count() == 1

        ents.Thing.delete_all()
        assert ents.Thing.query.count() == 0
