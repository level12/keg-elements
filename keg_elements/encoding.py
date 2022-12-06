def force_bytes(s, encoding='utf-8', errors='strict'):
    """Force objects to byte representation"""
    # Handle the common case first for performance reasons.
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)
    elif isinstance(s, memoryview):
        return bytes(s)
    else:
        return s.encode(encoding, errors)
