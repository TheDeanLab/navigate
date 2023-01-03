from time import time


def function_timer(func):
    """
    Decorator for evaluating the duration of time necessary to execute a statement.
    """

    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f"Function {func.__name__!r} executed in {(t2 - t1):.4f}s")
        return result

    return wrap_func
