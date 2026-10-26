from place_agent.analyzer import Analysis
from place_agent.bot import format_reply, photo_label, place_name

KNOWN = Analysis(True, True, "台北 101", "台北101", ["摩天大樓"], "很高。")
UNKNOWN = Analysis(True, False, "海邊夕陽", "海邊夕陽", ["海", "夕陽"], "傍晚的海邊。")
NOT_PLACE = Analysis(False, False, "馬克杯", "馬克杯", [], "")


def test_place_name_column():
    assert place_name(KNOWN) == "台北 101"
    assert place_name(UNKNOWN) == "無法確定（海邊夕陽）"
    assert place_name(NOT_PLACE) == "不是地方"


def test_photo_label():
    assert photo_label(KNOWN) == "台北101"
    assert photo_label(UNKNOWN) == "無法確定-海邊夕陽"
    assert photo_label(NOT_PLACE) == "不是地方-馬克杯"


def test_reply_text():
    assert format_reply(KNOWN) == "📍 台北 101\n景物：摩天大樓\n特色：很高。"
    assert format_reply(UNKNOWN).startswith("📍 無法確定（海邊夕陽）")
    assert format_reply(NOT_PLACE) == "🚫 你傳的不是地方，是「馬克杯」。"
