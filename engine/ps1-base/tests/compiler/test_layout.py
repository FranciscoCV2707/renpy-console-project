import struct

from vncompiler.layout import TextLayout


def font_data():
    glyphs = [(code, style) for code in list(range(32, 127)) + [225] for style in (0, 1)]
    return b"FNT1" + bytes((14, 11)) + struct.pack("<H", len(glyphs)) + b"".join(
        struct.pack("<HBBBBBbbB", code, style, 0, 0, 5, 10, 0, 0, 5)
        for code, style in glyphs)


def test_dialogue_wraps_and_paginates():
    layout = TextLayout(font_data(), dialogue_width=25, dialogue_height=28)
    assert layout(b"uno dos tres cuatro") == b"uno\ndos\x0btres\ncuatr\x0bo"


def test_menu_wraps_without_pages_or_control_arguments():
    layout = TextLayout(font_data(), menu_width=25)
    assert layout(b"\x01\x01uno dos tres", menu=True) == b"uno\ndos\ntres"


def test_control_argument_is_not_a_line_break():
    layout = TextLayout(font_data())
    assert layout(b"a\x02\x0ab") == b"a\x02\x0ab"


def test_style_reopened_after_page_and_utf8_preserved():
    layout = TextLayout(font_data(), dialogue_width=10, dialogue_height=14)
    assert layout("\x01\x01áá áá".encode()) == "\x01\x01áá\x0b\x01\x01áá".encode()


def test_long_word_splits_without_losing_letters():
    layout = TextLayout(font_data(), dialogue_width=15)
    assert layout(b"abcdefgh") == b"abc\ndef\ngh"
