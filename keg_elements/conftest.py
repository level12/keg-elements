from kegel_app.app import KegElApp


def pytest_configure(config):
    KegElApp.testing_prep()
