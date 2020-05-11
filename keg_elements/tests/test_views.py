import flask
import flask_webtest

from kegel_app.model import entities as ents


class TestDemoGrid:
    def setup(self):
        ents.Thing.delete_cascaded()

    def test_get(self):
        ents.Thing.testing_create(name='Thing Foo')
        ents.Thing.testing_create(name='Thing Two')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-grid')
        assert 'datagrid' in resp
        assert 'Thing Foo' in resp
        assert 'Thing Two' in resp

    def test_qs_args_applied(self):
        ents.Thing.testing_create(name='Thing Foo')
        ents.Thing.testing_create(name='Thing Two')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-grid?op(name)=contains&v1(name)=Foo')
        assert 'datagrid' in resp
        assert 'Thing Foo' in resp
        assert 'Thing Two' not in resp

    def test_export(self):
        ents.Thing.testing_create(name='Thing Foo')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-grid?export_to=xlsx')
        assert 'spreadsheetml' in resp.content_type
