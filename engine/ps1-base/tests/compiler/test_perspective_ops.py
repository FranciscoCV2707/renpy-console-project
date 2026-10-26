import struct

from vncompiler.programa import compile_program
from vncompiler.simulador import simulate


def compile_body(body):
    script = {"script": {"test.rpy": [{"op": "label", "name": "start", "body": body}]}}
    program = compile_program(script, ["start"])
    return program.chapters[0][0], program.chapters[0][2]


def test_perspective_and_depth_encode_their_fields():
    vnb, chapter = compile_body([
        {"op": "ps1_perspective", "z11": 1000, "zc": -500, "on": 1},
        {"op": "ps1_depth", "tag": 2, "z": -300},
        {"op": "return"},
    ])
    code = vnb[32:]
    assert code[0] == 0x1B and code[1:6] == struct.pack("<HhB", 1000, -500, 1)
    assert code[6] == 0x1C and code[7:11] == struct.pack("<BhB", 2, -300, 0)
    assert chapter.reporte["PERSPECTIVE"] == 1 and chapter.reporte["DEPTH"] == 1


def test_perspective_defaults_to_z11_1000_and_rejects_bad_values():
    vnb, _ = compile_body([{"op": "ps1_perspective", "on": 0}, {"op": "return"}])
    assert vnb[32:][1:6] == struct.pack("<HhB", 1000, 0, 0)
    for bad in ({"op": "ps1_depth", "tag": 300, "z": 0}, {"op": "ps1_perspective", "z11": 0, "on": 1}):
        try:
            compile_body([bad, {"op": "return"}])
        except ValueError:
            continue
        raise AssertionError(f"debio rechazar {bad}")


def test_order_encodes_tag_reference_and_side():
    vnb, chapter = compile_body([{"op": "ps1_order", "tag": 3, "ref": 1, "above": 0}, {"op": "return"}])
    assert vnb[32:][:4] == bytes([0x18, 3, 1, 0]) and chapter.reporte["ORDER"] == 1
    try:
        compile_body([{"op": "ps1_order", "tag": 3, "ref": 1, "above": 2}, {"op": "return"}])
    except ValueError:
        return
    raise AssertionError("debio rechazar above 2")


def test_simulator_accepts_the_new_opcodes():
    vnb, _ = compile_body([
        {"op": "ps1_perspective", "z11": 1000, "zc": 0, "on": 1},
        {"op": "ps1_depth", "tag": 1, "z": 200},
        {"op": "say", "text": "hola", "tl": {"es": [{"text": "hola"}]}},
    ])
    events = simulate({0: vnb}, choices=[])
    assert any(event.startswith("SAY") for event in events)
