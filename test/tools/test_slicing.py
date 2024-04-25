def test_slice_len():
    import random
    from navigate.tools.slicing import slice_len

    for _ in range(100):
        n0 = random.randint(1,10)
        n1 = random.randint(1,10)
        sl = slice(0,n0,1)

        assert slice_len(sl, n1) == min(n0,n1)

def test_ensure_iter():
    from navigate.tools.slicing import ensure_iter

    ensure_iter(2, 0, 1) == range(0, 1)
    ensure_iter(2, 1, 1) == range(0, 1)
    ensure_iter(2, 0, 5) == range(2, 3)
    ensure_iter(2, 1, 5) == range(0, 5)
    ensure_iter(slice(0, 2), 0, 1) == range(0, 1)
    ensure_iter(slice(0, 2), 1, 1) == range(0, 1)
    ensure_iter(slice(0, 2), 0, 5) == range(0, 2)
    ensure_iter(slice(0, 2), 1, 5) == range(0, 5)

def test_ensure_slice():
    from navigate.tools.slicing import ensure_slice

    ensure_slice(2, 0) == slice(2, 3)
    ensure_slice(2, 1) == slice(None, None, None)
    ensure_slice(slice(0, 2), 0) == slice(0, 2, None)
    ensure_slice(slice(0, 2), 1) == slice(None, None, None)
