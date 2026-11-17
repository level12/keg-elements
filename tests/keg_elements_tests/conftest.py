from keg.testing import ContextManager
from kegel_app.app import KegElApp
import pytest


def pytest_configure(config):
    app = KegElApp.testing_prep()

    from keg.db import db

    with app.app_context():
        print(f'Running tests against {db.engine.dialect.name} DB')


@pytest.fixture(scope='class', autouse=True)
def auto_app_context():
    with ContextManager.get_for(KegElApp).app.app_context():
        yield
