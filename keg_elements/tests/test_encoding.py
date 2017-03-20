import six
import keg_elements.encoding as encoding


def test_force_bytes():
    memory = memoryview('a') if six.PY2 else memoryview(b'a')

    assert encoding.force_bytes(memory) == b'a'
    assert encoding.force_bytes('a') == b'a'
    assert encoding.force_bytes(b'a') == b'a'

    try:
        encoding.force_bytes(True)
    except AttributeError:
        pass
    else:
        raise AssertionError('Expected force_bytes to throw')
