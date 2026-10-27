"""Pruebas de comparación de estado completo Ren'Py (T-623)."""
from pathlib import Path

from tools.ctl.full_diff import compare_files
from tools.ctl.scenario import Scenario, ScenarioError
from tools.ctl.trace import (
    compare_renpy_full,
    normalize_engine_full,
    normalize_renpy_full,
    parse_trace,
)


SNOOT_MAP = {
    "text": {100: "line_1"},
    "speakers": {1: "Anon"},
    "images": {10: ["bg classroom"], 11: ["anon happy"]},
    "tracks": {3: "audio/music.ogg"},
    "tags": {1: "anon"},
}
SPANISH = {"line_1": "Hola."}


def _traces(bg="classroom", expression="happy", music="audio/music.ogg"):
    engine = parse_trace(
        "T|1|1|SCENE|img=10\n"
        "T|2|1|SHOW|tag=1;img=11\n"
        "T|3|1|PLAY|track=3\n"
        "T|4|2|SAY|who=1;text=100\n"
    )
    reference = parse_trace(
        f"T|1|1|SCENE\n"
        f"T|2|1|SHOW|tag={bg};attrs=\n"
        f"T|3|1|SHOW|tag=anon;attrs={expression}\n"
        f"T|4|1|PLAY|music={music}\n"
        "T|5|2|SAY|who=Anon;id=line_1;loc=script.rpy:1\n"
    )
    return (
        normalize_engine_full(engine, SNOOT_MAP, SPANISH),
        normalize_renpy_full(reference, SPANISH, {"classroom", "hallway"}),
    )


def test_full_state_matches_background_sprites_and_music():
    actual, reference = _traces()
    assert actual[0].fields == {
        "who": "Anon",
        "text": "Hola.",
        "bg": "classroom",
        "sprites": ["anon happy"],
        "music": "mix:audio/music.ogg",
    }
    assert compare_renpy_full(actual, reference).verdict == "PASS"


def test_renpy_scene_image_and_overlay_keep_background_and_sprite_roles():
    reference = parse_trace(
        "T|1|1|SCENE\n"
        "T|2|1|SHOW|tag=room;attrs=anon day alt\n"
        "T|3|1|SHOW|tag=viewfinder;attrs=\n"
        "T|4|1|SHOW|tag=rec;attrs=\n"
        "T|5|2|SAY|who=Anon;id=line_1\n"
    )

    state = normalize_renpy_full(reference, SPANISH)[0]

    assert state.fields["bg"] == "room anon day alt"
    assert state.fields["sprites"] == ["rec", "viewfinder"]


def test_renpy_flip_attribute_is_represented_by_compiled_render_flag():
    reference = parse_trace(
        "T|1|1|SHOW|tag=anon;attrs=happy flip\n"
        "T|2|2|SAY|who=Anon;id=line_1\n"
    )

    state = normalize_renpy_full(reference, SPANISH)[0]

    assert state.fields["sprites"] == ["anon happy"]


def test_renpy_unattributed_characters_and_dimmer_layers_are_sprites():
    reference = parse_trace(
        "T|1|1|SCENE\n"
        "T|2|1|SHOW|tag=auditorium;attrs=\n"
        "T|3|1|SHOW|tag=jin;attrs=\n"
        "T|4|1|SHOW|tag=dimmer_darker;attrs=\n"
        "T|5|2|SAY|who=Anon;id=line_1\n"
    )

    state = normalize_renpy_full(reference, SPANISH, {"auditorium"})[0]

    assert state.fields["bg"] == "auditorium"
    assert state.fields["sprites"] == ["dimmer_darker", "jin"]


def test_layeredimage_defaults_are_omitted_from_compiled_sprite_names():
    image_map = {
        **SNOOT_MAP,
        "images": {**SNOOT_MAP["images"], 12: ["fangphonevideocall anonneutral basic bgday blackmid"]},
        "tags": {**SNOOT_MAP["tags"], 2: "fangphonevideocall"},
    }
    engine = parse_trace(
        "T|1|1|SHOW|tag=2;img=12\n"
        "T|2|2|SAY|who=1;text=100\n"
    )

    state = normalize_engine_full(engine, image_map, SPANISH)[0]

    assert state.fields["sprites"] == ["fangphonevideocall anonneutral"]


def test_music_layer_names_ignore_sync_and_mix_representation():
    engine = parse_trace(
        "T|1|1|PLAY|track=3\n"
        "T|2|2|SAY|who=1;text=100\n"
    )
    reference = parse_trace(
        "T|1|1|PLAY|music=<sync music1>audio\\music.ogg\n"
        "T|2|2|SAY|who=Anon;id=line_1\n"
    )

    actual = normalize_engine_full(engine, SNOOT_MAP, SPANISH)
    expected = normalize_renpy_full(reference, SPANISH)

    assert actual[0].fields["music"] == "mix:audio/music.ogg"
    assert actual[0].fields["music"] == expected[0].fields["music"]


def test_full_state_reports_first_divergent_visual_or_audio_field():
    for kwargs, field in (({"bg": "hallway"}, "bg"), ({"expression": "sad"}, "sprites"),
                          ({"music": "audio/other.ogg"}, "music")):
        actual, reference = _traces(**kwargs)
        result = compare_renpy_full(actual, reference)
        assert result.verdict == "FAIL"
        assert result.index == 0
        assert field in result.message


def test_declared_exception_matches_only_the_declared_pair():
    actual, reference = _traces(bg="hallway")
    exception = [{"index": 0, "field": "bg", "actual": "classroom", "reference": "hallway"}]
    assert compare_renpy_full(actual, reference, exception).verdict == "PASS"
    exception[0]["reference"] = "other"
    assert compare_renpy_full(actual, reference, exception).verdict == "FAIL"


def test_scenario_accepts_renpy_full_exceptions():
    data = {
        "id": "full",
        "reference": "reference.trace",
        "inputs": [],
        "expect": [],
        "compare": {
            "mode": "renpy_full",
            "events": ["SAY"],
            "exceptions": [{"index": 2, "field": "sprites", "actual": [], "reference": ["anon happy"]}],
        },
        "limits": {"max_seconds": 1},
    }
    assert Scenario.from_dict(data).compare.mode == "renpy_full"
    data["compare"]["exceptions"][0]["field"] = "who"
    try:
        Scenario.from_dict(data)
    except ScenarioError as error:
        assert "compare.exceptions[0].field" in str(error)
    else:
        raise AssertionError("invalid exception field was accepted")


def test_all_pc_routes_have_fixed_renpy_full_difference_counts():
    expected = {
        "chapter_x1": 0,
        "chapter_x2": 0,
        "chapter_x3": 0,
        "chapter_x4": 0,
        "chapter_x5": 0,
        "chapter_x6": 0,
        "chapter_x7": 3,
        "chapter_x8": 2,
        "chapter_x9": 163,
        "chapter_x10": 144,
        "ruta-1": 5826,
        "ruta-2": 5848,
        "ruta-3": 8198,
        "ruta-4": 7084,
    }
    for route, difference_count in expected.items():
        reference_name = route.replace("ruta-", "ruta ")
        actual, rows = compare_files(
            Path(f"tests/reference/traces/pc-routes/snoot-route-{route}.trace"),
            Path(f"tests/reference/traces/snoot/{reference_name}.trace"),
        )
        assert actual == difference_count, route
        assert sum(row["count"] for row in rows) == difference_count, route
