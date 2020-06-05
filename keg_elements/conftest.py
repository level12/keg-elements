from kegel_app.app import KegElApp


def pytest_configure(config):
    KegElApp.testing_prep()

    from keg.db import db
    print('Running tests against {} DB'.format(db.engine.dialect.name))
