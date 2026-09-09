"""Offline translation contract checks: python tests_translate.py."""
from __future__ import annotations

import warnings

from pipeline.translate import PhanHoi, dich


def test_translation_validation_and_context() -> None:
    calls = []

    def good(request):
        calls.append(request)
        return PhanHoi({"lines": {k: "vi " + v for k, v in request["lines"].items()},
                        "thuat_ngu_moi": {"A": "changed", "B": "Bee"}}, token_vao=3, token_ra=4)

    lines = [str(i) for i in range(450)]
    result = dich(lines, {"A": "Ay"}, good)
    assert result.ban == ["vi " + s for s in lines]
    assert len(calls) == 2 and calls[1]["context"] == lines[395:400]
    assert calls[1]["glossary"] == {"A": "Ay", "B": "Bee"}
    assert result.thuat_ngu_moi == {"B": "Bee"} and result.giu_nguon == []
    assert (result.token_vao, result.token_ra) == (6, 8)

    for invalid in (None, "", "  ", 7, [], "one\n \ntwo"):
        calls.clear()
        def partial(request):
            calls.append(request)
            if len(calls) == 1:
                return PhanHoi({"lines": {"1": "good", "2": invalid, "9": "extra"}})
            assert request["lines"] == {"1": "second"}
            assert request["context"] == ["first"]
            return PhanHoi({"lines": {"1": "fixed"}})
        with warnings.catch_warnings(record=True) as reported:
            result = dich(["first", "second"], {}, partial)
        assert result.ban == ["good", "fixed"] and len(calls) == 2 and reported

    for invalid in ([], {"lines": []}, {"lines": {}}, "{bad", None):
        calls.clear()
        def broken(request):
            calls.append(request)
            return PhanHoi(invalid)
        with warnings.catch_warnings(record=True):
            result = dich(["a"] * 8, {}, broken)
        assert result.ban == ["a"] * 8 and result.giu_nguon == list(range(8))
        assert len(calls) == 15  # root + 2 halves + 4 leaves + 8 single retries

    calls.clear()
    def split(request):
        calls.append(request)
        if len(calls) == 1:
            return PhanHoi({"lines": {"1": "truncated"}}, finish_reason="length")
        return PhanHoi({"lines": {k: "ok" for k in request["lines"]},
                        "thuat_ngu_moi": {"new": "term"}})
    with warnings.catch_warnings(record=True):
        assert dich(["a", "b", "c", "d"], {}, split).ban == ["ok"] * 4
    assert len(calls) == 3 and calls[2]["glossary"] == {"new": "term"}

    for terms in ([], {"x": 9}, {"": "bad"}):
        with warnings.catch_warnings(record=True) as reported:
            result = dich(["a"], {}, lambda req: PhanHoi({"lines": {"1": "ok"}, "thuat_ngu_moi": terms}))
        assert result.ban == ["ok"] and result.thuat_ngu_moi == {} and reported

    calls.clear()
    def network(request):
        calls.append(request)
        raise ConnectionError("offline")
    try:
        dich(["a", "b"], {}, network)
    except ConnectionError:
        assert len(calls) == 1
    else:
        raise AssertionError("Transport error must propagate without split")

    large_glossary = {str(i): f"term {i}" for i in range(501)}
    def json_response(request):
        assert request["glossary"] == large_glossary
        return PhanHoi('{"lines":{"1":"first\\nsecond"}}')
    assert dich(["a"], large_glossary, json_response).ban == ["first\nsecond"]
    for source, terms, size in (([], {}, 400), (["\n"], {}, 400),
                                 (["a"], {"x": 7}, 400), (["a"], {}, 0)):
        try:
            dich(source, terms, lambda req: (_ for _ in ()).throw(AssertionError("unexpected call")), size)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid input was accepted")


if __name__ == "__main__":
    test_translation_validation_and_context()
    print("translation checks passed")
