import keg_elements.testing as testing


def test_dont_care():
    assert testing.DontCare() == True  # noqa
    assert (testing.DontCare() == True) is True  # noqa
    assert (testing.DontCare() == False) is True  # noqa
    assert (testing.DontCare() == object) is True  # noqa
    assert (testing.DontCare() != object) is False  # noqa
    assert (testing.DontCare()() == object) is True  # noqa
    assert (testing.DontCare()['thing'] == object) is True  # noqa
    assert (testing.DontCare()[1] == object) is True  # noqa
