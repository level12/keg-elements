import wrapt


def keyword_optional(keyword, before=False, after=False, keep_keyword=False,
                     when_missing=False):
    """Execute a function before and after the decorated function if the keyword
    is in the kwargs

    Examples:
        def do_thing():
            # ... does something ...

        @keyword_optional('_do_thing', before=do_thing)
        def func(data):
            return data

        func(data, _do_thing=True)
    """

    @wrapt.decorator
    def _execute(wrapped, instance, args, kwargs):
        do_it = (kwargs.get(keyword, when_missing)
                 if keep_keyword
                 else kwargs.pop(keyword, when_missing))

        if before and do_it:
            before()

        result = wrapped(*args, **kwargs)

        if after and do_it:
            after()

        return result

    return _execute
