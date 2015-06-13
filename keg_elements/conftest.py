from __future__ import absolute_import
from __future__ import unicode_literals

from kegel_app.app import KegElApp


def pytest_configure(config):
    KegElApp.testing_prep()
