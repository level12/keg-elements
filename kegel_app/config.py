import os


class DefaultProfile(object):
    KEG_KEYRING_ENABLE = False

    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite://')


class TestProfile(object):
    KEG_KEYRING_ENABLE = False

    # Turn off CSRF protection for tests.  Makes form testing easier and provides no value during
    # testing.
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:@localhost/keg-elem-test'

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite://')
