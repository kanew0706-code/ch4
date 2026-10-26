import json

import pytest

from place_agent.analyzer import AnalysisError, parse_output, validate

GOOD = {
    "is_place": True,
    "identified": True,
    "name": "台北 101",
    "short_name": "台北101",
    "scenery": ["摩天大樓", "藍天"],
    "intro": "曾是世界最高的大樓。跨年煙火很有名。",
}


def envelope(**fields) -> str:
    return json.dumps({"type": "result", "is_error": False, **fields})


def test_structured_output():
    result = parse_output(envelope(structured_output=GOOD))
    assert result.name == "台北 101"
    assert result.scenery == ["摩天大樓", "藍天"]


def test_falls_back_to_json_inside_result_text():
    text = "好的，結果如下：\n```json\n" + json.dumps(GOOD, ensure_ascii=False) + "\n```"
    assert parse_output(envelope(result=text)).identified is True


@pytest.mark.parametrize(
    "stdout",
    [
        "這不是 JSON",
        "",
        "[1, 2]",
        envelope(is_error=True, result="rate limited"),
        envelope(result="我看不出來這是哪裡"),
        envelope(result="{壞掉的 json"),
    ],
)
def test_bad_output_raises_analysis_error(stdout):
    with pytest.raises(AnalysisError):
        parse_output(stdout)


@pytest.mark.parametrize(
    "field, value",
    [
        ("is_place", "yes"),
        ("is_place", None),
        ("identified", 1),
        ("name", ""),
        ("name", None),
        ("scenery", 123),
    ],
)
def test_bad_fields_raise_analysis_error(field, value):
    with pytest.raises(AnalysisError):
        validate({**GOOD, field: value})


def test_long_text_is_truncated():
    result = validate({**GOOD, "intro": "很" * 1000, "scenery": ["山"] * 50})
    assert len(result.intro) == 300
    assert len(result.scenery) == 10


def test_not_place_clears_scenery_and_intro():
    result = validate({**GOOD, "is_place": False, "name": "馬克杯"})
    assert (result.identified, result.scenery, result.intro) == (False, [], "")
