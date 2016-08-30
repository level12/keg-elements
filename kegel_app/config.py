class TestProfile(object):
    KEG_KEYRING_ENABLE = False

    # Turn off CSRF protection for tests.  Makes form testing easier and provides no value during
    # testing.
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
