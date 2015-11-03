import pytest
import validators

from keg_elements.db.utils import randemail


def test_randemail():
    for length in range(0, 6):
        with pytest.raises(ValueError):
            randemail(length)

    def not_so_rand_email(length, char):
        return randemail(length, randomizer=lambda n, *args, **kwargs: char * n)

    assert not_so_rand_email(7, 'a') == 'a@a.aaa'
    assert not_so_rand_email(8, 'b') == 'b@bb.bbb'
    assert not_so_rand_email(9, 'c') == 'cc@cc.ccc'

    # Fuzzy testing for an extra dose of confidence
    for length in range(7, 50):
        email = randemail(length)
        assert len(email) == length
        assert validators.email(email)

    # Get some confidence of randomness
    assert len(set(randemail(50) for _ in range(5))) == 5, \
        'randemail not random (beware non-determinism; try again)'
