from keg.testing import ContextManager
import pytest

from kegel_app.app import KegElApp


def pytest_configure(config):
    app = KegElApp.testing_prep()

    from keg.db import db
    with app.app_context():
        print('Running tests against {} DB'.format(db.engine.dialect.name))


@pytest.fixture(scope='class', autouse=True)
def auto_app_context():
    with ContextManager.get_for(KegElApp).app.app_context():
        yield
