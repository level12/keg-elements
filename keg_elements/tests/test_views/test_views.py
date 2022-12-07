from unittest import mock

import flask
import flask_webtest
from pyquery import PyQuery
from webgrid.extensions import RequestArgsLoader

from kegel_app.model import entities as ents


def setup_module():
    from keg.db import db
    db.session.remove()


class TestDemoForm:
    def test_get(self):
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-form')
        assert 'Input field' in resp

    def test_post_valid(self):
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-form')
        resp.form['my_field'] = 'foo'
        resp = resp.form.submit()
        assert resp.flashes == [('success', 'Form submitted successfully.')]
        assert resp.location.endswith('demo-grid')

    def test_post_invalid(self):
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-form')
        resp = resp.form.submit()
        assert resp.flashes == [('error', 'Form errors detected, see below for details.')]
        assert resp.status_code == 200
        assert 'Input field' in resp


class TestDemoGrid:
    def setup_method(self):
        ents.Thing.delete_cascaded()

    def test_get(self):
        ents.Thing.fake(name='Thing Foo')
        ents.Thing.fake(name='Thing Two')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-grid')
        assert 'datagrid' in resp
        assert 'Thing Foo' in resp
        assert 'Thing Two' in resp
        assert PyQuery(resp.body)('form.header').attr('method') == 'post'

    def test_qs_args_applied(self):
        ents.Thing.fake(name='Thing Foo')
        ents.Thing.fake(name='Thing Two')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-grid?op(name)=contains&v1(name)=Foo')
        assert 'datagrid' in resp
        assert 'Thing Foo' in resp
        assert 'Thing Two' not in resp

    def test_post(self):
        ents.Thing.fake(name='Thing Foo')
        ents.Thing.fake(name='Thing Two')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.post('/demo-grid?session_key=abc123', {
            'op(name)': 'contains',
            'v1(name)': 'Foo',
        }, status=302)
        assert resp.location.endswith('/demo-grid?session_key=abc123')
        resp = resp.follow()
        assert 'datagrid' in resp
        assert 'Thing Foo' in resp
        assert 'Thing Two' not in resp

    @mock.patch('kegel_app.grids.DemoGrid.session_on', False)
    def test_post_no_session(self):
        ents.Thing.fake(name='Thing Foo')
        ents.Thing.fake(name='Thing Two')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.post('/demo-grid?session_key=abc123', {
            'op(name)': 'contains',
            'v1(name)': 'Foo',
        })
        assert 'datagrid' in resp
        assert 'Thing Foo' in resp
        assert 'Thing Two' not in resp

    @mock.patch('kegel_app.grids.DemoGrid.manager.args_loaders', [RequestArgsLoader])
    def test_post_no_form_loader(self):
        client = flask_webtest.TestApp(flask.current_app)
        client.post('/demo-grid?session_key=abc123', {
            'op(name)': 'contains',
            'v1(name)': 'Foo',
        }, status=405)

    def test_export(self):
        ents.Thing.fake(name='Thing Foo')
        client = flask_webtest.TestApp(flask.current_app)
        resp = client.get('/demo-grid?export_to=xlsx')
        assert 'spreadsheetml' in resp.content_type
