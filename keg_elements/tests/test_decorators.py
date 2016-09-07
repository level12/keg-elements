import keg_elements.decorators as decor


class TestKeywordOptional:
    class optional_execute:
        def __init__(self):
            self.called = False

        def __call__(self):
            self.called = True

    def test_keyword_optional_runs_with_true_pass(self):
        run_me = self.optional_execute()

        @decor.keyword_optional('test', before=run_me)
        def wrapped():
            pass

        wrapped(test=True)
        assert run_me.called is True

    def test_keyword_optional_doesnt_run_with_false_pass(self):
        run_me = self.optional_execute()

        @decor.keyword_optional('test', before=run_me)
        def wrapped():
            pass

        wrapped(test=False)
        assert run_me.called is False

    def test_keyword_optional_passes_keyword_when_told(self):
        run_me = self.optional_execute()

        @decor.keyword_optional('test', before=run_me, keep_keyword=True)
        def wrapped(test):
            return test

        assert wrapped(test=True) is True
        assert run_me.called is True

    def test_keyword_runs_after(self):
        run_me = self.optional_execute()

        @decor.keyword_optional('test', after=run_me)
        def wrapped():
            pass

        wrapped(test=True)
        assert run_me.called is True

    def test_when_missing_executes(self):
        run_me = self.optional_execute()

        @decor.keyword_optional('test', after=run_me, when_missing=True)
        def wrapped():
            pass

        wrapped(test=True)
        assert run_me.called is True
